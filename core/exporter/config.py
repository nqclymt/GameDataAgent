"""导出配置：未设置 luban 工程时退化为独立输出目录。"""

from pathlib import Path

from pydantic import BaseModel, Field

from core.paths import app_dir, default_output_dir


class ExportConfig(BaseModel):
    """导出配置。

    - 未设置 ``project_dir``：只把表写到 ``output_dir``（方案 A）。
    - 设置 ``project_dir``：写入工程的 ``Datas`` 并调用 luban 导出（方案 C）。
    """

    luban_dll: Path = Field(
        default_factory=lambda: app_dir() / "tools" / "luban" / "Luban" / "Luban.dll"
    )
    project_dir: Path | None = None
    output_dir: Path = Field(default_factory=default_output_dir)
    code_out: Path | None = None
    data_out: Path | None = None
    backup_dir: Path = Field(default_factory=lambda: app_dir() / "output" / "backup")

    def datas_dir(self) -> Path:
        """表数据目录：有工程写工程，否则写独立输出目录。"""
        if self.project_dir:
            return self.project_dir / "Datas"
        return self.output_dir

    def code_dir(self) -> Path | None:
        if not self.project_dir:
            return None
        return self.code_out or (self.project_dir / "out" / "code")

    def data_dir(self) -> Path | None:
        if not self.project_dir:
            return None
        return self.data_out or (self.project_dir / "out" / "data")
