"""统一 LLM 客户端，屏蔽 OpenAI / Anthropic 协议差异。"""

import json

from llm.config import ProviderConfig


class LLMError(RuntimeError):
    """LLM 调用或输出解析失败。"""


class LLMClient:
    def __init__(self, config: ProviderConfig) -> None:
        self.config = config

    def complete(self, system: str, user: str) -> str:
        if self.config.protocol == "anthropic":
            return self._complete_anthropic(system, user)
        return self._complete_openai(system, user)

    def complete_json(self, system: str, user: str) -> dict:
        return _extract_json(self.complete(system, user))

    def _complete_openai(self, system: str, user: str) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=self.config.api_key, base_url=self.config.base_url)
        resp = client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.7,
        )
        return resp.choices[0].message.content or ""

    def _complete_anthropic(self, system: str, user: str) -> str:
        from anthropic import Anthropic

        client = Anthropic(api_key=self.config.api_key, base_url=self.config.base_url)
        resp = client.messages.create(
            model=self.config.model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(
            block.text for block in resp.content if getattr(block, "type", "") == "text"
        )


def _extract_json(text: str) -> dict:
    """从模型输出中剥离可能的 markdown 包裹，取出 JSON 对象。"""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < 0:
        raise LLMError("模型未返回 JSON 对象")
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise LLMError(f"JSON 解析失败: {exc}") from exc
