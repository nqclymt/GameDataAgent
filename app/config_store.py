"""应用配置持久化（供应商与导出设置）。"""

from pathlib import Path

from pydantic import BaseModel, Field

from core.exporter.config import ExportConfig
from core.paths import app_dir
from llm.config import ProviderConfig


class AppConfig(BaseModel):
    provider: ProviderConfig | None = None
    export: ExportConfig = Field(default_factory=ExportConfig)


def config_file() -> Path:
    return app_dir() / "config" / "app_config.json"


def load_config() -> AppConfig:
    path = config_file()
    if not path.exists():
        return AppConfig()
    try:
        return AppConfig.model_validate_json(path.read_text(encoding="utf-8"))
    except Exception:
        return AppConfig()


def save_config(config: AppConfig) -> None:
    path = config_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(config.model_dump_json(indent=2), encoding="utf-8")
