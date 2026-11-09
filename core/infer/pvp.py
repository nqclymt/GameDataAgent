"""PVP 胜率模型：按双方战力比估算胜率（Elo 式）。"""

from pydantic import BaseModel

from core.calc.growth import power_at
from core.modeling.framework import ValueFramework


class PvpResult(BaseModel):
    attacker_power: float
    defender_power: float
    ratio: float
    win_rate: float


def win_rate_by_power(
    attacker: float, defender: float, scale: float = 1.0
) -> float:
    """战力比换算胜率：ratio^scale / (1 + ratio^scale)。

    scale 越大，战力优势放大越明显（1.0 为对称标准）。
    """
    if attacker <= 0 or defender <= 0:
        return 0.0
    ratio = (attacker / defender) ** scale
    return ratio / (1 + ratio)


def compare_pvp(
    framework: ValueFramework,
    attacker_level: int,
    defender_level: int,
    scale: float = 1.0,
) -> PvpResult:
    """同框架下两个等级的 PVP 胜率对比。"""
    attacker = power_at(framework, attacker_level)
    defender = power_at(framework, defender_level)
    return PvpResult(
        attacker_power=round(attacker, 1),
        defender_power=round(defender, 1),
        ratio=round(attacker / defender, 3) if defender else 0.0,
        win_rate=round(win_rate_by_power(attacker, defender, scale), 4),
    )


def pvp_curve(
    framework: ValueFramework,
    base_level: int,
    deltas: tuple[int, ...] = (0, 1, 2, 3, 5, 10),
    scale: float = 1.0,
) -> list[tuple[int, int, PvpResult]]:
    """攻方比守方高 delta 级时的胜率曲线（返回 (delta, 攻方等级, 结果)）。"""
    results: list[tuple[int, int, PvpResult]] = []
    for delta in deltas:
        attacker_level = min(max(base_level + delta, 1), framework.level_cap)
        result = compare_pvp(framework, attacker_level, base_level, scale)
        results.append((delta, attacker_level, result))
    return results
