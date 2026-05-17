import json
from datetime import date

from agent.llm import LLMClient
from agent.memory import load as load_memory, render_for_prompt, save as save_memory
from agent.prompts import MEMORY_EXTRACTION_PROMPT, SYSTEM_PROMPT
from agent.tool_registry import TOOL_SCHEMAS, build_dispatch, execute

MAX_TOOL_HOPS = 8  # safety bound per user turn


def _log(role: str, content: str) -> None:
    print(f"\n--- {role} ---\n{content}", flush=True)


def _parse_json_loose(text: str) -> dict | None:
    """Parse JSON, tolerating code fences or leading/trailing prose."""
    if not text:
        return None
    s = text.strip()
    if s.startswith("```"):
        s = s.strip("`")
        if s.lower().startswith("json"):
            s = s[4:]
        s = s.strip()
    start, end = s.find("{"), s.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        return json.loads(s[start:end + 1])
    except json.JSONDecodeError:
        return None


def run_session(user_turns: list[str], today: str | None = None) -> None:
    today = today or date.today().isoformat()
    memory = load_memory()
    dispatch = build_dispatch(memory)
    llm = LLMClient()

    _log("session_start", f"backend={llm.backend} model={llm.model} today={today}")
    _log("memory_loaded", json.dumps(memory, indent=2))

    system_content = SYSTEM_PROMPT.format(today=today, memory_block=render_for_prompt(memory))
    messages: list[dict] = [{"role": "system", "content": system_content}]

    for user_msg in user_turns:
        _log("user", user_msg)
        messages.append({"role": "user", "content": user_msg})

        for _ in range(MAX_TOOL_HOPS):
            resp = llm.chat(messages, tools=TOOL_SCHEMAS)

            if resp.tool_calls:
                messages.append({
                    "role": "assistant",
                    "content": resp.content or "",
                    "tool_calls": [
                        {"id": tc["id"], "type": "function",
                         "function": {"name": tc["name"], "arguments": tc["arguments"]}}
                        for tc in resp.tool_calls
                    ],
                })
                for tc in resp.tool_calls:
                    result = execute(dispatch, tc["name"], tc["arguments"])
                    _log(f"tool:{tc['name']}", f"args={tc['arguments']}\nresult={result}")
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": result,
                    })
                continue

            _log("assistant", resp.content or "")
            messages.append({"role": "assistant", "content": resp.content or ""})
            break
        else:
            _log("warn", f"hit MAX_TOOL_HOPS={MAX_TOOL_HOPS} without final reply")

    _end_of_session_sweep(llm, messages, memory, today)
    save_memory(memory)
    _log("memory_saved", json.dumps(memory, indent=2))


def _end_of_session_sweep(llm: LLMClient, messages: list[dict], memory: dict, today: str) -> None:
    transcript_lines = []
    for m in messages:
        if m["role"] == "user":
            transcript_lines.append(f"USER: {m['content']}")
        elif m["role"] == "assistant" and m.get("content"):
            transcript_lines.append(f"ASSISTANT: {m['content']}")
    transcript = "\n".join(transcript_lines)

    sweep_messages = [
        {"role": "system", "content": "You extract memory updates. Output strict JSON only."},
        {"role": "user", "content": MEMORY_EXTRACTION_PROMPT.format(transcript=transcript)},
    ]
    resp = llm.chat(sweep_messages)
    _log("memory_sweep_raw", resp.content or "")

    extracted = _parse_json_loose(resp.content or "")
    if not extracted:
        _log("memory_sweep_warn", "could not parse JSON; skipping merge")
        return

    for fact in extracted.get("facts", []) or []:
        if isinstance(fact, str) and not any(f["text"] == fact for f in memory["facts"]):
            memory["facts"].append({"text": fact, "saved_on": today})
    for commitment in extracted.get("commitments", []) or []:
        if isinstance(commitment, str) and not any(c["text"] == commitment for c in memory["commitments"]):
            memory["commitments"].append({"text": commitment, "saved_on": today})
    if extracted.get("summary"):
        memory["last_session"] = {"date": today, "summary": extracted["summary"]}
