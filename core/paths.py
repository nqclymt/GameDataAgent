"""运行目录定位（开发与打包环境通用）。"""

import sys
from pathlib import Path


def app_dir() -> Path:
    """开发时是项目根，PyInstaller 打包后是 exe 所在目录（可写数据放这里）。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def resource_dir() -> Path:
    """只读资源（assets）目录。

    打包后 PyInstaller 会把 --add-data 的内容解到 sys._MEIPASS
    （onefile 是临时目录，onedir 是 _internal），开发时是项目根。
    """
    bundled = getattr(sys, "_MEIPASS", None)
    if getattr(sys, "frozen", False) and bundled:
        return Path(bundled)
    return Path(__file__).resolve().parent.parent


def default_output_dir() -> Path:
    return app_dir() / "output" / "luban"
