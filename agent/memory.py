import json
from pathlib import Path

DATA_DIR = Path("data")
MEMORY_PATH = DATA_DIR / "memory.json"
PROFILE_PATH = DATA_DIR / "user_profile.json"


def load() -> dict:
    if MEMORY_PATH.exists():
        return json.loads(MEMORY_PATH.read_text())
    profile = json.loads(PROFILE_PATH.read_text()) if PROFILE_PATH.exists() else {}
    return {"profile": profile, "facts": [], "commitments": [], "last_session": None}


def save(memory: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    MEMORY_PATH.write_text(json.dumps(memory, indent=2))


def render_for_prompt(memory: dict) -> str:
    """Format memory as a compact block to inject into the system prompt."""
    parts: list[str] = []

    if memory.get("profile"):
        parts.append("### Profile")
        for k, v in memory["profile"].items():
            parts.append(f"- {k}: {v}")

    if memory.get("facts"):
        parts.append("\n### Facts learned about the user")
        for f in memory["facts"]:
            parts.append(f"- ({f['saved_on']}) {f['text']}")

    if memory.get("commitments"):
        parts.append("\n### Active commitments the user has made")
        for c in memory["commitments"]:
            parts.append(f"- ({c['saved_on']}) {c['text']}")

    if memory.get("last_session"):
        ls = memory["last_session"]
        parts.append(f"\n### Last session ({ls['date']})")
        parts.append(ls["summary"])

    return "\n".join(parts) if parts else "(no prior memory)"
