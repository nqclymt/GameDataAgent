"""导出差异对比验证：首次导出无差异，改数值后能定位到具体格子。"""

import copy
import tempfile
from pathlib import Path

from core.exporter.config import ExportConfig
from core.exporter.service import export_framework, preview_export
from core.modeling.builder import build_framework


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out"
        config = ExportConfig(output_dir=out, backup_dir=Path(tmp) / "backup")

        framework = build_framework("差异测试", level_cap=10, game_type="rpg")
        first = export_framework(framework, config)
        print(f"首次导出：{len(first.files)} 个表，差异 {len(first.diffs)} 项（期望 0）")

        changed = copy.deepcopy(framework)
        for attr in changed.attributes:
            if attr.key == "hp":
                attr.growth = 1.05

        preview = preview_export(changed, config)
        print(f"预览（干跑，不写入）：{len(preview)} 张表有差异")

        second = export_framework(changed, config)
        print(f"二次导出（生命成长 1.12 → 1.05）：差异 {len(second.diffs)} 张表")
        for diff in second.diffs:
            print(
                f"  {diff.table}：新增 {diff.added} 行 / 删除 {diff.removed} 行 / "
                f"修改 {len(diff.changed)} 格"
            )
            for change in diff.changed[:5]:
                print(f"    {change.row} 行 {change.column}：{change.old} → {change.new}")


if __name__ == "__main__":
    main()
