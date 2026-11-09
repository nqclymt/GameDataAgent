"""多方案对比：把多个框架的关键指标拉成一张表。"""

from pydantic import BaseModel, Field

from core.calc.equipment import equipment_power_share
from core.calc.growth import power_at
from core.infer.analysis import analyze
from core.infer.pacing import analyze_pacing
from core.modeling.framework import ValueFramework


class MetricRow(BaseModel):
    """一行指标：label + 每个方案一个字符串值。"""

    label: str
    values: list[str] = Field(default_factory=list)


class CompareResult(BaseModel):
    names: list[str] = Field(default_factory=list)
    rows: list[MetricRow] = Field(default_factory=list)


def compare_frameworks(
    items: list[tuple[str, ValueFramework]],
    daily_exp: float | None = None,
) -> CompareResult:
    """对比多个方案的关键指标（每个方案的分析只跑一次）。"""
    entries = [
        (
            name,
            framework,
            analyze(framework, daily_exp),
            analyze_pacing(framework, daily_exp) if daily_exp else None,
        )
        for name, framework in items
    ]

    return CompareResult(
        names=[name for name, _, _, _ in entries],
        rows=[
            MetricRow(
                label="类型", values=[fw.game_type for _, fw, _, _ in entries]
            ),
            MetricRow(
                label="等级上限", values=[str(fw.level_cap) for _, fw, _, _ in entries]
            ),
            MetricRow(
                label="属性数",
                values=[str(len(fw.attributes)) for _, fw, _, _ in entries],
            ),
            MetricRow(
                label="总经验",
                values=[f"{report.total_exp:,}" for _, _, report, _ in entries],
            ),
            MetricRow(
                label="满级天数",
                values=[
                    f"{pacing.total_days:.1f}" if pacing else "—"
                    for _, _, _, pacing in entries
                ],
            ),
            MetricRow(label="战力", values=[_power_span(fw) for _, fw, _, _ in entries]),
            MetricRow(
                label="TTK",
                values=[_ttk(report) for _, _, report, _ in entries],
            ),
            MetricRow(label="装备战力", values=[_equip(fw) for _, fw, _, _ in entries]),
            MetricRow(
                label="节奏卡点",
                values=[
                    str(len(pacing.spikes)) if pacing else "—"
                    for _, _, _, pacing in entries
                ],
            ),
            MetricRow(
                label="最紧经济", values=[_economy(fw) for _, fw, _, _ in entries]
            ),
        ],
    )


def _power_span(framework: ValueFramework) -> str:
    first = power_at(framework, 1)
    last = power_at(framework, framework.level_cap)
    span = last / first if first else 0
    return f"{first:,.0f} → {last:,.0f}（{span:.0f}x）"


def _ttk(report) -> str:
    if not report.combat:
        return "—"
    positive = [point.ttk for point in report.combat if point.ttk > 0]
    spread = max(positive) / min(positive) if positive else 1
    return (
        f"{report.combat[0].ttk:.1f}s → {report.combat[-1].ttk:.1f}s"
        f"（{spread:.1f}x）"
    )


def _equip(framework: ValueFramework) -> str:
    if not framework.equipment.slots or not framework.equipment.qualities:
        return "—"
    strongest = max(
        framework.equipment.qualities, key=lambda quality: quality.multiplier
    ).key
    share = equipment_power_share(
        framework,
        framework.level_cap,
        strongest,
        framework.equipment.enhance.max_level,
    )
    return f"+{share:.0%}"


def _economy(framework: ValueFramework) -> str:
    if not framework.economy.flows:
        return "—"
    worst = min(framework.economy.flows, key=lambda flow: flow.net_per_hour)
    return f"{worst.resource} {worst.net_per_hour:+.0f}/h"
