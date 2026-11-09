"""工作台：左侧参数、右侧可编辑框架。"""

import flet as ft

from app.pages.framework_editor import build_editor
from app.state import AppState
from app.theme import BORDER, DANGER, FG, MUTED
from app.widgets import card, picker, primary_button, section_title, text_input
from core.modeling.builder import build_framework
from core.storage.frameworks import (
    delete_saved,
    list_saved,
    load_framework,
    save_framework,
)


def build_workbench(page: ft.Page, state: AppState) -> ft.Control:
    type_holder = {"value": "rpg"}
    game_type = picker(
        page,
        "游戏类型",
        [
            {"key": "rpg", "text": "RPG", "icon": ft.Icons.SPORTS_ESPORTS},
            {"key": "mmorpg", "text": "MMORPG", "icon": ft.Icons.GROUPS},
            {"key": "card", "text": "卡牌", "icon": ft.Icons.STYLE},
            {"key": "idle", "text": "放置", "icon": ft.Icons.HOURGLASS_EMPTY},
            {"key": "slg", "text": "SLG", "icon": ft.Icons.CASTLE},
            {"key": "tower", "text": "塔防", "icon": ft.Icons.FORT},
            {"key": "shooter", "text": "射击", "icon": ft.Icons.GPS_FIXED},
            {"key": "moba", "text": "MOBA", "icon": ft.Icons.SHIELD},
            {"key": "sim", "text": "模拟经营", "icon": ft.Icons.STOREFRONT},
        ],
        "rpg",
        on_change=lambda key: type_holder.__setitem__("value", key),
    )
    title = text_input("游戏标题", "苍梧纪")
    level_cap = text_input("等级上限", "60")
    theme = text_input("题材", "东方玄幻")
    status = ft.Text("", size=12, color=MUTED)
    right_box = ft.Column(spacing=12)

    def apply_framework(updated) -> None:
        state.framework = updated
        status.value = "编辑已应用"

    def on_generate(_e) -> None:
        status.value = "生成中..."
        right_box.controls = [ft.ProgressRing(width=20, height=20)]
        page.update()

        def work() -> None:
            try:
                framework = build_framework(
                    title.value.strip() or "未命名",
                    int(level_cap.value.strip() or "60"),
                    theme.value.strip() or "通用",
                    game_type=type_holder["value"],
                    llm=state.llm(),
                )
                state.framework = framework
                right_box.controls = [
                    _summary(framework),
                    build_editor(page, framework, apply_framework),
                ]
                status.value = (
                    f"已生成：{len(framework.attributes)} 个属性 / {framework.level_cap} 级"
                )
            except Exception as exc:
                right_box.controls = [ft.Text(f"生成失败：{exc}", color=DANGER)]
                status.value = "生成失败"
            page.update()

        page.run_thread(work)

    def on_save_variant(_e) -> None:
        if state.framework is None:
            status.value = "请先生成数值框架"
            page.update()
            return
        name = title.value.strip() or "未命名"
        state.save_variant(name, state.framework)
        status.value = f"已保存方案「{name}」（共 {len(state.variants)} 个）"
        page.update()

    saved_box = ft.Column(spacing=4)

    def refresh_saved() -> None:
        saved_box.controls = []
        files = list_saved()
        if not files:
            saved_box.controls.append(ft.Text("暂无存档", size=11, color=MUTED))
            return
        for path in files[:8]:

            def make_loader(target):
                def load(_e) -> None:
                    try:
                        framework = load_framework(target)
                        state.framework = framework
                        right_box.controls = [
                            _summary(framework),
                            build_editor(page, framework, apply_framework),
                        ]
                        status.value = f"已加载 {target.name}"
                    except Exception as exc:
                        status.value = f"加载失败：{exc}"
                    page.update()

                return load

            def make_deleter(target):
                def delete(_e) -> None:
                    delete_saved(target)
                    status.value = f"已删除 {target.name}"
                    refresh_saved()
                    page.update()

                return delete

            saved_box.controls.append(
                ft.Row(
                    [
                        ft.TextButton(
                            path.name[:24],
                            icon=ft.Icons.FOLDER_OPEN,
                            on_click=make_loader(path),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_color=DANGER,
                            icon_size=16,
                            width=28,
                            height=28,
                            padding=0,
                            on_click=make_deleter(path),
                            tooltip="删除该存档",
                        ),
                    ],
                    spacing=4,
                )
            )

    def on_save_file(_e) -> None:
        if state.framework is None:
            status.value = "请先生成数值框架"
            page.update()
            return
        try:
            path = save_framework(state.framework)
            status.value = f"已保存 {path.name}"
            refresh_saved()
        except Exception as exc:
            status.value = f"保存失败：{exc}"
        page.update()

    def on_refresh_click(_e) -> None:
        refresh_saved()
        page.update()

    refresh_saved()

    left = ft.Container(
        width=380,
        content=card(
            section_title("生成参数"),
            game_type,
            title,
            level_cap,
            theme,
            ft.Row(
                [
                    primary_button(
                        "生成数值框架", on_generate, icon=ft.Icons.PLAY_ARROW
                    ),
                    ft.TextButton(
                        "保存为方案",
                        icon=ft.Icons.BOOKMARK_ADD,
                        on_click=on_save_variant,
                    ),
                ],
                spacing=8,
            ),
            status,
            ft.Divider(height=1, color=BORDER),
            section_title("存档（保存 / 加载）"),
            ft.Row(
                [
                    ft.TextButton(
                        "保存当前框架",
                        icon=ft.Icons.SAVE,
                        on_click=on_save_file,
                    ),
                    ft.TextButton(
                        "刷新", icon=ft.Icons.REFRESH, on_click=on_refresh_click
                    ),
                ],
                spacing=4,
            ),
            saved_box,
        ),
    )
    right = ft.Container(
        expand=True,
        content=card(
            section_title("框架编辑器"),
            right_box,
            scroll=ft.ScrollMode.AUTO,
        ),
    )

    return ft.Column(
        spacing=16,
        expand=True,
        controls=[
            ft.Text("工作台", size=20, weight=ft.FontWeight.W_600, color=FG),
            ft.Text("生成后可增删改属性与参数；未配置 LLM 时走内置模板", size=12, color=MUTED),
            ft.Row(spacing=16, expand=True, controls=[left, right]),
        ],
    )


def _summary(framework) -> ft.Control:
    return ft.Column(
        spacing=4,
        controls=[
            ft.Text(
                f"{framework.title}｜{framework.game_type.upper()}｜{framework.level_cap} 级",
                size=14,
                weight=ft.FontWeight.W_600,
                color=FG,
            ),
            ft.Text(
                f"经验：{framework.exp_curve.formula}　公式：{framework.combat.expression}",
                size=11,
                color=MUTED,
            ),
        ],
    )
