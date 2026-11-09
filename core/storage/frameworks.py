"""框架存档：把 ValueFramework 存成 JSON 文件，支持保存 / 加载 / 列表 / 删除。"""

import json
from datetime import datetime
from pathlib import Path

from core.modeling.framework import ValueFramework

# 项目根目录下的 saved/
DEFAULT_DIR = Path(__file__).resolve().parents[2] / "saved"


def safe_name(title: str) -> str:
    """把标题转成安全文件名（保留中英文与数字）。"""
    cleaned = "".join(
        char for char in title if char.isalnum() or char in "_-"
    )
    return cleaned or "frame"


def save_framework(
    framework: ValueFramework, directory: Path = DEFAULT_DIR
) -> Path:
    """保存框架为 JSON，返回文件路径（标题 + 时间戳命名）。"""
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = directory / f"{safe_name(framework.title)}_{stamp}.json"
    path.write_text(
        framework.model_dump_json(indent=2), encoding="utf-8"
    )
    return path


def load_framework(path: Path) -> ValueFramework:
    """从 JSON 文件加载框架。"""
    return ValueFramework.model_validate_json(path.read_text(encoding="utf-8"))


def list_saved(directory: Path = DEFAULT_DIR) -> list[Path]:
    """按修改时间倒序列出存档。"""
    if not directory.exists():
        return []
    return sorted(
        directory.glob("*.json"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )


def delete_saved(path: Path) -> None:
    """删除存档（不存在时静默返回）。"""
    path.unlink(missing_ok=True)
