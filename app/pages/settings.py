"""配置：LLM 来源切换（模板 / ccswitch / 自定义）与 Luban 路径，并持久化。"""

from pathlib import Path

import flet as ft

from app.config_store import save_config
from app.state import AppState
from app.theme import FG, MUTED
from app.widgets import card, primary_button, section_title, select, text_input
from llm.ccswitch import read_ccswitch_providers
from llm.config import ProviderConfig


def build_settings(page: ft.Page, state: AppState) -> ft.Control:
    providers = read_ccswitch_providers()
    current = state.config.provider
    is_custom = current is not None and current.name == "custom"

    source = ft.RadioGroup(
        value="template" if current is None else ("custom" if is_custom else "ccswitch"),
        content=ft.Column(
            [
                ft.Radio(value="template", label="模板模式（不调用 LLM）"),
                ft.Radio(value="ccswitch", label="导入 ccswitch 供应商"),
                ft.Radio(value="custom", label="自定义配置"),
            ],
            spacing=2,
        ),
    )

    provider_dd = select(
        "ccswitch 供应商",
        [
            ft.DropdownOption(key=str(i), text=f"{p.name} | {p.protocol} | {p.model}")
            for i, p in enumerate(providers)
        ],
        value=_match_index(providers, current) if providers else None,
        width=520,
    )

    protocol = select(
        "协议",
        [
            ft.DropdownOption(key="openai", text="openai"),
            ft.DropdownOption(key="anthropic", text="anthropic"),
        ],
        value=current.protocol if is_custom else "openai",
        width=180,
    )
    model = text_input("模型名", current.model if is_custom else "", width=260)
    base_url = text_input("Base URL", current.base_url if is_custom else "", width=520)
    api_key = text_input(
        "API Key", current.api_key if is_custom else "", width=520, password=True
    )
    luban_dll = text_input(
        "Luban.dll 路径", str(state.config.export.luban_dll), width=520
    )
    status = ft.Text("", size=12, color=MUTED)

    def on_apply(_e) -> None:
        try:
            if source.value == "template":
                state.config.provider = None
                message = "已切换到模板模式"
            elif source.value == "ccswitch":
                if not providers:
                    raise ValueError("未找到 ccswitch 供应商")
                state.config.provider = providers[int(provider_dd.value or 0)]
                message = (
                    f"已使用：{state.config.provider.name}"
                    f"（{state.config.provider.protocol}）"
                )
            else:
                if not (base_url.value and api_key.value and model.value):
                    raise ValueError("请填写 Base URL / API Key / 模型名")
                state.config.provider = ProviderConfig(
                    name="custom",
                    protocol=protocol.value,
                    base_url=base_url.value.strip(),
                    api_key=api_key.value.strip(),
                    model=model.value.strip(),
                )
                message = "已使用自定义配置"

            if luban_dll.value.strip():
                state.config.export.luban_dll = Path(luban_dll.value.strip())
            save_config(state.config)
            status.value = f"{message}（已保存）"
        except Exception as exc:
            status.value = f"配置失败：{exc}"
        page.update()

    return ft.Column(
        spacing=16,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Text("配置", size=20, weight=ft.FontWeight.W_600, color=FG),
            ft.Text(
                f"ccswitch 检测到 {len(providers)} 个供应商；配置会保存到本地",
                size=12,
                color=MUTED,
            ),
            card(
                section_title("LLM 来源"),
                source,
                ft.Text("ccswitch 供应商", size=11, color=MUTED),
                provider_dd,
            ),
            card(
                section_title("自定义配置"),
                ft.Row([protocol, model], spacing=12),
                base_url,
                api_key,
            ),
            card(section_title("Luban"), luban_dll),
            ft.Row([primary_button("应用配置", on_apply), status], spacing=12),
        ],
    )


def _match_index(providers, current) -> str:
    if current is None:
        return "0"
    for i, provider in enumerate(providers):
        if provider.name == current.name and provider.model == current.model:
            return str(i)
    return "0"
