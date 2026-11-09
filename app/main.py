"""Game Data Agent 客户端入口。"""

import flet as ft

from app.pages.analysis import build_analysis
from app.pages.export import build_export
from app.pages.settings import build_settings
from app.pages.workbench import build_workbench
from app.state import AppState
from app.theme import ACCENT, BG, BORDER, FG, MUTED, PANEL
from core.paths import resource_dir


def main(page: ft.Page) -> None:
    page.title = "Game Data Agent"
    page.padding = 0
    page.bgcolor = BG
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(
        font_family="Microsoft YaHei UI",
        color_scheme=ft.ColorScheme(
            primary=ACCENT,
            surface=PANEL,
            on_surface=FG,
            outline=BORDER,
        ),
    )
    page.window.width = 1220
    page.window.height = 800
    page.window.min_width = 980
    page.window.min_height = 660

    icon_path = resource_dir() / "assets" / "icon.png"
    # Windows 的窗口图标只认 .ico，侧栏 logo 仍用 png
    icon_ico = resource_dir() / "assets" / "icon.ico"
    window_icon = icon_ico if icon_ico.exists() else icon_path
    if window_icon.exists():
        try:
            page.window.icon = str(window_icon)
        except Exception:
            pass

    state = AppState()
    content = ft.Container(expand=True, padding=24)
    builders = {0: build_workbench, 1: build_analysis, 2: build_settings, 3: build_export}

    def show(index: int) -> None:
        content.content = builders[index](page, state)
        page.update()

    def on_nav_change(e) -> None:
        show(e.control.selected_index)

    brand_controls: list[ft.Control] = []
    if icon_path.exists():
        brand_controls.append(ft.Image(src=str(icon_path), width=40, height=40))
    brand_controls.append(
        ft.Text("数值 Agent", size=9, color=ACCENT, text_align=ft.TextAlign.CENTER)
    )
    brand = ft.Container(
        padding=ft.Padding.symmetric(horizontal=10, vertical=18),
        content=ft.Column(
            brand_controls,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=6,
        ),
    )

    nav = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=96,
        bgcolor=PANEL,
        leading=brand,
        on_change=on_nav_change,
        destinations=[
            ft.NavigationRailDestination(icon=ft.Icons.DASHBOARD, label="工作台"),
            ft.NavigationRailDestination(icon=ft.Icons.TABLE_CHART, label="分析"),
            ft.NavigationRailDestination(icon=ft.Icons.TUNE, label="配置"),
            ft.NavigationRailDestination(icon=ft.Icons.DOWNLOAD, label="导出"),
        ],
    )

    header = ft.Container(
        padding=ft.Padding.symmetric(horizontal=24, vertical=12),
        bgcolor=PANEL,
        border=ft.Border(bottom=ft.BorderSide(1, BORDER)),
        content=ft.Row(
            [
                ft.Text("Game Data Agent", size=15, weight=ft.FontWeight.W_600, color=ACCENT),
                ft.Text("数值建模 · 配表生成 · 平衡验证", size=11, color=MUTED),
                ft.Container(expand=True),
                ft.Text("v0.1", size=11, color=MUTED),
            ],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    footer = ft.Container(
        padding=ft.Padding.symmetric(horizontal=24, vertical=8),
        bgcolor=PANEL,
        border=ft.Border(top=ft.BorderSide(1, BORDER)),
        content=ft.Row(
            [
                ft.Text("就绪", size=11, color=MUTED),
                ft.Container(expand=True),
                ft.Text("模板 / ccswitch / 自定义 LLM 均已接入", size=11, color=MUTED),
            ],
        ),
    )

    body = ft.Row(
        controls=[nav, ft.VerticalDivider(width=1, color=BORDER), content],
        expand=True,
    )

    page.add(ft.Column([header, body, footer], spacing=0, expand=True))
    show(0)


if __name__ == "__main__":
    ft.run(main)
