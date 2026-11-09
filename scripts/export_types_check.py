"""验证五种游戏类型都能导出成 luban 表。"""

import tempfile
from pathlib import Path

from core.exporter.config import ExportConfig
from core.exporter.service import export_framework
from core.modeling.builder import build_framework


def main() -> None:
    cases = [
        ("rpg", 60),
        ("mmorpg", 80),
        ("card", 60),
        ("idle", 200),
        ("slg", 30),
        ("tower", 50),
        ("shooter", 50),
        ("moba", 18),
        ("sim", 30),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        for game_type, level_cap in cases:
            framework = build_framework(
                "导出测试", level_cap=level_cap, game_type=game_type
            )
            config = ExportConfig(output_dir=Path(tmp) / game_type)
            result = export_framework(framework, config)
            print(
                f"{game_type}: {len(result.files)} 个表 / "
                f"{len(framework.attributes)} 属性 / {level_cap} 级"
            )


if __name__ == "__main__":
    main()
