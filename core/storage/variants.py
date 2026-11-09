"""方案存档：多方案对比用的框架集合，按方案名一个文件。"""

from pathlib import Path

from core.modeling.framework import ValueFramework
from core.storage.frameworks import DEFAULT_DIR, safe_name

VARIANTS_DIR = DEFAULT_DIR / "variants"


def save_variant(
    name: str, framework: ValueFramework, directory: Path = VARIANTS_DIR
) -> Path:
    """保存方案（同名覆盖），返回文件路径。"""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{safe_name(name)}.json"
    path.write_text(framework.model_dump_json(indent=2), encoding="utf-8")
    return path


def load_variants(directory: Path = VARIANTS_DIR) -> dict[str, ValueFramework]:
    """加载全部方案；单个文件损坏时跳过，不影响其余。"""
    if not directory.exists():
        return {}
    result: dict[str, ValueFramework] = {}
    for path in sorted(directory.glob("*.json")):
        try:
            framework = ValueFramework.model_validate_json(
                path.read_text(encoding="utf-8")
            )
        except Exception:
            continue
        result[path.stem] = framework
    return result


def delete_variant(name: str, directory: Path = VARIANTS_DIR) -> None:
    """删除方案（不存在时静默返回）。"""
    (directory / f"{safe_name(name)}.json").unlink(missing_ok=True)
