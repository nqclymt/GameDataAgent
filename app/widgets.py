"""通用 UI 组件（统一卡片、输入框、分段选择、下拉、按钮）。"""

import flet as ft

from app.theme import ACCENT, ACCENT_SOFT, BORDER, FG, MENU, MUTED, PANEL


def card(*controls: ft.Control, spacing: int = 10, scroll=None) -> ft.Container:
    """统一的卡片容器。"""
    return ft.Container(
        padding=16,
        bgcolor=PANEL,
        border_radius=8,
        border=ft.Border.all(1, BORDER),
        content=ft.Column(list(controls), spacing=spacing, scroll=scroll),
    )


def primary_button(text: str, on_click, icon=None) -> ft.Button:
    """强调色主按钮。"""
    return ft.Button(text, icon=icon, bgcolor=ACCENT, color="#FFFFFF", on_click=on_click)


def section_title(text: str) -> ft.Text:
    return ft.Text(text, size=12, weight=ft.FontWeight.W_600, color=ACCENT)


def text_input(
    label: str,
    value: str = "",
    width: int | None = None,
    password: bool = False,
) -> ft.TextField:
    """统一风格的文本输入框（outlined + 暖色边框）。"""
    return ft.TextField(
        label=label,
        value=value,
        width=width,
        password=password,
        border=ft.OutlineInputBorder(),
        border_color=BORDER,
        focused_border_color=ACCENT,
        fill_color=PANEL,
    )


def segmented(
    label: str,
    options: list[dict],
    value: str,
    on_change,
) -> ft.Control:
    """行内胶囊切换（2~3 个选项）：选中态深蓝底白字，状态完全自绘。

    options 形如 [{"key": "rpg", "text": "RPG", "icon": ft.Icons.XXX}, ...]
    """
    state = {"value": value}
    group = ft.Row(spacing=6)

    def _render() -> None:
        tiles = []
        for item in options:
            selected = item["key"] == state["value"]
            content = [ft.Text(item["text"], size=12, color="#FFFFFF" if selected else FG)]
            if item.get("icon") is not None:
                content.insert(
                    0,
                    ft.Icon(
                        item["icon"],
                        size=14,
                        color="#FFFFFF" if selected else MUTED,
                    ),
                )
            tiles.append(
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                    bgcolor=ACCENT if selected else PANEL,
                    border=ft.Border.all(1, ACCENT if selected else BORDER),
                    border_radius=6,
                    on_click=lambda e, k=item["key"]: _choose(k),
                    content=ft.Row(
                        content,
                        spacing=4,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                )
            )
        group.controls = tiles

    def _choose(key: str) -> None:
        state["value"] = key
        _render()
        on_change(key)
        group.update()

    _render()
    return ft.Column(
        [ft.Text(label, size=11, color=MUTED), group],
        spacing=4,
    )


def picker(
    page: ft.Page,
    label: str,
    options: list[dict],
    value: str,
    on_change,
    title: str | None = None,
) -> ft.Control:
    """点击弹窗选择：触发区固定一行，选项再多也不撑高页面。

    options 形如 [{"key": "rpg", "text": "RPG", "icon": ft.Icons.XXX}, ...]
    """
    state = {"value": value}

    def _current() -> dict:
        for item in options:
            if item["key"] == state["value"]:
                return item
        return options[0]

    text_ctl = ft.Text(_current()["text"], size=13, color=FG)
    icon_ctl = ft.Icon(_current().get("icon") or ft.Icons.CIRCLE, size=16, color=MUTED)

    def _tile(item: dict) -> ft.Container:
        selected = item["key"] == state["value"]
        return ft.Container(
            expand=True,
            height=48,
            padding=ft.Padding.symmetric(horizontal=10, vertical=6),
            bgcolor=ACCENT_SOFT if selected else PANEL,
            border=ft.Border.all(2 if selected else 1, ACCENT if selected else BORDER),
            border_radius=8,
            on_click=lambda e, k=item["key"]: _choose(k),
            content=ft.Row(
                [
                    ft.Icon(
                        item.get("icon") or ft.Icons.CIRCLE,
                        size=16,
                        color=ACCENT if selected else MUTED,
                    ),
                    ft.Text(
                        item["text"],
                        size=12,
                        color=ACCENT if selected else FG,
                        weight=ft.FontWeight.W_600
                        if selected
                        else ft.FontWeight.W_400,
                    ),
                ],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def _choose(key: str) -> None:
        state["value"] = key
        chosen = _current()
        text_ctl.value = chosen["text"]
        icon_ctl.name = chosen.get("icon") or ft.Icons.CIRCLE
        page.pop_dialog()
        on_change(key)
        page.update()

    def _open(_e) -> None:
        rows = [
            ft.Row([_tile(item) for item in options[i : i + 2]], spacing=8)
            for i in range(0, len(options), 2)
        ]
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                title or label, size=15, weight=ft.FontWeight.W_600, color=FG
            ),
            content=ft.Container(
                width=380,
                content=ft.Column(rows, spacing=8, scroll=ft.ScrollMode.AUTO),
            ),
            bgcolor=PANEL,
            shape=ft.RoundedRectangleBorder(radius=12),
            actions=[ft.TextButton("取消", on_click=lambda ev: page.pop_dialog())],
        )
        page.show_dialog(dialog)

    trigger = ft.Container(
        padding=ft.Padding.symmetric(horizontal=12, vertical=11),
        border=ft.Border.all(1, BORDER),
        border_radius=6,
        bgcolor=PANEL,
        on_click=_open,
        content=ft.Row(
            [
                icon_ctl,
                text_ctl,
                ft.Container(expand=True),
                ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN, size=18, color=MUTED),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    return ft.Column(
        [ft.Text(label, size=11, color=MUTED), trigger],
        spacing=4,
    )


def select(
    label: str,
    options: list[ft.DropdownOption],
    value: str | None = None,
    width: int | None = None,
) -> ft.Dropdown:
    """统一风格的下拉框（选项较多时使用）。"""
    return ft.Dropdown(
        label=label,
        value=value,
        width=width,
        options=options,
        border=ft.OutlineInputBorder(),
        border_color=BORDER,
        focused_border_color=ACCENT,
        fill_color=PANEL,
        menu_style=ft.MenuStyle(
            bgcolor=MENU,
            shape=ft.RoundedRectangleBorder(radius=10),
            elevation=6,
        ),
    )
