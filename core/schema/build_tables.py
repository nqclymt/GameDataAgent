"""把数值框架映射为 luban 表定义与数据表。"""

from pathlib import Path

from core.calc.growth import attribute_value, exp_at, power_at
from core.modeling.framework import Attribute, ValueFramework
from core.schema.luban import Column, TableDef, write_data_sheet, write_tables_def


def generate_luban_tables(framework: ValueFramework, out_dir: Path) -> list[Path]:
    """生成属性、等级、属性数值（+ 经济、掉落）表与 __tables__ 定义。"""
    out_dir.mkdir(parents=True, exist_ok=True)

    attr_path = out_dir / "cfg_Attribute.xlsx"
    level_path = out_dir / "cfg_Role_Level.xlsx"
    value_path = out_dir / "cfg_Role_Attribute.xlsx"
    tables_path = out_dir / "__tables__.xlsx"

    _write_attributes(attr_path, framework)
    _write_levels(level_path, framework)
    _write_attribute_values(value_path, framework)

    files = [attr_path, level_path, value_path]
    defs = [
        TableDef("role.TbAttr", "Attr", "cfg_Attribute.xlsx"),
        TableDef("role.TbLevel", "LevelConf", "cfg_Role_Level.xlsx"),
        TableDef("role.TbRoleAttr", "RoleAttr", "cfg_Role_Attribute.xlsx"),
    ]

    power_path = out_dir / "cfg_Power.xlsx"
    _write_power(power_path, framework)
    files.append(power_path)
    defs.append(TableDef("role.TbPower", "PowerConf", "cfg_Power.xlsx"))

    if framework.equipment.slots:
        equip_specs = [
            ("cfg_EquipSlot.xlsx", _write_equip_slots, "equip.TbSlot", "EquipSlot"),
            ("cfg_EquipQuality.xlsx", _write_equip_qualities, "equip.TbQuality", "EquipQuality"),
            ("cfg_Enhance.xlsx", _write_enhance, "equip.TbEnhance", "EquipEnhance"),
        ]
        for filename, writer, full_name, sheet_name in equip_specs:
            equip_path = out_dir / filename
            writer(equip_path, framework)
            files.append(equip_path)
            defs.append(TableDef(full_name, sheet_name, filename))

    if framework.equipment.affixes:
        affix_path = out_dir / "cfg_Affix.xlsx"
        _write_affixes(affix_path, framework)
        files.append(affix_path)
        defs.append(TableDef("equip.TbAffix", "Affix", "cfg_Affix.xlsx"))

    if framework.equipment.sets:
        set_path = out_dir / "cfg_EquipSet.xlsx"
        _write_equip_sets(set_path, framework)
        files.append(set_path)
        defs.append(TableDef("equip.TbEquipSet", "EquipSet", "cfg_EquipSet.xlsx"))

    if framework.progression.breakthroughs:
        bt_path = out_dir / "cfg_Breakthrough.xlsx"
        _write_breakthrough(bt_path, framework)
        files.append(bt_path)
        defs.append(
            TableDef("grow.TbBreakthrough", "Breakthrough", "cfg_Breakthrough.xlsx")
        )

    if framework.progression.talent.enabled:
        talent_path = out_dir / "cfg_Talent.xlsx"
        _write_talent(talent_path, framework)
        files.append(talent_path)
        defs.append(TableDef("grow.TbTalent", "Talent", "cfg_Talent.xlsx"))

    if framework.professions:
        prof_path = out_dir / "cfg_Profession.xlsx"
        _write_professions(prof_path, framework)
        files.append(prof_path)
        defs.append(
            TableDef("role.TbProfession", "Profession", "cfg_Profession.xlsx")
        )

    if framework.investment.bands:
        invest_path = out_dir / "cfg_Investment.xlsx"
        _write_investment(invest_path, framework)
        files.append(invest_path)
        defs.append(
            TableDef("economy.TbInvestment", "InvestmentConf", "cfg_Investment.xlsx")
        )

    if framework.gacha:
        gacha_path = out_dir / "cfg_Gacha.xlsx"
        _write_gacha(gacha_path, framework)
        files.append(gacha_path)
        defs.append(TableDef("gacha.TbPool", "GachaPool", "cfg_Gacha.xlsx"))

    if framework.economy.flows:
        economy_path = out_dir / "cfg_Economy.xlsx"
        _write_economy(economy_path, framework)
        files.append(economy_path)
        defs.append(TableDef("economy.TbEconomy", "EconomyConf", "cfg_Economy.xlsx"))

    if framework.drop_tables:
        drop_path = out_dir / "cfg_Drop.xlsx"
        _write_drops(drop_path, framework)
        files.append(drop_path)
        defs.append(TableDef("drop.TbDrop", "DropConf", "cfg_Drop.xlsx"))

    write_tables_def(tables_path, defs)
    files.append(tables_path)
    return files


def _write_equip_slots(path: Path, framework: ValueFramework) -> None:
    columns = [
        Column("id", "int", "c,s", "部位id"),
        Column("slot_key", "string", "c,s", "部位key"),
        Column("name", "string", "c", "名称"),
        Column("attr_key", "string", "c", "加成属性"),
        Column("ratio", "float", "c", "加成比例"),
    ]
    rows = [
        [index, slot.key, slot.name, slot.attr_key, slot.ratio]
        for index, slot in enumerate(framework.equipment.slots, 1)
    ]
    write_data_sheet(path, columns, rows)


def _write_equip_qualities(path: Path, framework: ValueFramework) -> None:
    columns = [
        Column("id", "int", "c,s", "品质id"),
        Column("quality_key", "string", "c,s", "品质key"),
        Column("name", "string", "c", "名称"),
        Column("multiplier", "float", "c", "属性倍率"),
        Column("affix_count", "int", "c", "词条数量"),
    ]
    rows = [
        [
            index,
            quality.key,
            quality.name,
            quality.multiplier,
            quality.affix_count,
        ]
        for index, quality in enumerate(framework.equipment.qualities, 1)
    ]
    write_data_sheet(path, columns, rows)


def _write_affixes(path: Path, framework: ValueFramework) -> None:
    columns = [
        Column("id", "int", "c,s", "词条id"),
        Column("attr_key", "string", "c,s", "属性"),
        Column("value_type", "string", "c", "类型（percent/flat）"),
        Column("min_value", "float", "c", "下限"),
        Column("max_value", "float", "c", "上限"),
        Column("weight", "float", "c", "抽取权重"),
    ]
    rows = [
        [
            index,
            affix.attr_key,
            affix.value_type,
            affix.min_value,
            affix.max_value,
            affix.weight,
        ]
        for index, affix in enumerate(framework.equipment.affixes, 1)
    ]
    write_data_sheet(path, columns, rows)


def _write_equip_sets(path: Path, framework: ValueFramework) -> None:
    columns = [
        Column("id", "int", "c,s", "效果id"),
        Column("set_name", "string", "c,s", "套装名"),
        Column("pieces", "int", "c", "所需件数"),
        Column("attr_key", "string", "c", "属性"),
        Column("value_type", "string", "c", "类型（percent/flat）"),
        Column("value", "float", "c", "数值"),
    ]
    rows: list[list] = []
    index = 1
    for equip_set in framework.equipment.sets:
        for effect in equip_set.effects:
            rows.append(
                [
                    index,
                    equip_set.name,
                    effect.pieces,
                    effect.attr_key,
                    effect.value_type,
                    effect.value,
                ]
            )
            index += 1
    write_data_sheet(path, columns, rows)


def _write_enhance(path: Path, framework: ValueFramework) -> None:
    rule = framework.equipment.enhance
    columns = [
        Column("id", "int", "c,s", "强化等级"),
        Column("multiplier", "float", "c", "加成倍率"),
        Column("cost", "int", "c", "升级消耗"),
    ]
    rows = [
        [level, rule.multiplier(level), rule.cost(level)]
        for level in range(0, rule.max_level + 1)
    ]
    write_data_sheet(path, columns, rows)


def _write_breakthrough(path: Path, framework: ValueFramework) -> None:
    columns = [
        Column("id", "int", "c,s", "突破id"),
        Column("level", "int", "c,s", "卡点等级"),
        Column("resource", "string", "c", "消耗资源"),
        Column("amount", "float", "c", "消耗数量"),
        Column("unlock_level", "int", "c", "解锁等级"),
    ]
    rows = [
        [index, item.level, item.cost_resource, item.cost_amount, item.unlock_level]
        for index, item in enumerate(framework.progression.breakthroughs, 1)
    ]
    write_data_sheet(path, columns, rows)


def _write_talent(path: Path, framework: ValueFramework) -> None:
    talent = framework.progression.talent
    columns = [
        Column("level", "int", "c,s", "等级"),
        Column("points", "float", "c", "累计天赋点"),
        Column("bonus", "float", "c", "加成比例"),
    ]
    rows = [
        [
            level,
            round(level * talent.points_per_level, 2),
            round(level * talent.points_per_level * talent.bonus_per_point, 4),
        ]
        for level in range(1, framework.level_cap + 1)
    ]
    write_data_sheet(path, columns, rows)


def _write_professions(path: Path, framework: ValueFramework) -> None:
    columns = [
        Column("id", "int", "c,s", "行id"),
        Column("name", "string", "c,s", "职业"),
        Column("attr_key", "string", "c,s", "属性"),
        Column("scale", "float", "c", "属性系数"),
    ]
    rows: list[list] = []
    index = 1
    for profession in framework.professions:
        for attr_key, scale in profession.stat_scale.items():
            rows.append([index, profession.name, attr_key, scale])
            index += 1
    write_data_sheet(path, columns, rows)


def _write_investment(path: Path, framework: ValueFramework) -> None:
    columns = [
        Column("id", "int", "c,s", "渠道id"),
        Column("level_start", "int", "c", "起始等级"),
        Column("level_end", "int", "c", "结束等级"),
        Column("source", "string", "c", "渠道"),
        Column("resource", "string", "c", "资源"),
        Column("amount_per_day", "float", "c", "每日投放"),
    ]
    rows: list[list] = []
    index = 1
    for band in framework.investment.bands:
        for source in band.sources:
            rows.append(
                [
                    index,
                    band.level_start,
                    band.level_end,
                    source.name,
                    source.resource,
                    source.amount_per_day,
                ]
            )
            index += 1
    write_data_sheet(path, columns, rows)


def _write_gacha(path: Path, framework: ValueFramework) -> None:
    columns = [
        Column("id", "int", "c,s", "池id"),
        Column("pool", "string", "c,s", "池名"),
        Column("base_rate", "float", "c", "基础出货率"),
        Column("hard_pity", "int", "c", "硬保底抽数（0=无）"),
        Column("soft_pity", "int", "c", "软保底起点（0=无）"),
        Column("soft_step", "float", "c", "软保底每抽增幅"),
        Column("win_rate", "float", "c", "命中目标概率"),
        Column("guarantee", "bool", "c", "大小保底"),
    ]
    rows = [
        [
            index,
            rule.pool,
            rule.base_rate,
            rule.hard_pity or 0,
            rule.soft_pity or 0,
            rule.soft_step,
            rule.win_rate,
            rule.guarantee,
        ]
        for index, rule in enumerate(framework.gacha, 1)
    ]
    write_data_sheet(path, columns, rows)


def _write_power(path: Path, framework: ValueFramework) -> None:
    columns = [
        Column("id", "int", "c,s", "等级"),
        Column("power", "float", "c,s", "战力"),
    ]
    rows = [
        [level, round(power_at(framework, level), 1)]
        for level in range(1, framework.level_cap + 1)
    ]
    write_data_sheet(path, columns, rows)


def _write_economy(path: Path, framework: ValueFramework) -> None:
    columns = [
        Column("id", "int", "c,s", "资源id"),
        Column("resource", "string", "c,s", "资源名"),
        Column("income_per_hour", "float", "c", "每小时产出"),
        Column("cost_per_hour", "float", "c", "每小时消耗"),
        Column("net_per_hour", "float", "c", "净产出"),
        Column("income_growth", "float", "c", "收入每级增幅"),
        Column("cost_growth", "float", "c", "消耗每级增幅"),
        Column("net_at_cap", "float", "c", "满级净产出"),
    ]
    rows = [
        [
            i,
            flow.resource,
            flow.income_per_hour,
            flow.cost_per_hour,
            flow.net_per_hour,
            flow.income_growth,
            flow.cost_growth,
            flow.net_at(framework.level_cap),
        ]
        for i, flow in enumerate(framework.economy.flows, 1)
    ]
    write_data_sheet(path, columns, rows)


def _write_drops(path: Path, framework: ValueFramework) -> None:
    columns = [
        Column("id", "int", "c,s", "条目id"),
        Column("table_name", "string", "c,s", "掉落表"),
        Column("item", "string", "c,s", "物品"),
        Column("probability", "float", "c", "掉率"),
        Column("min_count", "int", "c", "最小数量"),
        Column("max_count", "int", "c", "最大数量"),
    ]
    rows: list[list] = []
    index = 1
    for table in framework.drop_tables:
        for entry in table.entries:
            rows.append(
                [
                    index,
                    table.name,
                    entry.item,
                    entry.probability,
                    entry.min_count,
                    entry.max_count,
                ]
            )
            index += 1
    write_data_sheet(path, columns, rows)


def _write_attributes(path: Path, framework: ValueFramework) -> None:
    columns = [
        Column("id", "int", "c,s", "属性id"),
        Column("attribute", "string", "c,s", "属性键名"),
        Column("attribute_name", "string", "c", "属性中文名"),
    ]
    rows = [[i, attr.key, attr.name] for i, attr in enumerate(framework.attributes, 1)]
    write_data_sheet(path, columns, rows)


def _write_levels(path: Path, framework: ValueFramework) -> None:
    columns = [
        Column("id", "int", "c,s", "id"),
        Column("level", "int", "c,s", "等级"),
        Column("level_name", "string", "c", "等级名称"),
        Column("exp", "long", "c,s", "升级所需经验"),
    ]
    rows = [
        [level, level, f"等级{level}", exp_at(framework, level)]
        for level in range(1, framework.level_cap + 1)
    ]
    write_data_sheet(path, columns, rows)


def _write_attribute_values(path: Path, framework: ValueFramework) -> None:
    columns = [Column("id", "int", "c,s", "属性组id")]
    columns += [Column(a.key, _column_type(a), "c,s", a.name) for a in framework.attributes]
    rows = [
        [level] + [_value_at(attr, level) for attr in framework.attributes]
        for level in range(1, framework.level_cap + 1)
    ]
    write_data_sheet(path, columns, rows)


def _value_at(attr: Attribute, level: int) -> float | int:
    value = attribute_value(attr, level)
    return int(round(value)) if _column_type(attr) == "int" else round(value, 3)


def _column_type(attr: Attribute) -> str:
    """比例类属性（如暴击率）用 float，其余用 int。"""
    if abs(attr.base) < 1 or (attr.growth_type == "linear" and abs(attr.growth) < 1):
        return "float"
    return "int"
