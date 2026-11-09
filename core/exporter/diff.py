"""表数据差异对比：导出前旧表 vs 即将写入的新表。"""

from pathlib import Path

from pydantic import BaseModel, Field

from core.schema.luban import read_data_sheet


class CellChange(BaseModel):
    row: str
    column: str
    old: str
    new: str


class TableDiff(BaseModel):
    table: str
    added: int = 0
    removed: int = 0
    changed: list[CellChange] = Field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)


def diff_table_files(old_path: Path, new_path: Path) -> TableDiff:
    """对比两个数据表文件：按首列匹配行，逐列比较。"""
    old_columns, old_rows = read_data_sheet(old_path)
    new_columns, new_rows = read_data_sheet(new_path)
    return _diff(old_path.stem, old_rows, new_rows, new_columns or old_columns)


def _diff(
    table: str, old_rows: list[list], new_rows: list[list], columns: list[str]
) -> TableDiff:
    old_map = {_key(row): row for row in old_rows}
    new_map = {_key(row): row for row in new_rows}

    diff = TableDiff(table=table)
    diff.added = len(new_map.keys() - old_map.keys())
    diff.removed = len(old_map.keys() - new_map.keys())

    for key in old_map.keys() & new_map.keys():
        old_row, new_row = old_map[key], new_map[key]
        for i, column in enumerate(columns):
            old_value = old_row[i] if i < len(old_row) else None
            new_value = new_row[i] if i < len(new_row) else None
            if old_value != new_value:
                diff.changed.append(
                    CellChange(
                        row=key,
                        column=column,
                        old=_fmt(old_value),
                        new=_fmt(new_value),
                    )
                )
    return diff


def _key(row: list) -> str:
    return str(row[0]) if row else "?"


def _fmt(value) -> str:
    if value is None:
        return "空"
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)
