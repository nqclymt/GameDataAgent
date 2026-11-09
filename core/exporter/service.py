"""导出服务：生成表 → 备份 → 写入目标 → 调用 luban。"""

import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from core.exporter.config import ExportConfig
from core.exporter.diff import TableDiff, diff_table_files
from core.modeling.framework import ValueFramework
from core.schema.build_tables import generate_luban_tables


class ExportError(RuntimeError):
    """导出流程失败。"""


class ExportResult(BaseModel):
    files: list[Path]
    diffs: list[TableDiff] = Field(default_factory=list)
    code_dir: Path | None = None
    data_dir: Path | None = None
    luban_log: str = ""


def export_framework(framework: ValueFramework, config: ExportConfig) -> ExportResult:
    """按配置导出数值框架。

    未配置 luban 工程时只产出表格文件；配置后额外调用 luban 导出代码与数据。
    """
    target_dir = config.datas_dir()
    target_dir.mkdir(parents=True, exist_ok=True)

    files: list[Path] = []
    diffs: list[TableDiff] = []
    with tempfile.TemporaryDirectory() as tmp:
        generated = generate_luban_tables(framework, Path(tmp))
        for src in generated:
            dst = target_dir / src.name
            if dst.exists():
                table_diff = diff_table_files(dst, src)
                if table_diff.has_changes:
                    diffs.append(table_diff)
                _backup(dst, config.backup_dir)
            shutil.copy2(src, dst)
            files.append(dst)

    if not config.project_dir:
        return ExportResult(files=files, diffs=diffs)

    code_dir, data_dir, log = _run_luban(config)
    return ExportResult(
        files=files, diffs=diffs, code_dir=code_dir, data_dir=data_dir, luban_log=log
    )


def preview_export(framework: ValueFramework, config: ExportConfig) -> list[TableDiff]:
    """干跑：只对比目标目录现有表与新表，返回差异，不写入、不备份。"""
    target_dir = config.datas_dir()
    if not target_dir.exists():
        return []

    diffs: list[TableDiff] = []
    with tempfile.TemporaryDirectory() as tmp:
        generated = generate_luban_tables(framework, Path(tmp))
        for src in generated:
            dst = target_dir / src.name
            if not dst.exists():
                continue
            table_diff = diff_table_files(dst, src)
            if table_diff.has_changes:
                diffs.append(table_diff)
    return diffs


def _backup(path: Path, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    dst = backup_dir / f"{path.stem}_{stamp}{path.suffix}"
    shutil.copy2(path, dst)
    return dst


def _run_luban(config: ExportConfig) -> tuple[Path, Path, str]:
    if not config.luban_dll.exists():
        raise ExportError(f"找不到 Luban.dll: {config.luban_dll}")

    project_dir = config.project_dir
    if project_dir is None:
        raise ExportError("未配置 luban 工程目录")
    conf = project_dir / "luban.conf"
    if not conf.exists():
        raise ExportError(f"找不到 luban.conf: {conf}")

    code_dir, data_dir = config.code_dir(), config.data_dir()
    if code_dir is None or data_dir is None:
        raise ExportError("未配置代码/数据输出目录")
    code_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "dotnet",
        str(config.luban_dll),
        "-t",
        "client",
        "-c",
        "cs-bin",
        "-d",
        "bin",
        "--conf",
        str(conf),
        "-x",
        f"outputCodeDir={code_dir}",
        "-x",
        f"outputDataDir={data_dir}",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    log = (proc.stdout or "") + (proc.stderr or "")
    if "运行失败" in log or "ERROR" in log:
        raise ExportError(f"luban 导出失败:\n{log[-2000:]}")
    return code_dir, data_dir, log
