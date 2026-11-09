"""LLM 供应商配置。"""

from pydantic import BaseModel


class ProviderConfig(BaseModel):
    """统一的供应商配置，抹平 OpenAI / Anthropic 协议差异。"""

    name: str
    protocol: str  # openai | anthropic
    base_url: str
    api_key: str
    model: str

    def masked_key(self) -> str:
        """脱敏展示，避免把 key 写进日志。"""
        if len(self.api_key) <= 8:
            return "***"
        return f"{self.api_key[:4]}...{self.api_key[-4:]}"
