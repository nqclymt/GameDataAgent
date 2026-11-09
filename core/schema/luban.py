"""luban Excel 格式读写。"""

from dataclasses import dataclass
from pathlib import Path

import openpyxl

# __tables__.xlsx 的表头（第一行定义列名，第二行是说明）
TABLE_DEF_HEADERS = [
    "##var",
    "full_name",
    "value_type",
    "read_schema_from_file",
    "input",
    "index",
    "mode",
    "group",
    "comment",
    "tags",
    "output",
]
TABLE_DEF_COMMENTS = [
    "##",
    "全名(包含模块和名字)",
    "记录类名",
    "从excel读取定义",
    "文件列表",
    "表id字段",
    "模式",
    "分组",
    "注释",
    "",
    "输出文件名",
]


@dataclass
class Column:
    """数据表的一列。"""

    name: str
    type: str
    group: str = "c,s"
    comment: str = ""


@dataclass
class TableDef:
    """一张数据表在 __tables__.xlsx 中的定义。"""

    full_name: str
    value_type: str
    input: str
    index: str = ""
    mode: str = ""
    group: str = ""


def write_data_sheet(path: Path, columns: list[Column], rows: list[list]) -> None:
    """写一张 luban 数据表：前 4 行元信息 + 数据行。"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws.append(["##var"] + [c.name for c in columns])
    ws.append(["##type"] + [c.type for c in columns])
    ws.append(["##group"] + [c.group for c in columns])
    ws.append(["##"] + [c.comment for c in columns])
    for row in rows:
        ws.append([None] + list(row))
    wb.save(path)
    wb.close()


def read_data_sheet(path: Path) -> tuple[list[str], list[list]]:
    """读取 luban 数据表：返回列名与数据行（跳过前 4 行元信息）。"""
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active
    raw = list(ws.iter_rows(values_only=True))
    wb.close()
    if len(raw) < 5:
        return [], []
    columns = [str(cell) for cell in raw[0][1:] if cell is not None]
    rows: list[list] = []
    for row in raw[4:]:
        if row[0] is None and all(cell is None for cell in row[1:]):
            continue
        rows.append(list(row[1:]))
    return columns, rows


def write_tables_def(path: Path, tables: list[TableDef]) -> None:
    """写 __tables__.xlsx 的表定义。"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws.append(TABLE_DEF_HEADERS)
    ws.append(TABLE_DEF_COMMENTS)
    for table in tables:
        ws.append(
            [
                None,
                table.full_name,
                table.value_type,
                1,
                table.input,
                table.index or None,
                table.mode or None,
                table.group or None,
                None,
                None,
                None,
            ]
        )
    wb.save(path)
    wb.close()
