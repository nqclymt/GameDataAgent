"""投放规划分析：各等级段每日投放 vs 每日消耗。"""

from pydantic import BaseModel, Field

from core.modeling.framework import ValueFramework


class BandBalance(BaseModel):
    band: str
    level_start: int
    level_end: int
    mid_level: int
    daily_income: dict[str, float] = Field(default_factory=dict)
    daily_cost: dict[str, float] = Field(default_factory=dict)
    net: dict[str, float] = Field(default_factory=dict)


class InvestmentReport(BaseModel):
    bands: list[BandBalance] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def analyze_investment(framework: ValueFramework) -> InvestmentReport:
    """按等级段对比每日投放（任务/活动/掉落）与每日消耗。"""
    flows = {flow.resource: flow for flow in framework.economy.flows}
    bands: list[BandBalance] = []

    for band in framework.investment.bands:
        mid = (band.level_start + band.level_end) // 2
        income: dict[str, float] = {}
        for source in band.sources:
            income[source.resource] = round(
                income.get(source.resource, 0.0) + source.amount_per_day, 2
            )
        cost = {
            resource: round(flow.cost_at(mid) * 24, 2)
            for resource, flow in flows.items()
        }
        resources = set(income) | set(cost)
        net = {
            resource: round(
                income.get(resource, 0.0) - cost.get(resource, 0.0), 2
            )
            for resource in resources
        }
        bands.append(
            BandBalance(
                band=f"{band.level_start}-{band.level_end}",
                level_start=band.level_start,
                level_end=band.level_end,
                mid_level=mid,
                daily_income=income,
                daily_cost=cost,
                net=net,
            )
        )

    return InvestmentReport(bands=bands, warnings=_warnings(bands))


def _warnings(bands: list[BandBalance]) -> list[str]:
    warnings: list[str] = []
    for balance in bands:
        for resource, value in balance.net.items():
            if value < 0:
                warnings.append(
                    f"{balance.band} 级段 {resource} 每日缺口 {value:.0f}"
                    f"（投放 {balance.daily_income.get(resource, 0.0):.0f}"
                    f" / 消耗 {balance.daily_cost.get(resource, 0.0):.0f}）"
                )
    return warnings
