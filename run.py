"""打包入口：先显示启动画面，再拉起 flet 应用。

导入顺序是有意安排的：`app.main`（约 1.3s）放在启动画面之后，
这样窗口能在 0.5s 内出现，而不是等所有模块 import 完才显示。

设置环境变量 GDA_DEBUG_LOG=<路径> 可输出各阶段耗时，便于排查启动慢的问题。
"""

import os
import time

import flet as ft

from app.splash import SplashScreen

_T0 = time.perf_counter()
_MARKS: list[tuple[float, str]] = []


def mark(label: str) -> None:
    elapsed = time.perf_counter() - _T0
    _MARKS.append((elapsed, label))
    path = os.environ.get("GDA_DEBUG_LOG")
    if not path:
        return
    try:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(f"{elapsed:6.2f}s  {label}\n")
    except Exception:
        pass


def dump_marks() -> None:
    path = os.environ.get("GDA_DEBUG_LOG")
    if not path:
        return
    mark("进程结束")


def main() -> None:
    mark("模块导入完成")

    splash = SplashScreen()
    splash.start()
    mark("启动屏已拉起")

    try:
        import flet_desktop

        splash.set_status("正在准备运行库…")
        flet_desktop.ensure_client_cached()
        mark("运行库就绪")
    except Exception as exc:  # noqa: BLE001
        mark(f"运行库准备失败: {exc}")

    splash.set_status("正在加载界面…")
    from app.main import main as app_main
    mark("业务模块导入完成")

    ft.run(app_main)
    mark("ft.run 已返回")


if __name__ == "__main__":
    try:
        main()
    finally:
        dump_marks()
