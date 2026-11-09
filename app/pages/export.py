"""导出：方案 A（独立目录） / 方案 C（写入工程并调 luban），并持久化。"""

from pathlib import Path

import flet as ft

from app.config_store import save_config
from app.state import AppState
from app.theme import ACCENT, BG, BORDER, DANGER, FG, MUTED, PANEL, SUCCESS
from app.widgets import card, primary_button, section_title, text_input
from core.exporter.config import ExportConfig
from core.exporter.service import export_framework, preview_export


def build_export(page: ft.Page, state: AppState) -> ft.Control:
    saved = state.config.export
    mode = ft.RadioGroup(
        value="C" if saved.project_dir else "A",
        content=ft.Column(
            [
                ft.Radio(value="A", label="方案 A：输出到独立目录"),
                ft.Radio(value="C", label="方案 C：写入 luban 工程（自动备份 + 调 luban）"),
            ],
            spacing=2,
        ),
    )
    output_dir = text_input("独立输出目录", str(saved.output_dir), width=520)
    project_dir = text_input(
        "luban 工程目录（方案 C 必填）",
        str(saved.project_dir) if saved.project_dir else "",
        width=520,
    )
    log = ft.Text("", size=11, color=MUTED, selectable=True)
    diff_box = ft.Column(spacing=10)
    diff_card = ft.Container(
        visible=False,
        height=380,
        content=card(
            section_title("差异详情（逐格）"),
            diff_box,
            scroll=ft.ScrollMode.AUTO,
        ),
    )

    def do_export(config: ExportConfig) -> None:
        log.value = "导出中..."
        page.update()

        def work() -> None:
            try:
                result = export_framework(state.framework, config)
                lines = [f"导出成功：{len(result.files)} 个表 -> {config.datas_dir()}"]
                lines.extend(_summarize_diffs(result.diffs))
                if result.code_dir:
                    lines.append(f"代码：{result.code_dir}")
                    lines.append(f"数据：{result.data_dir}")
                lines.extend(_summarize_log(result.luban_log))
                log.value = "\n".join(lines)
                diff_box.controls = _diff_controls(result.diffs)
                diff_card.visible = bool(result.diffs)
            except Exception as exc:
                log.value = f"导出失败：{exc}"
            page.update()

        page.run_thread(work)

    def on_export(_e) -> None:
        if state.framework is None:
            log.value = "请先在工作台生成数值框架"
            page.update()
            return
        project = project_dir.value.strip()
        if mode.value == "C" and not project:
            log.value = "方案 C 需要填写 luban 工程目录"
            page.update()
            return

        config = ExportConfig(
            luban_dll=saved.luban_dll,
            project_dir=Path(project) if project else None,
            output_dir=Path(output_dir.value.strip() or str(saved.output_dir)),
            backup_dir=saved.backup_dir,
        )
        state.config.export = config
        save_config(state.config)

        try:
            diffs = preview_export(state.framework, config)
        except Exception as exc:
            log.value = f"预览差异失败：{exc}"
            page.update()
            return

        if not diffs:
            do_export(config)
            return

        body = ft.Column(
            [
                ft.Text("以下表将被覆盖（旧表会自动备份）：", size=12, color=FG),
                *[
                    ft.Text(
                        f"  {diff.table}：修改 {len(diff.changed)} 格"
                        f" / 新增 {diff.added} 行 / 删除 {diff.removed} 行",
                        size=12,
                        color=MUTED,
                    )
                    for diff in diffs
                ],
                ft.Divider(height=1, color=BORDER),
                *_diff_controls(diffs),
            ],
            spacing=6,
            scroll=ft.ScrollMode.AUTO,
        )
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("确认写入", size=15, weight=ft.FontWeight.W_600, color=FG),
            content=ft.Container(width=480, height=360, content=body),
            bgcolor=PANEL,
            shape=ft.RoundedRectangleBorder(radius=12),
            actions=[
                ft.TextButton("取消", on_click=lambda ev: page.pop_dialog()),
                ft.Button(
                    "确认写入",
                    bgcolor=ACCENT,
                    color="#FFFFFF",
                    on_click=lambda ev: (page.pop_dialog(), do_export(config)),
                ),
            ],
        )
        page.show_dialog(dialog)

    return ft.Column(
        spacing=16,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Text("导出", size=20, weight=ft.FontWeight.W_600, color=FG),
            ft.Text("配置为空时默认方案 A；填写工程目录后按方案 C 导出", size=12, color=MUTED),
            card(section_title("导出模式"), mode),
            card(
                section_title("路径"),
                output_dir,
                project_dir,
                ft.Row([primary_button("开始导出", on_export, icon=ft.Icons.DOWNLOAD)]),
            ),
            card(
                section_title("导出结果"),
                ft.Container(
                    padding=12,
                    bgcolor=BG,
                    border_radius=6,
                    border=ft.Border.all(1, BORDER),
                    content=log,
                ),
            ),
            diff_card,
        ],
    )


def _summarize_diffs(diffs) -> list[str]:
    if not diffs:
        return ["", "差异：无（首次导出或表内容未变）"]
    lines = ["", "差异（对比导出前的旧表，旧表已备份）："]
    for diff in diffs:
        lines.append(
            f"  {diff.table}：新增 {diff.added} 行 / 删除 {diff.removed} 行 / "
            f"修改 {len(diff.changed)} 格"
        )
        for change in diff.changed[:6]:
            lines.append(f"    {change.row} 行 {change.column}：{change.old} → {change.new}")
        if len(diff.changed) > 6:
            lines.append(f"    ... 还有 {len(diff.changed) - 6} 处")
    return lines


def _diff_controls(diffs) -> list[ft.Control]:
    """逐格差异控件：每张表一组，每格一行（旧值 → 新值）。"""
    if not diffs:
        return []
    controls: list[ft.Control] = []
    for diff in diffs:
        controls.append(
            ft.Column(
                [
                    ft.Text(
                        f"{diff.table}　修改 {len(diff.changed)} 格"
                        f" / 新增 {diff.added} 行 / 删除 {diff.removed} 行",
                        size=12,
                        weight=ft.FontWeight.W_600,
                        color=FG,
                    ),
                    *[
                        ft.Row(
                            [
                                ft.Text(f"行 {change.row}", size=11, color=MUTED, width=70),
                                ft.Text(change.column, size=11, color=FG, width=120),
                                ft.Text(change.old, size=11, color=DANGER, width=110),
                                ft.Text("→", size=11, color=MUTED),
                                ft.Text(change.new, size=11, color=SUCCESS, width=110),
                            ],
                            spacing=6,
                        )
                        for change in diff.changed
                    ],
                ],
                spacing=4,
            )
        )
    return controls


def _summarize_log(log: str) -> list[str]:
    if not log:
        return []
    keywords = ("[new]", "ERROR", "运行失败")
    lines = [line.strip() for line in log.splitlines() if any(k in line for k in keywords)]
    return ["", "luban 输出：", *lines[:15]]
