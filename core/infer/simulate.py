"""蒙特卡洛模拟：抽卡期望与掉落期望（统计方法，不训练模型）。"""

import random

from pydantic import BaseModel, Field


class GachaResult(BaseModel):
    probability: float
    pity: int | None = None
    soft_pity: int | None = None
    soft_step: float = 0.06
    win_rate: float = 1.0
    guarantee: bool = False
    trials: int
    mean_draws: float
    median_draws: float
    p10_draws: float
    p90_draws: float
    mean_draws_to_target: float = 0.0
    p90_draws_to_target: float = 0.0


class DropEntry(BaseModel):
    name: str
    probability: float


class DropItem(BaseModel):
    name: str
    mean_drops: float
    mean_per_kill: float


class DropResult(BaseModel):
    trials: int
    items: list[DropItem] = Field(default_factory=list)


def simulate_gacha(
    probability: float,
    pity: int | None = None,
    trials: int = 20000,
    seed: int | None = 42,
    soft_pity: int | None = None,
    soft_step: float = 0.06,
    win_rate: float = 1.0,
    guarantee: bool = False,
) -> GachaResult:
    """模拟抽卡：软/硬保底 + 可选的大小保底（歪了下次必中）。

    win_rate 为出货时命中目标的概率；guarantee=True 时，
    一旦歪掉，下一次出货必中目标（大小保底）。
    """
    if not 0 < probability <= 1:
        raise ValueError("probability 必须在 (0, 1] 之间")
    if pity is not None and pity < 1:
        raise ValueError("pity 必须 >= 1")
    if soft_pity is not None and soft_pity < 1:
        raise ValueError("soft_pity 必须 >= 1")
    if soft_pity is not None and pity is not None and soft_pity > pity:
        raise ValueError("软保底起点不能晚于硬保底")
    if soft_step <= 0:
        raise ValueError("soft_step 必须大于 0")
    if not 0 < win_rate <= 1:
        raise ValueError("win_rate 必须在 (0, 1] 之间")

    rng = random.Random(seed)
    draws: list[int] = []
    target_draws: list[int] = []
    for _ in range(trials):
        draw = _draw_until_hit(rng, probability, pity, soft_pity, soft_step)
        draws.append(draw)

        if win_rate < 1.0:
            needed = draw
            pending_guarantee = False
            while True:
                hit = pending_guarantee or rng.random() < win_rate
                if hit:
                    target_draws.append(needed)
                    break
                pending_guarantee = guarantee
                needed += _draw_until_hit(
                    rng, probability, pity, soft_pity, soft_step
                )

    draws.sort()
    n = len(draws)
    result = GachaResult(
        probability=probability,
        pity=pity,
        soft_pity=soft_pity,
        soft_step=soft_step,
        win_rate=win_rate,
        guarantee=guarantee,
        trials=trials,
        mean_draws=round(sum(draws) / n, 2),
        median_draws=float(draws[n // 2]),
        p10_draws=float(draws[int(n * 0.1)]),
        p90_draws=float(draws[int(n * 0.9)]),
    )
    if target_draws:
        target_draws.sort()
        m = len(target_draws)
        result.mean_draws_to_target = round(sum(target_draws) / m, 2)
        result.p90_draws_to_target = float(target_draws[int(m * 0.9)])
    return result


def _draw_until_hit(
    rng: random.Random,
    probability: float,
    pity: int | None,
    soft_pity: int | None,
    soft_step: float,
) -> int:
    """抽到出货为止，返回抽数（单次出货）。"""
    limit = pity if pity else 10000
    for count in range(1, limit + 1):
        rate = probability
        if soft_pity is not None and count >= soft_pity:
            rate = min(probability + soft_step * (count - soft_pity + 1), 1.0)
        if rng.random() < rate or (pity is not None and count == pity):
            return count
    return limit


def simulate_drops(
    entries: list[tuple[str, float]],
    kills: int = 1000,
    trials: int = 2000,
    seed: int | None = 42,
) -> DropResult:
    """模拟 kills 次击杀，统计每件物品的平均掉落数。"""
    if kills < 1:
        raise ValueError("kills 必须 >= 1")
    for name, probability in entries:
        if not 0 <= probability <= 1:
            raise ValueError(f"{name} 的掉率必须在 [0, 1] 之间")

    rng = random.Random(seed)
    totals = {name: 0 for name, _ in entries}
    for _ in range(trials):
        for _kill in range(kills):
            for name, probability in entries:
                if rng.random() < probability:
                    totals[name] += 1

    items = [
        DropItem(
            name=name,
            mean_drops=round(totals[name] / trials, 3),
            mean_per_kill=round(totals[name] / trials / kills, 4),
        )
        for name, _ in entries
    ]
    return DropResult(trials=trials, items=items)
