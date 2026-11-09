"""M3 验证：框架生成 luban 表并回读校验。"""

from pathlib import Path

import openpyxl

from core.modeling.builder import build_framework
from core.schema.build_tables import generate_luban_tables

OUT_DIR = Path("output/luban")


def main() -> None:
    framework = build_framework("苍梧纪", level_cap=60)
    paths = generate_luban_tables(framework, OUT_DIR)
    print(f"已生成 {len(paths)} 个文件到 {OUT_DIR}")

    for path in paths:
        wb = openpyxl.load_workbook(path, data_only=True)
        ws = wb.active
        print(f"  {path.name}: {ws.max_row} 行 x {ws.max_column} 列")
        wb.close()

    wb = openpyxl.load_workbook(OUT_DIR / "__tables__.xlsx", data_only=True)
    rows = list(wb.active.iter_rows(values_only=True))
    wb.close()

    assert rows[0][0] == "##var", "表定义缺少 ##var 表头"
    print("\n表定义:")
    for row in rows[2:]:
        if row[1]:
            print(f"  {row[1]} -> {row[4]}")

    level_wb = openpyxl.load_workbook(OUT_DIR / "cfg_Role_Level.xlsx", data_only=True)
    level_rows = list(level_wb.active.iter_rows(values_only=True))
    level_wb.close()
    assert level_rows[0][0] == "##var" and level_rows[1][0] == "##type"
    assert len(level_rows) == 4 + framework.level_cap, "等级数据行数不符"
    print(f"\n等级表校验通过：{len(level_rows) - 4} 行数据")


if __name__ == "__main__":
    main()
