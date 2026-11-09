"""经济长期模拟：按成长节奏推进等级，逐日累计货币余额。"""

from pydantic import BaseModel, Field

from core.infer.pacing import analyze_pacing
from core.modeling.framework import ValueFramework


class EconomyDay(BaseModel):
    day: int
    level: int
    income: float
    cost: float
    balance: float


class ResourceSeries(BaseModel):
    resource: str
    days: list[EconomyDay] = Field(default_factory=list)
    peak_day: int = 0
    peak_balance: float = 0.0
    negative_day: int | None = None
    final_balance: float = 0.0


class EconomySimResult(BaseModel):
    days: int
    series: list[ResourceSeries] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def simulate_economy(
    framework: ValueFramework,
    daily_exp: float = 50000.0,
    days: int = 30,
    initial_balance: float = 0.0,
) -> EconomySimResult:
    """模拟 days 天：等级按成长节奏推进，产出/消耗按当级速率逐日结算。"""
    if days < 1:
        raise ValueError("天数必须 >= 1")
    if not framework.economy.flows:
        return EconomySimResult(days=days)

    pacing = analyze_pacing(framework, daily_exp)
    series_list: list[ResourceSeries] = []

    for flow in framework.economy.flows:
        balance = initial_balance
        records: list[EconomyDay] = []
        for day in range(1, days + 1):
            level = _level_on_day(pacing, day)
            income = round(flow.income_at(level) * 24, 2)
            cost = round(flow.cost_at(level) * 24, 2)
            balance += income - cost
            records.append(
                EconomyDay(
                    day=day,
                    level=level,
                    income=income,
                    cost=cost,
                    balance=round(balance, 2),
                )
            )

        peak = max(records, key=lambda item: item.balance)
        negative_day = next(
            (item.day for item in records if item.balance < 0), None
        )
        series_list.append(
            ResourceSeries(
                resource=flow.resource,
                days=records,
                peak_day=peak.day,
                peak_balance=peak.balance,
                negative_day=negative_day,
                final_balance=records[-1].balance,
            )
        )

    return EconomySimResult(
        days=days,
        series=series_list,
        warnings=_warnings(series_list, days),
    )


def _level_on_day(pacing, day: int) -> int:
    """第 day 天对应的等级（按累计天数反查）。"""
    level = 1
    for point in pacing.points:
        if point.cumulative_days <= day:
            level = point.level
        else:
            break
    return level


def _warnings(series_list: list[ResourceSeries], days: int) -> list[str]:
    warnings: list[str] = []
    for series in series_list:
        if series.negative_day is not None:
            warnings.append(
                f"{series.resource} 第 {series.negative_day} 天余额转负"
                f"（{days} 天累计 {series.final_balance:.0f}）"
            )
        elif series.peak_day < days and series.final_balance < series.peak_balance:
            warnings.append(
                f"{series.resource} 第 {series.peak_day} 天见顶后回落，"
                f"后期消耗增速偏快"
            )
    return warnings
