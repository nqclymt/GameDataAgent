"""成长节奏分析：每级耗时、累计天数、阶段汇总与节奏卡点。

只依赖经验曲线和日均经验产出，不涉及随机模拟。
"""

from pydantic import BaseModel, Field

from core.calc.growth import exp_at
from core.modeling.framework import ValueFramework


class PacingPoint(BaseModel):
    level: int
    exp: int
    cumulative_exp: int
    days: float
    cumulative_days: float


class PacingSpike(BaseModel):
    """节奏卡点：该级耗时相对上一级明显陡增。"""

    level: int
    days: float
    prev_days: float
    ratio: float


class PacingReport(BaseModel):
    daily_exp: float
    total_days: float
    early_days: float = 0.0
    mid_days: float = 0.0
    late_days: float = 0.0
    points: list[PacingPoint] = Field(default_factory=list)
    spikes: list[PacingSpike] = Field(default_factory=list)

    @property
    def level_at_day(self) -> dict[int, int]:
        """按天查等级：第 N 天能到几级（同一天取最高等级）。"""
        result: dict[int, int] = {}
        for point in self.points:
            day = int(point.cumulative_days)
            result[day] = point.level
        return result


def analyze_pacing(
    framework: ValueFramework,
    daily_exp: float,
    spike_ratio: float = 1.3,
    min_days: float = 0.5,
) -> PacingReport:
    """按日均经验产出，算出每级耗时与节奏卡点。

    卡点需同时满足：耗时 >= min_days 天，且相对上一级 >= spike_ratio 倍
    （只按倍数会在前几级误报——1 级升 2 级本来就只有几小时）。
    """
    if daily_exp <= 0:
        raise ValueError("日均经验必须大于 0")

    points: list[PacingPoint] = []
    cumulative_exp = 0
    for level in range(1, framework.level_cap + 1):
        exp = exp_at(framework, level)
        cumulative_exp += exp
        points.append(
            PacingPoint(
                level=level,
                exp=exp,
                cumulative_exp=cumulative_exp,
                days=round(exp / daily_exp, 3),
                cumulative_days=round(cumulative_exp / daily_exp, 3),
            )
        )

    spikes = [
        PacingSpike(
            level=point.level,
            days=point.days,
            prev_days=points[index - 1].days,
            ratio=round(point.days / points[index - 1].days, 2),
        )
        for index, point in enumerate(points)
        if index > 0
        and point.days >= min_days
        and points[index - 1].days > 0
        and point.days / points[index - 1].days >= spike_ratio
    ]

    total = points[-1].cumulative_days if points else 0.0
    early = points[9].cumulative_days if len(points) >= 10 else total
    mid_level = max(framework.level_cap // 2, 10)
    mid_end = points[mid_level - 1].cumulative_days if len(points) >= mid_level else total
    return PacingReport(
        daily_exp=daily_exp,
        total_days=total,
        early_days=round(early, 2),
        mid_days=round(mid_end - early, 2),
        late_days=round(total - mid_end, 2),
        points=points,
        spikes=spikes,
    )
