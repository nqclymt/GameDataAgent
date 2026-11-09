"""战斗蒙特卡洛模拟：带暴击与伤害浮动的击杀次数分布。

与解析法（hp / dps）的区别：解析法忽略暴击与随机性，
这里对每场战斗逐次攻击掷骰，得到击杀次数的分布与波动。
"""

import random

from pydantic import BaseModel

from core.calc.growth import attribute_value
from core.modeling.framework import ValueFramework

# 与战斗公式一致的防御减伤系数
DEFENSE_SOFTNESS = 1000.0
# 单场模拟的攻击次数上限，防止极端参数下死循环
MAX_HITS = 100_000
# 模拟次数硬上限
MAX_TRIALS = 50_000


class CombatDistribution(BaseModel):
    """单场战斗模拟的分布统计（单位：攻击次数）。"""

    trials: int
    mean_hits: float
    p10_hits: int
    p50_hits: int
    p90_hits: int
    max_hits: int

    @property
    def volatility(self) -> float:
        """波动率：(P90 - P10) / P50，越大说明手气影响越明显。"""
        return (
            round((self.p90_hits - self.p10_hits) / self.p50_hits, 3)
            if self.p50_hits
            else 0.0
        )


class CombatSimPoint(BaseModel):
    """某等级的模拟结果，附带解析法对照。"""

    level: int
    analytic_hits: float
    sim_mean: float
    sim_p10: int
    sim_p50: int
    sim_p90: int
    sim_max: int
    volatility: float


def mitigated_damage(atk: float, defense: float) -> float:
    """防御减伤后的单次伤害期望（与战斗公式一致）。"""
    return atk * (1 - defense / (defense + DEFENSE_SOFTNESS))


def simulate_combat(
    hp: float,
    atk: float,
    defense: float,
    crit: float = 0.0,
    crit_mult: float = 2.0,
    variance: float = 0.1,
    trials: int = 2000,
    seed: int | None = 42,
) -> CombatDistribution:
    """模拟单场战斗：每次攻击按暴击率与浮动掷骰，统计击杀所需次数。"""
    if hp <= 0:
        raise ValueError("hp 必须大于 0")
    if not 0 <= crit <= 1:
        raise ValueError("暴击率必须在 [0, 1] 之间")
    if crit_mult < 1:
        raise ValueError("暴击倍率必须 >= 1")
    if not 0 <= variance < 1:
        raise ValueError("伤害浮动必须在 [0, 1) 之间")
    if trials < 1:
        raise ValueError("模拟次数必须 >= 1")

    damage = mitigated_damage(atk, defense)
    if damage <= 0:
        raise ValueError("伤害为 0，无法模拟（攻击力过低或防御过高）")

    rng = random.Random(seed)
    trials = min(trials, MAX_TRIALS)
    hits = [
        _simulate_once(hp, damage, crit, crit_mult, variance, rng)
        for _ in range(trials)
    ]
    return _stats(hits)


def simulate_combat_curve(
    framework: ValueFramework,
    crit_mult: float = 2.0,
    variance: float = 0.1,
    trials: int = 1000,
    seed: int | None = 42,
) -> list[CombatSimPoint]:
    """对 1~level_cap 逐级跑模拟；等级上限越高，自动降低每级模拟次数。"""
    keys = {attr.key for attr in framework.attributes}
    if not {"hp", "atk"} <= keys:
        return []

    effective = max(200, min(trials, 200_000 // max(framework.level_cap, 1)))
    rng = random.Random(seed)
    points: list[CombatSimPoint] = []
    for level in range(1, framework.level_cap + 1):
        values = {
            attr.key: attribute_value(attr, level) for attr in framework.attributes
        }
        hp = values["hp"]
        atk = values["atk"]
        damage = mitigated_damage(atk, values.get("defense", 0.0))
        if damage <= 0 or hp <= 0:
            continue

        hits = sorted(
            _simulate_once(
                hp, damage, values.get("crit", 0.0), crit_mult, variance, rng
            )
            for _ in range(effective)
        )
        n = len(hits)
        p10, p50, p90 = hits[int(n * 0.1)], hits[n // 2], hits[int(n * 0.9)]
        points.append(
            CombatSimPoint(
                level=level,
                analytic_hits=round(hp / damage, 2),
                sim_mean=round(sum(hits) / n, 2),
                sim_p10=p10,
                sim_p50=p50,
                sim_p90=p90,
                sim_max=hits[-1],
                volatility=round((p90 - p10) / p50, 3) if p50 else 0.0,
            )
        )
    return points


def _simulate_once(
    hp: float,
    damage: float,
    crit: float,
    crit_mult: float,
    variance: float,
    rng: random.Random,
) -> int:
    remaining = hp
    hits = 0
    while remaining > 0 and hits < MAX_HITS:
        hit = damage * rng.uniform(1 - variance, 1 + variance)
        if rng.random() < crit:
            hit *= crit_mult
        remaining -= hit
        hits += 1
    return hits


def _stats(hits: list[int]) -> CombatDistribution:
    data = sorted(hits)
    n = len(data)
    return CombatDistribution(
        trials=n,
        mean_hits=round(sum(data) / n, 2),
        p10_hits=data[int(n * 0.1)],
        p50_hits=data[n // 2],
        p90_hits=data[int(n * 0.9)],
        max_hits=data[-1],
    )
