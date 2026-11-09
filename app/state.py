"""跨页面共享的应用状态。"""

from dataclasses import dataclass, field

from app.config_store import AppConfig, load_config
from core.modeling.framework import ValueFramework
from core.storage.variants import (
    delete_variant as _delete_variant_file,
    load_variants,
    save_variant as _save_variant_file,
)
from llm.client import LLMClient
from llm.config import ProviderConfig


@dataclass
class AppState:
    framework: ValueFramework | None = None
    variants: dict[str, ValueFramework] = field(default_factory=load_variants)
    config: AppConfig = field(default_factory=load_config)

    def save_variant(self, name: str, framework: ValueFramework) -> None:
        """保存一个方案（同名覆盖，同时落盘，重启不丢）。"""
        self.variants[name] = framework
        _save_variant_file(name, framework)

    def remove_variant(self, name: str) -> None:
        """删除方案（内存与磁盘同时清理）。"""
        self.variants.pop(name, None)
        _delete_variant_file(name)

    @property
    def provider(self) -> ProviderConfig | None:
        return self.config.provider

    def llm(self) -> LLMClient | None:
        """未配置供应商时返回 None，建模器自动走模板模式。"""
        return LLMClient(self.config.provider) if self.config.provider else None
