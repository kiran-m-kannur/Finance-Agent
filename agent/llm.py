import os
from dataclasses import dataclass, field

from openai import OpenAI


@dataclass
class LLMResponse:
    content: str | None
    tool_calls: list[dict] = field(default_factory=list)


class LLMClient:
    def __init__(self):
        self.client = OpenAI()
        self.model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        self.backend = "openai"

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> LLMResponse:
        kwargs = {"model": self.model, "messages": messages, "temperature": 0.2}
        if tools:
            kwargs["tools"] = tools
        resp = self.client.chat.completions.create(**kwargs)
        msg = resp.choices[0].message
        tool_calls = []
        for tc in msg.tool_calls or []:
            tool_calls.append(
                {"id": tc.id, "name": tc.function.name, "arguments": tc.function.arguments}
            )
        return LLMResponse(content=msg.content, tool_calls=tool_calls)
