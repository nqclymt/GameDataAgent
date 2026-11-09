"""装备与强化对属性的加成计算。

装备提供的是**相对比例**加成（如武器 +60% 攻击），
最终属性 = 基础属性 × (1 + Σ 部位比例 × 品质倍率 × 强化倍率)。
"""

from core.calc.growth import (
    attribute_value,
    power_at,
    power_from_values,
    progression_multiplier,
)
from core.modeling.framework import Attribute, Equipment, ValueFramework


def quality_multiplier(equipment: Equipment, quality_key: str) -> float:
    """按品质 key 取倍率，未匹配时按 1.0。"""
    for quality in equipment.qualities:
        if quality.key == quality_key:
            return quality.multiplier
    return 1.0


def equip_bonus(
    equipment: Equipment,
    quality_key: str,
    enhance_level: int,
) -> dict[str, float]:
    """某品质 + 某强化等级下，全身装备各属性的加成比例。"""
    if not equipment.slots:
        return {}
    multiplier = quality_multiplier(equipment, quality_key) * equipment.enhance.multiplier(
        max(enhance_level, 0)
    )
    bonus: dict[str, float] = {}
    for slot in equipment.slots:
        bonus[slot.attr_key] = (
            bonus.get(slot.attr_key, 0.0) + slot.ratio * multiplier
        )
    return bonus


def attribute_with_equipment(
    framework: ValueFramework,
    attr: Attribute,
    level: int,
    quality_key: str = "",
    enhance_level: int = 0,
) -> float:
    """带装备后的单项属性值。"""
    base = attribute_value(attr, level)
    bonus = equip_bonus(framework.equipment, quality_key, enhance_level)
    return base * (1 + bonus.get(attr.key, 0.0))


def affix_count(equipment: Equipment, quality_key: str) -> int:
    """按品质取词条数量。"""
    for quality in equipment.qualities:
        if quality.key == quality_key:
            return quality.affix_count
    return 0


def affix_bonus(
    framework: ValueFramework, count: int, worst: bool = False
) -> tuple[dict[str, float], dict[str, float]]:
    """抽取词条，返回 (百分比加成, 固定值加成)。

    worst=True 取下限最低的 count 条（最坏情况），
    否则按权重计算每条的期望贡献。
    """
    pool = framework.equipment.affixes
    if not pool or count <= 0:
        return {}, {}
    percent: dict[str, float] = {}
    flat: dict[str, float] = {}

    total_weight = sum(affix.weight for affix in pool) or 1.0
    for affix in pool:
        expected_count = count * affix.weight / total_weight
        value = affix.min_value if worst else affix.expected
        target = percent if affix.value_type == "percent" else flat
        target[affix.attr_key] = (
            target.get(affix.attr_key, 0.0) + value * expected_count
        )
    return percent, flat


def set_bonus(
    equipment: Equipment, worn_pieces: int
) -> tuple[dict[str, float], dict[str, float]]:
    """穿够件数后激活的套装效果，返回 (百分比, 固定值)。"""
    percent: dict[str, float] = {}
    flat: dict[str, float] = {}
    for equip_set in equipment.sets:
        for effect in equip_set.effects:
            if worn_pieces < effect.pieces:
                continue
            target = percent if effect.value_type == "percent" else flat
            target[effect.attr_key] = (
                target.get(effect.attr_key, 0.0) + effect.value
            )
    return percent, flat


def values_with_equipment(
    framework: ValueFramework,
    level: int,
    quality_key: str = "",
    enhance_level: int = 0,
    with_affix: bool = True,
    with_set: bool = True,
    worst: bool = False,
) -> dict[str, float]:
    """带装备（部位 + 词条 + 套装）的整张属性值表。

    最终属性 = 基础 × (1 + 百分比加成) + 固定值加成。
    """
    equipment = framework.equipment
    multiplier = quality_multiplier(
        equipment, quality_key
    ) * equipment.enhance.multiplier(max(enhance_level, 0))

    percent: dict[str, float] = {}
    for slot in equipment.slots:
        percent[slot.attr_key] = (
            percent.get(slot.attr_key, 0.0) + slot.ratio * multiplier
        )

    flat: dict[str, float] = {}
    if with_affix:
        pct, flt = affix_bonus(
            framework, affix_count(equipment, quality_key), worst
        )
        for key, value in pct.items():
            percent[key] = percent.get(key, 0.0) + value
        for key, value in flt.items():
            flat[key] = flat.get(key, 0.0) + value

    if with_set:
        pct, flt = set_bonus(equipment, len(equipment.slots))
        for key, value in pct.items():
            percent[key] = percent.get(key, 0.0) + value
        for key, value in flt.items():
            flat[key] = flat.get(key, 0.0) + value

    return {
        attr.key: attribute_value(attr, level) * (1 + percent.get(attr.key, 0.0))
        + flat.get(attr.key, 0.0)
        for attr in framework.attributes
    }


def validate_equipment(framework: ValueFramework) -> list[str]:
    """词条与套装的合法性检查。"""
    warnings: list[str] = []
    equipment = framework.equipment
    for affix in equipment.affixes:
        if affix.min_value > affix.max_value:
            warnings.append(
                f"词条 {affix.attr_key} 下限 {affix.min_value} 大于上限 {affix.max_value}"
            )
        if affix.value_type not in {"percent", "flat"}:
            warnings.append(
                f"词条 {affix.attr_key} 类型「{affix.value_type}」非法"
            )
    slots = len(equipment.slots)
    for equip_set in equipment.sets:
        for effect in equip_set.effects:
            if effect.pieces > slots:
                warnings.append(
                    f"套装「{equip_set.name}」要求 {effect.pieces} 件，"
                    f"但只配置了 {slots} 个部位"
                )
    return warnings


def power_with_equipment(
    framework: ValueFramework,
    level: int,
    quality_key: str = "",
    enhance_level: int = 0,
    with_affix: bool = True,
    with_set: bool = True,
    worst: bool = False,
) -> float:
    """带装备后的战力（含天赋/转生倍率，与裸装战力同量纲）。"""
    values = values_with_equipment(
        framework,
        level,
        quality_key,
        enhance_level,
        with_affix=with_affix,
        with_set=with_set,
        worst=worst,
    )
    return power_from_values(framework, values) * progression_multiplier(
        framework, level
    )


def equipment_power_share(
    framework: ValueFramework,
    level: int,
    quality_key: str = "",
    enhance_level: int = 0,
) -> float:
    """装备战力占裸装战力的比例（0.35 表示装备让战力提升 35%）。"""
    base = power_at(framework, level)
    if base <= 0:
        return 0.0
    return power_with_equipment(framework, level, quality_key, enhance_level) / base - 1
