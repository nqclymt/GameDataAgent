"""属性成长、经验曲线与战力的确定性计算。"""

from core.modeling.framework import Attribute, ValueFramework

# 通用战力权重兜底：生命 1、攻击 10、防御 8、比例类属性放大
_DEFAULT_WEIGHTS = {
    "hp": 1.0,
    "atk": 10.0,
    "defense": 8.0,
    "crit": 500.0,
    "speed": 2.0,
    "dps": 10.0,
    "gold_rate": 100.0,
    "income": 10.0,
}


def attribute_value(attr: Attribute, level: int) -> float:
    """按成长类型计算某等级属性值（level 从 1 开始）。

    未知成长类型直接报错，避免静默按线性算导致数值错误。
    """
    if attr.growth_type == "exponential":
        return attr.base * (attr.growth ** (level - 1))
    if attr.growth_type == "linear":
        return attr.base + attr.growth * (level - 1)
    raise ValueError(f"属性 {attr.key} 的成长类型未知: {attr.growth_type}")


def exp_at(framework: ValueFramework, level: int) -> int:
    """某等级升到下一级所需经验（含分段倍率）。"""
    params = framework.exp_curve.params
    base = params.get("base", 100.0)
    exponent = params.get("exponent", 1.5)
    multiplier = segment_multiplier(framework.exp_curve.segments, level)
    return int(base * (level**exponent) * multiplier)


def segment_multiplier(segments: list, level: int) -> float:
    """取该等级命中的分段倍率；未命中返回 1.0。"""
    for segment in segments:
        if segment.start_level <= level <= segment.end_level:
            return segment.multiplier
    return 1.0


def power_from_values(
    framework: ValueFramework, values: dict[str, float]
) -> float:
    """按给定的属性值表算战力（供带装备等场景复用）。"""
    total = 0.0
    for attr in framework.attributes:
        weight = framework.power.weights.get(
            attr.key, _DEFAULT_WEIGHTS.get(attr.key, 1.0)
        )
        total += values.get(attr.key, 0.0) * weight
    return total


def progression_multiplier(
    framework: ValueFramework, level: int, rebirths: int = 0
) -> float:
    """天赋与转生带来的整体倍率（关闭时返回 1.0）。"""
    multiplier = 1.0
    talent = framework.progression.talent
    if talent.enabled:
        points = level * talent.points_per_level
        multiplier *= 1 + points * talent.bonus_per_point
    rebirth = framework.progression.rebirth
    if rebirth.enabled and rebirths > 0:
        multiplier *= 1 + rebirths * rebirth.stat_bonus
    return multiplier


def power_at(framework: ValueFramework, level: int, rebirths: int = 0) -> float:
    """战力：属性加权和 × 天赋/转生倍率。"""
    values = {
        attr.key: attribute_value(attr, level) for attr in framework.attributes
    }
    return power_from_values(framework, values) * progression_multiplier(
        framework, level, rebirths
    )
