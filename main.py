"""打包入口：确保项目根在 sys.path，可打包也能直接运行。"""

import flet as ft

from app.main import main

if __name__ == "__main__":
    ft.run(main)
