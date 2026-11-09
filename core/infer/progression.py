"""进阶分析：突破节点、转生倍率、天赋加成。"""

from pydantic import BaseModel, Field

from core.modeling.framework import ValueFramework


class ProgressionReport(BaseModel):
    breakthroughs: list[str] = Field(default_factory=list)
    breakthrough_cost: dict[str, float] = Field(default_factory=dict)
    rebirth_enabled: bool = False
    rebirth_multipliers: list[float] = Field(default_factory=list)
    talent_points_at_cap: float = 0.0
    talent_bonus: float = 0.0
    warnings: list[str] = Field(default_factory=list)


def analyze_progression(framework: ValueFramework) -> ProgressionReport:
    """汇总突破节点、转生倍率曲线与天赋加成。"""
    progression = framework.progression
    report = ProgressionReport()

    for breakthrough in progression.breakthroughs:
        report.breakthroughs.append(
            f"{breakthrough.level} 级突破："
            f"消耗 {breakthrough.cost_amount:,.0f} {breakthrough.cost_resource}，"
            f"解锁至 {breakthrough.unlock_level} 级"
        )
        if breakthrough.cost_resource:
            report.breakthrough_cost[breakthrough.cost_resource] = round(
                report.breakthrough_cost.get(breakthrough.cost_resource, 0.0)
                + breakthrough.cost_amount,
                2,
            )
        if breakthrough.level >= framework.level_cap:
            report.warnings.append(
                f"突破点 {breakthrough.level} 不低于等级上限 {framework.level_cap}，不会生效"
            )

    rebirth = progression.rebirth
    if rebirth.enabled:
        report.rebirth_enabled = True
        report.rebirth_multipliers = [
            1 + index * rebirth.stat_bonus
            for index in range(rebirth.max_rebirths + 1)
        ]

    talent = progression.talent
    if talent.enabled:
        report.talent_points_at_cap = (
            framework.level_cap * talent.points_per_level
        )
        report.talent_bonus = (
            report.talent_points_at_cap * talent.bonus_per_point
        )
        if report.talent_bonus > 2.0:
            report.warnings.append(
                f"满级天赋加成 {report.talent_bonus:.0%}，超过基础属性的 2 倍"
            )

    return report
