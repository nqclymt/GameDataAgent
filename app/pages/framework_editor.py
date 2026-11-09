"""框架编辑器：可视化增删改属性、成长参数、战斗公式、经济流与掉落表。"""

import flet as ft

from app.theme import BORDER, DANGER, MUTED
from app.widgets import primary_button, section_title, segmented, text_input
from core.modeling.framework import (
    Affix,
    Attribute,
    CombatFormula,
    DropEntry,
    DropTable,
    Economy,
    EnhanceRule,
    Equipment,
    EquipQuality,
    EquipSet,
    EquipSlot,
    ExpSegment,
    GachaRule,
    GrowthCurve,
    Breakthrough,
    InvestmentPlan,
    LevelBandPlan,
    Profession,
    Progression,
    Rebirth,
    ResourceFlow,
    SetEffect,
    SourceTicket,
    Talent,
    ValueFramework,
)

_GROWTH_OPTIONS = [
    {"key": "exponential", "text": "指数", "icon": ft.Icons.SHOW_CHART},
    {"key": "linear", "text": "线性", "icon": ft.Icons.TRENDING_UP},
]


def build_editor(page: ft.Page, framework: ValueFramework, on_apply) -> ft.Control:
    """构建可编辑的框架控件树；点「应用到框架」时回调 on_apply(新框架)。"""
    attr_box = ft.Column(spacing=8)
    rows: list[dict] = []

    def add_row(attr: Attribute | None = None) -> None:
        name_f = text_input("名称", attr.name if attr else "", width=96)
        key_f = text_input("key", attr.key if attr else "", width=92)
        base_f = text_input("base", _num(attr.base) if attr else "10", width=86)
        growth_f = text_input(
            "growth", _num(attr.growth) if attr else "1.1", width=92
        )
        holder = {"value": attr.growth_type if attr else "exponential"}
        type_m = segmented(
            "类型",
            _GROWTH_OPTIONS,
            holder["value"],
            on_change=lambda k: holder.__setitem__("value", k),
        )
        row_data = {
            "name": name_f,
            "key": key_f,
            "base": base_f,
            "growth": growth_f,
            "type": holder,
        }
        rows.append(row_data)

        def remove(_e) -> None:
            rows.remove(row_data)
            attr_box.controls.remove(line)
            page.update()

        line = ft.Row(
            [
                name_f,
                key_f,
                base_f,
                growth_f,
                type_m,
                ft.Container(expand=True),
                _delete_button(remove, "删除该属性"),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.END,
        )
        attr_box.controls.append(line)

    for attr in framework.attributes:
        add_row(attr)

    economy_box = ft.Column(spacing=8)
    economy_rows: list[dict] = []

    def add_economy_row(flow: ResourceFlow | None = None) -> None:
        resource_f = text_input("资源", flow.resource if flow else "", width=120)
        income_f = text_input(
            "产出/h", _num(flow.income_per_hour) if flow else "0", width=110
        )
        cost_f = text_input(
            "消耗/h", _num(flow.cost_per_hour) if flow else "0", width=110
        )
        income_growth_f = text_input(
            "收入增长/级", _num(flow.income_growth) if flow else "0", width=110
        )
        growth_f = text_input(
            "消耗增长/级", _num(flow.cost_growth) if flow else "0", width=110
        )
        row_data = {
            "resource": resource_f,
            "income": income_f,
            "cost": cost_f,
            "income_growth": income_growth_f,
            "growth": growth_f,
        }
        economy_rows.append(row_data)

        def remove(_e) -> None:
            economy_rows.remove(row_data)
            economy_box.controls.remove(line)
            page.update()

        line = ft.Row(
            [
                resource_f,
                income_f,
                income_growth_f,
                cost_f,
                growth_f,
                _delete_button(remove, "删除该资源流"),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.END,
        )
        economy_box.controls.append(line)

    for flow in framework.economy.flows:
        add_economy_row(flow)

    drop_box = ft.Column(spacing=12)
    drop_table_rows: list[dict] = []

    def add_drop_table(table: DropTable | None = None) -> None:
        name_f = text_input("掉落表名", table.name if table else "", width=220)
        entries_box = ft.Column(spacing=8)
        entry_rows: list[dict] = []
        holder = {"name": name_f, "entries": entry_rows}

        def add_entry(entry: DropEntry | None = None) -> None:
            item_f = text_input("物品", entry.item if entry else "", width=130)
            prob_f = text_input(
                "掉率%", _pct(entry.probability) if entry else "100", width=100
            )
            min_f = text_input("最小", str(entry.min_count) if entry else "1", width=80)
            max_f = text_input("最大", str(entry.max_count) if entry else "1", width=80)
            row_data = {
                "item": item_f,
                "prob": prob_f,
                "min": min_f,
                "max": max_f,
            }
            entry_rows.append(row_data)

            def remove_entry(_e) -> None:
                entry_rows.remove(row_data)
                entries_box.controls.remove(entry_line)
                page.update()

            entry_line = ft.Row(
                [
                    item_f,
                    prob_f,
                    min_f,
                    max_f,
                    _delete_button(remove_entry, "删除该条目"),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.END,
            )
            entries_box.controls.append(entry_line)

        if table:
            for entry in table.entries:
                add_entry(entry)

        def add_entry_click(_e) -> None:
            add_entry()
            page.update()

        group = ft.Container(
            padding=10,
            border=ft.Border.all(1, BORDER),
            border_radius=6,
            content=ft.Column(
                [
                    name_f,
                    entries_box,
                    ft.TextButton("添加条目", icon=ft.Icons.ADD, on_click=add_entry_click),
                ],
                spacing=8,
            ),
        )
        drop_table_rows.append(holder)
        drop_box.controls.append(group)

    for table in framework.drop_tables:
        add_drop_table(table)

    slot_box = ft.Column(spacing=8)
    slot_rows: list[dict] = []

    def add_slot_row(slot: EquipSlot | None = None) -> None:
        name_f = text_input("部位", slot.name if slot else "", width=100)
        key_f = text_input("key", slot.key if slot else "", width=110)
        attr_f = text_input("属性", slot.attr_key if slot else "", width=100)
        ratio_f = text_input("比例", _num(slot.ratio) if slot else "0.3", width=80)
        row_data = {
            "name": name_f,
            "key": key_f,
            "attr": attr_f,
            "ratio": ratio_f,
        }
        slot_rows.append(row_data)

        def remove(_e) -> None:
            slot_rows.remove(row_data)
            slot_box.controls.remove(line)
            page.update()

        line = ft.Row(
            [name_f, key_f, attr_f, ratio_f, _delete_button(remove, "删除该部位")],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.END,
        )
        slot_box.controls.append(line)

    for slot in framework.equipment.slots:
        add_slot_row(slot)

    quality_box = ft.Column(spacing=8)
    quality_rows: list[dict] = []

    def add_quality_row(quality: EquipQuality | None = None) -> None:
        name_f = text_input("品质", quality.name if quality else "", width=100)
        key_f = text_input("key", quality.key if quality else "", width=110)
        mult_f = text_input(
            "倍率", _num(quality.multiplier) if quality else "1.0", width=80
        )
        affix_f = text_input(
            "词条数", str(quality.affix_count) if quality else "0", width=80
        )
        row_data = {
            "name": name_f,
            "key": key_f,
            "mult": mult_f,
            "affix": affix_f,
        }
        quality_rows.append(row_data)

        def remove(_e) -> None:
            quality_rows.remove(row_data)
            quality_box.controls.remove(line)
            page.update()

        line = ft.Row(
            [
                name_f,
                key_f,
                mult_f,
                affix_f,
                _delete_button(remove, "删除该品质"),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.END,
        )
        quality_box.controls.append(line)

    for quality in framework.equipment.qualities:
        add_quality_row(quality)

    affix_box = ft.Column(spacing=8)
    affix_rows: list[dict] = []

    def add_affix_row(affix: Affix | None = None) -> None:
        attr_f = text_input("属性", affix.attr_key if affix else "", width=95)
        type_f = text_input(
            "类型", affix.value_type if affix else "percent", width=105
        )
        min_f = text_input(
            "下限", _num(affix.min_value) if affix else "0", width=80
        )
        max_f = text_input(
            "上限", _num(affix.max_value) if affix else "0", width=80
        )
        weight_f = text_input(
            "权重", _num(affix.weight) if affix else "1", width=70
        )
        row_data = {
            "attr": attr_f,
            "type": type_f,
            "min": min_f,
            "max": max_f,
            "weight": weight_f,
        }
        affix_rows.append(row_data)

        def remove(_e) -> None:
            affix_rows.remove(row_data)
            affix_box.controls.remove(line)
            page.update()

        line = ft.Row(
            [
                attr_f,
                type_f,
                min_f,
                max_f,
                weight_f,
                _delete_button(remove, "删除该词条"),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.END,
        )
        affix_box.controls.append(line)

    for affix in framework.equipment.affixes:
        add_affix_row(affix)

    set_box = ft.Column(spacing=8)
    set_rows: list[dict] = []

    def add_set_row(
        equip_set: EquipSet | None = None, effect: SetEffect | None = None
    ) -> None:
        name_f = text_input(
            "套装名", equip_set.name if equip_set else "", width=110
        )
        pieces_f = text_input(
            "件数", str(effect.pieces) if effect else "2", width=70
        )
        attr_f = text_input("属性", effect.attr_key if effect else "", width=90)
        type_f = text_input(
            "类型", effect.value_type if effect else "percent", width=105
        )
        value_f = text_input(
            "数值", _num(effect.value) if effect else "0", width=80
        )
        row_data = {
            "name": name_f,
            "pieces": pieces_f,
            "attr": attr_f,
            "type": type_f,
            "value": value_f,
        }
        set_rows.append(row_data)

        def remove(_e) -> None:
            set_rows.remove(row_data)
            set_box.controls.remove(line)
            page.update()

        line = ft.Row(
            [
                name_f,
                pieces_f,
                attr_f,
                type_f,
                value_f,
                _delete_button(remove, "删除该套装效果"),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.END,
        )
        set_box.controls.append(line)

    for equip_set in framework.equipment.sets:
        for effect in equip_set.effects:
            add_set_row(equip_set, effect)

    prof_box = ft.Column(spacing=8)
    prof_rows: list[dict] = []

    def add_prof_row(profession: Profession | None = None) -> None:
        name_f = text_input(
            "职业", profession.name if profession else "", width=110
        )
        scale_f = text_input(
            "系数（hp:1.25,atk:0.85）",
            _format_scales(profession.stat_scale) if profession else "",
            width=360,
        )
        row_data = {"name": name_f, "scale": scale_f}
        prof_rows.append(row_data)

        def remove(_e) -> None:
            prof_rows.remove(row_data)
            prof_box.controls.remove(line)
            page.update()

        line = ft.Row(
            [name_f, scale_f, _delete_button(remove, "删除该职业")],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.END,
        )
        prof_box.controls.append(line)

    for profession in framework.professions:
        add_prof_row(profession)

    bt_box = ft.Column(spacing=8)
    bt_rows: list[dict] = []

    def add_bt_row(item: Breakthrough | None = None) -> None:
        level_f = text_input(
            "卡点等级", str(item.level) if item else "20", width=100
        )
        res_f = text_input("资源", item.cost_resource if item else "", width=100)
        amt_f = text_input(
            "消耗", _num(item.cost_amount) if item else "0", width=110
        )
        unlock_f = text_input(
            "解锁至", str(item.unlock_level) if item else "40", width=100
        )
        row_data = {
            "level": level_f,
            "res": res_f,
            "amt": amt_f,
            "unlock": unlock_f,
        }
        bt_rows.append(row_data)

        def remove(_e) -> None:
            bt_rows.remove(row_data)
            bt_box.controls.remove(line)
            page.update()

        line = ft.Row(
            [
                level_f,
                res_f,
                amt_f,
                unlock_f,
                _delete_button(remove, "删除该突破"),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.END,
        )
        bt_box.controls.append(line)

    for item in framework.progression.breakthroughs:
        add_bt_row(item)

    rebirth = framework.progression.rebirth
    rebirth_cb = ft.Checkbox(label="开启转生", value=rebirth.enabled)
    rebirth_bonus = text_input(
        "每次加成", _num(rebirth.stat_bonus), width=110
    )
    rebirth_max = text_input(
        "最大次数", str(rebirth.max_rebirths), width=110
    )

    talent_rule = framework.progression.talent
    talent_cb = ft.Checkbox(label="开启天赋", value=talent_rule.enabled)
    talent_points = text_input(
        "每级点数", _num(talent_rule.points_per_level), width=110
    )
    talent_bonus = text_input(
        "每点加成", _num(talent_rule.bonus_per_point), width=110
    )

    invest_box = ft.Column(spacing=8)
    invest_rows: list[dict] = []

    def add_invest_row(
        band_start: int, band_end: int, source: SourceTicket | None = None
    ) -> None:
        start_f = text_input("起始", str(band_start), width=80)
        end_f = text_input("结束", str(band_end), width=80)
        name_f = text_input("渠道", source.name if source else "", width=110)
        res_f = text_input("资源", source.resource if source else "", width=100)
        amt_f = text_input(
            "每日量", _num(source.amount_per_day) if source else "0", width=100
        )
        row_data = {
            "start": start_f,
            "end": end_f,
            "name": name_f,
            "res": res_f,
            "amt": amt_f,
        }
        invest_rows.append(row_data)

        def remove(_e) -> None:
            invest_rows.remove(row_data)
            invest_box.controls.remove(line)
            page.update()

        line = ft.Row(
            [
                start_f,
                end_f,
                name_f,
                res_f,
                amt_f,
                _delete_button(remove, "删除该渠道"),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.END,
        )
        invest_box.controls.append(line)

    default_end = max(11, framework.level_cap // 2)
    for band in framework.investment.bands:
        for source in band.sources:
            add_invest_row(band.level_start, band.level_end, source)

    gacha_box = ft.Column(spacing=8)
    gacha_rows: list[dict] = []

    def add_gacha_row(rule: GachaRule | None = None) -> None:
        pool_f = text_input("池名", rule.pool if rule else "", width=120)
        rate_f = text_input(
            "基础率", _num(rule.base_rate) if rule else "0.006", width=100
        )
        hard_f = text_input(
            "硬保底",
            str(rule.hard_pity) if rule and rule.hard_pity else "",
            width=95,
        )
        soft_f = text_input(
            "软保底",
            str(rule.soft_pity) if rule and rule.soft_pity else "",
            width=95,
        )
        step_f = text_input(
            "增幅", _num(rule.soft_step) if rule else "0.06", width=100
        )
        win_f = text_input("命中率", _num(rule.win_rate) if rule else "1.0", width=100)
        guarantee_cb = ft.Checkbox(
            label="大小保底",
            value=rule.guarantee if rule else False,
            tooltip="歪了下次必中",
        )
        row_data = {
            "pool": pool_f,
            "rate": rate_f,
            "hard": hard_f,
            "soft": soft_f,
            "step": step_f,
            "win": win_f,
            "guarantee": guarantee_cb,
        }
        gacha_rows.append(row_data)

        def remove(_e) -> None:
            gacha_rows.remove(row_data)
            gacha_box.controls.remove(line)
            page.update()

        line = ft.Column(
            [
                ft.Row(
                    [pool_f, rate_f, hard_f, soft_f],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.END,
                ),
                ft.Row(
                    [
                        step_f,
                        win_f,
                        guarantee_cb,
                        _delete_button(remove, "删除该池"),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.END,
                ),
            ],
            spacing=4,
        )
        gacha_box.controls.append(line)

    for rule in framework.gacha:
        add_gacha_row(rule)

    enhance = framework.equipment.enhance
    enh_max = text_input("强化上限", str(enhance.max_level), width=110)
    enh_growth = text_input("每级加成", _num(enhance.growth), width=110)
    enh_cost = text_input("消耗基数", _num(enhance.cost_base), width=110)
    enh_exp = text_input("消耗指数", _num(enhance.cost_exponent), width=110)

    segment_box = ft.Column(spacing=8)
    segment_rows: list[dict] = []

    def add_segment_row(segment: ExpSegment | None = None) -> None:
        start_f = text_input(
            "起始", str(segment.start_level) if segment else "1", width=80
        )
        end_f = text_input(
            "结束", str(segment.end_level) if segment else "10", width=80
        )
        mult_f = text_input(
            "倍率", _num(segment.multiplier) if segment else "1.0", width=80
        )
        note_f = text_input("备注", segment.note if segment else "", width=130)
        row_data = {"start": start_f, "end": end_f, "mult": mult_f, "note": note_f}
        segment_rows.append(row_data)

        def remove(_e) -> None:
            segment_rows.remove(row_data)
            segment_box.controls.remove(line)
            page.update()

        line = ft.Row(
            [start_f, end_f, mult_f, note_f, _delete_button(remove, "删除该分段")],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.END,
        )
        segment_box.controls.append(line)

    for segment in framework.exp_curve.segments:
        add_segment_row(segment)

    exp_base = text_input(
        "经验 base", _num(framework.exp_curve.params.get("base", 100)), width=140
    )
    exp_exp = text_input(
        "经验 exponent",
        _num(framework.exp_curve.params.get("exponent", 1.5)),
        width=140,
    )
    formula = text_input("战斗公式", framework.combat.expression, width=520)
    hint = ft.Text("", size=12, color=MUTED)

    def add_attr_click(_e) -> None:
        add_row()
        page.update()

    def add_economy_click(_e) -> None:
        add_economy_row()
        page.update()

    def add_table_click(_e) -> None:
        add_drop_table()
        page.update()

    def add_segment_click(_e) -> None:
        add_segment_row()
        page.update()

    def add_slot_click(_e) -> None:
        add_slot_row()
        page.update()

    def add_quality_click(_e) -> None:
        add_quality_row()
        page.update()

    def add_affix_click(_e) -> None:
        add_affix_row()
        page.update()

    def add_set_click(_e) -> None:
        add_set_row()
        page.update()

    def add_gacha_click(_e) -> None:
        add_gacha_row()
        page.update()

    def add_invest_click(_e) -> None:
        add_invest_row(1, default_end)
        page.update()

    def add_bt_click(_e) -> None:
        add_bt_row()
        page.update()

    def add_prof_click(_e) -> None:
        add_prof_row()
        page.update()

    def apply(_e) -> None:
        try:
            attributes = [
                Attribute(
                    key=row["key"].value.strip(),
                    name=row["name"].value.strip(),
                    base=float(row["base"].value),
                    growth=float(row["growth"].value),
                    growth_type=row["type"]["value"],
                )
                for row in rows
            ]
            if not attributes:
                raise ValueError("至少保留一个属性")

            flows = [
                ResourceFlow(
                    resource=row["resource"].value.strip(),
                    income_per_hour=_float(row["income"].value),
                    cost_per_hour=_float(row["cost"].value),
                    income_growth=_float(row["income_growth"].value),
                    cost_growth=_float(row["growth"].value),
                )
                for row in economy_rows
                if row["resource"].value.strip()
            ]

            tables_out: list[DropTable] = []
            for holder in drop_table_rows:
                name = holder["name"].value.strip()
                if not name:
                    continue
                entries = [
                    DropEntry(
                        item=entry["item"].value.strip(),
                        probability=_float(entry["prob"].value, 100) / 100,
                        min_count=int(entry["min"].value or 1),
                        max_count=int(entry["max"].value or 1),
                    )
                    for entry in holder["entries"]
                    if entry["item"].value.strip()
                ]
                tables_out.append(DropTable(name=name, entries=entries))

            slots = [
                EquipSlot(
                    key=row["key"].value.strip() or f"slot{index}",
                    name=row["name"].value.strip(),
                    attr_key=row["attr"].value.strip(),
                    ratio=_float(row["ratio"].value, 0.0),
                )
                for index, row in enumerate(slot_rows, 1)
                if row["name"].value.strip()
            ]
            qualities = [
                EquipQuality(
                    key=row["key"].value.strip() or f"quality{index}",
                    name=row["name"].value.strip(),
                    multiplier=_float(row["mult"].value, 1.0),
                    affix_count=int(row["affix"].value or 0),
                )
                for index, row in enumerate(quality_rows, 1)
                if row["name"].value.strip()
            ]
            affixes = [
                Affix(
                    attr_key=row["attr"].value.strip(),
                    value_type=row["type"].value.strip() or "percent",
                    min_value=_float(row["min"].value),
                    max_value=_float(row["max"].value),
                    weight=_float(row["weight"].value, 1.0),
                )
                for row in affix_rows
                if row["attr"].value.strip()
            ]
            set_map: dict[str, list[SetEffect]] = {}
            for row in set_rows:
                if not row["name"].value.strip():
                    continue
                set_map.setdefault(row["name"].value.strip(), []).append(
                    SetEffect(
                        pieces=int(row["pieces"].value or 1),
                        attr_key=row["attr"].value.strip(),
                        value_type=row["type"].value.strip() or "percent",
                        value=_float(row["value"].value),
                    )
                )
            sets = [
                EquipSet(name=name, effects=effects)
                for name, effects in set_map.items()
            ]
            equipment = Equipment(
                slots=slots,
                qualities=qualities,
                enhance=EnhanceRule(
                    max_level=int(enh_max.value or 10),
                    growth=_float(enh_growth.value, 0.12),
                    cost_base=_float(enh_cost.value, 100.0),
                    cost_exponent=_float(enh_exp.value, 1.5),
                ),
                affixes=affixes,
                sets=sets,
            )

            professions = [
                Profession(
                    name=row["name"].value.strip(),
                    stat_scale=_parse_scales(row["scale"].value),
                )
                for row in prof_rows
                if row["name"].value.strip()
            ]

            breakthroughs = [
                Breakthrough(
                    level=int(row["level"].value or 1),
                    cost_resource=row["res"].value.strip(),
                    cost_amount=_float(row["amt"].value),
                    unlock_level=int(row["unlock"].value or 1),
                )
                for row in bt_rows
                if row["level"].value.strip()
            ]
            progression = Progression(
                breakthroughs=breakthroughs,
                rebirth=Rebirth(
                    enabled=bool(rebirth_cb.value),
                    stat_bonus=_float(rebirth_bonus.value, 0.05),
                    max_rebirths=int(rebirth_max.value or 5),
                ),
                talent=Talent(
                    enabled=bool(talent_cb.value),
                    points_per_level=_float(talent_points.value, 0.5),
                    bonus_per_point=_float(talent_bonus.value, 0.01),
                ),
            )

            band_map: dict[tuple[int, int], list[SourceTicket]] = {}
            for row in invest_rows:
                if not row["name"].value.strip():
                    continue
                key = (
                    int(row["start"].value or 1),
                    int(row["end"].value or 1),
                )
                band_map.setdefault(key, []).append(
                    SourceTicket(
                        name=row["name"].value.strip(),
                        resource=row["res"].value.strip(),
                        amount_per_day=_float(row["amt"].value),
                    )
                )
            investment = InvestmentPlan(
                bands=[
                    LevelBandPlan(
                        level_start=start, level_end=end, sources=sources
                    )
                    for (start, end), sources in band_map.items()
                ]
            )

            gacha = [
                GachaRule(
                    pool=row["pool"].value.strip() or f"池子{index}",
                    base_rate=_float(row["rate"].value, 0.006),
                    hard_pity=_int_or_none(row["hard"].value),
                    soft_pity=_int_or_none(row["soft"].value),
                    soft_step=_float(row["step"].value, 0.06),
                    win_rate=_float(row["win"].value, 1.0),
                    guarantee=bool(row["guarantee"].value),
                )
                for index, row in enumerate(gacha_rows, 1)
                if row["pool"].value.strip()
            ]

            updated = ValueFramework(
                game_type=framework.game_type,
                title=framework.title,
                level_cap=framework.level_cap,
                attributes=attributes,
                exp_curve=GrowthCurve(
                    name=framework.exp_curve.name,
                    formula="base * level^exponent",
                    params={
                        "base": float(exp_base.value),
                        "exponent": float(exp_exp.value),
                    },
                    segments=[
                        ExpSegment(
                            start_level=int(row["start"].value or 1),
                            end_level=int(row["end"].value or 1),
                            multiplier=_float(row["mult"].value, 1.0),
                            note=row["note"].value.strip(),
                        )
                        for row in segment_rows
                        if row["start"].value.strip() and row["end"].value.strip()
                    ],
                ),
                combat=CombatFormula(
                    name=framework.combat.name,
                    expression=formula.value.strip(),
                    description=framework.combat.description,
                ),
                economy=Economy(
                    currencies=[flow.resource for flow in flows]
                    or framework.economy.currencies,
                    sources=framework.economy.sources,
                    sinks=framework.economy.sinks,
                    flows=flows,
                ),
                drop_tables=tables_out,
                equipment=equipment,
                gacha=gacha,
                investment=investment,
                progression=progression,
                professions=professions,
                notes=framework.notes,
            )
            on_apply(updated)
            net = "，".join(f"{flow.resource} 净 {flow.net_per_hour:+g}/h" for flow in flows)
            hint.value = f"已应用（{net}）" if net else "已应用"
        except Exception as exc:
            hint.value = f"应用失败：{exc}"
        page.update()

    return ft.Container(
        padding=ft.Padding.only(right=18),
        content=ft.Column(
            spacing=14,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                section_title("属性（可增删改）"),
                attr_box,
                ft.TextButton("添加属性", icon=ft.Icons.ADD, on_click=add_attr_click),
                ft.Divider(height=1, color=BORDER),
                section_title("成长参数"),
                ft.Row([exp_base, exp_exp], spacing=12),
                segment_box,
                ft.TextButton(
                    "添加经验分段", icon=ft.Icons.ADD, on_click=add_segment_click
                ),
                formula,
                ft.Divider(height=1, color=BORDER),
                section_title("经济流（可增删改）"),
                economy_box,
                ft.TextButton(
                    "添加资源流", icon=ft.Icons.ADD, on_click=add_economy_click
                ),
                ft.Divider(height=1, color=BORDER),
                section_title("掉落表（可增删改）"),
                drop_box,
                ft.TextButton(
                    "添加掉落表", icon=ft.Icons.ADD, on_click=add_table_click
                ),
                ft.Divider(height=1, color=BORDER),
                section_title("装备（可增删改）"),
                slot_box,
                ft.TextButton("添加部位", icon=ft.Icons.ADD, on_click=add_slot_click),
                quality_box,
                ft.TextButton("添加品质", icon=ft.Icons.ADD, on_click=add_quality_click),
                ft.Row([enh_max, enh_growth, enh_cost, enh_exp], spacing=8),
                section_title("词条池（可增删改）"),
                affix_box,
                ft.TextButton(
                    "添加词条", icon=ft.Icons.ADD, on_click=add_affix_click
                ),
                section_title("套装（可增删改）"),
                set_box,
                ft.TextButton(
                    "添加套装效果", icon=ft.Icons.ADD, on_click=add_set_click
                ),
                ft.Divider(height=1, color=BORDER),
                section_title("抽卡池（可增删改）"),
                gacha_box,
                ft.TextButton(
                    "添加抽卡池", icon=ft.Icons.ADD, on_click=add_gacha_click
                ),
                ft.Divider(height=1, color=BORDER),
                section_title("职业（可增删改）"),
                prof_box,
                ft.TextButton(
                    "添加职业", icon=ft.Icons.ADD, on_click=add_prof_click
                ),
                ft.Divider(height=1, color=BORDER),
                section_title("进阶（突破/转生/天赋）"),
                bt_box,
                ft.TextButton(
                    "添加突破节点", icon=ft.Icons.ADD, on_click=add_bt_click
                ),
                ft.Row([rebirth_cb, rebirth_bonus, rebirth_max], spacing=12),
                ft.Row([talent_cb, talent_points, talent_bonus], spacing=12),
                ft.Divider(height=1, color=BORDER),
                section_title("投放规划（可增删改）"),
                invest_box,
                ft.TextButton(
                    "添加投放渠道", icon=ft.Icons.ADD, on_click=add_invest_click
                ),
                ft.Divider(height=1, color=BORDER),
                ft.Row(
                    [primary_button("应用到框架", apply), hint],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
        ),
    )


def _delete_button(on_click, tooltip: str) -> ft.IconButton:
    return ft.IconButton(
        icon=ft.Icons.DELETE_OUTLINE,
        icon_color=DANGER,
        icon_size=18,
        on_click=on_click,
        tooltip=tooltip,
        width=32,
        height=32,
        padding=0,
    )


def _num(value) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _float(text: str, default: float = 0.0) -> float:
    value = text.strip()
    return float(value) if value else default


def _format_scales(scales: dict[str, float]) -> str:
    """属性系数表 → hp:1.25,atk:0.85。"""
    return ",".join(f"{key}:{value:g}" for key, value in scales.items())


def _parse_scales(text: str) -> dict[str, float]:
    """解析 hp:1.25,atk:0.85；非法片段跳过。"""
    result: dict[str, float] = {}
    for part in (text or "").split(","):
        if ":" not in part:
            continue
        key, _, value = part.partition(":")
        key = key.strip()
        if not key:
            continue
        try:
            result[key] = float(value.strip())
        except ValueError:
            continue
    return result


def _int_or_none(text: str) -> int | None:
    """空串或非正数返回 None（表示不设保底）。"""
    text = (text or "").strip()
    if not text:
        return None
    value = int(float(text))
    return value if value > 0 else None


def _pct(value: float) -> str:
    return _num(round(value * 100, 2))
