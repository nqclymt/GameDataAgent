"""从 CC Switch 本地数据库导入供应商配置。"""

import json
import os
import sqlite3
import tomllib
from pathlib import Path

from llm.config import ProviderConfig


def default_db_path() -> Path:
    return Path(os.path.expanduser("~")) / ".cc-switch" / "cc-switch.db"


def read_ccswitch_providers(db_path: Path | None = None) -> list[ProviderConfig]:
    """读取 CC Switch 中所有可解析的供应商，解析失败的条目会被跳过。"""
    db = Path(db_path) if db_path else default_db_path()
    if not db.exists():
        return []

    con = sqlite3.connect(db)
    try:
        rows = con.execute(
            "SELECT app_type, name, settings_config FROM providers "
            "ORDER BY is_current DESC, sort_index"
        ).fetchall()
    finally:
        con.close()

    providers: list[ProviderConfig] = []
    for app_type, name, raw in rows:
        if not raw:
            continue
        try:
            cfg = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if app_type == "claude":
            provider = _parse_claude(cfg, name)
        elif app_type == "codex":
            provider = _parse_codex(cfg, name)
        else:
            provider = None
        if provider:
            providers.append(provider)
    return providers


def _parse_claude(cfg: dict, name: str) -> ProviderConfig | None:
    env = cfg.get("env") or {}
    base_url = cfg.get("base_url") or env.get("ANTHROPIC_BASE_URL", "")
    api_key = cfg.get("api_key") or env.get("ANTHROPIC_AUTH_TOKEN", "")
    model = (
        cfg.get("model")
        or env.get("ANTHROPIC_MODEL")
        or env.get("ANTHROPIC_DEFAULT_SONNET_MODEL")
        or _first_model(cfg)
    )
    if not (base_url and api_key and model):
        return None
    return ProviderConfig(
        name=name, protocol="anthropic", base_url=base_url, api_key=api_key, model=model
    )


def _parse_codex(cfg: dict, name: str) -> ProviderConfig | None:
    auth = cfg.get("auth") or {}
    api_key = auth.get("OPENAI_API_KEY", "")
    base_url, model = _parse_codex_toml(cfg.get("config") or "")
    if not (base_url and api_key and model):
        return None
    return ProviderConfig(
        name=name, protocol="openai", base_url=base_url, api_key=api_key, model=model
    )


def _parse_codex_toml(text: str) -> tuple[str, str]:
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return "", ""
    provider = (data.get("model_providers") or {}).get(data.get("model_provider", "")) or {}
    return provider.get("base_url", ""), data.get("model", "")


def _first_model(cfg: dict) -> str:
    for item in cfg.get("models") or []:
        model_id = item.get("id") or item.get("model")
        if model_id:
            return model_id
    for item in (cfg.get("modelCatalog") or {}).get("models") or []:
        model_id = item.get("model")
        if model_id:
            return model_id
    return ""
