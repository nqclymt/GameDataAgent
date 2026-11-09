"""数值框架的可行性分析与预测（统计方法，不训练模型）。

只做可量化的验证：经验曲线、属性成长、战斗 TTK。
"""

import ast
import operator

from pydantic import BaseModel, Field

from core.calc.equipment import equipment_power_share, power_with_equipment
from core.calc.growth import attribute_value, exp_at, power_at
from core.modeling.framework import Attribute, ValueFramework

_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}


class LevelPoint(BaseModel):
    level: int
    exp: int
    cumulative_exp: int


class AttributeGrowth(BaseModel):
    key: str
    name: str
    first: float
    last: float
    ratio: float
    max_step_ratio: float


class CombatPoint(BaseModel):
    level: int
    dps: float
    ttk: float


class PowerPoint(BaseModel):
    level: int
    power: float


class AnalysisReport(BaseModel):
    title: str
    level_cap: int
    total_exp: int
    days_to_max: float | None = None
    levels: list[LevelPoint] = Field(default_factory=list)
    growths: list[AttributeGrowth] = Field(default_factory=list)
    combat: list[CombatPoint] = Field(default_factory=list)
    power_curve: list[PowerPoint] = Field(default_factory=list)
    equip_share_common: float = 0.0
    equip_share_full: float = 0.0
    affix_share_expected: float = 0.0
    affix_share_worst: float = 0.0
    warnings: list[str] = Field(default_factory=list)


def analyze(framework: ValueFramework, daily_exp: float | None = None) -> AnalysisReport:
    """跑一遍可行性分析；daily_exp 用于估算满级所需天数。"""
    levels = _levels(framework)
    total_exp = sum(point.exp for point in levels)
    report = AnalysisReport(
        title=framework.title,
        level_cap=framework.level_cap,
        total_exp=total_exp,
        days_to_max=round(total_exp / daily_exp, 1) if daily_exp else None,
        levels=levels,
        growths=[_growth(attr, framework.level_cap) for attr in framework.attributes],
        combat=_combat(framework),
        power_curve=[
            PowerPoint(level=level, power=round(power_at(framework, level), 1))
            for level in range(1, framework.level_cap + 1)
        ],
    )
    if framework.equipment.slots and framework.equipment.qualities:
        qualities = framework.equipment.qualities
        weakest = min(qualities, key=lambda q: q.multiplier).key
        strongest = max(qualities, key=lambda q: q.multiplier).key
        report.equip_share_common = round(
            equipment_power_share(framework, framework.level_cap, weakest, 0), 3
        )
        report.equip_share_full = round(
            equipment_power_share(
                framework,
                framework.level_cap,
                strongest,
                framework.equipment.enhance.max_level,
            ),
            3,
        )
        if framework.equipment.affixes:
            without = power_with_equipment(
                framework,
                framework.level_cap,
                strongest,
                0,
                with_affix=False,
            )
            if without > 0:
                expected = power_with_equipment(
                    framework, framework.level_cap, strongest, 0
                )
                worst = power_with_equipment(
                    framework, framework.level_cap, strongest, 0, worst=True
                )
                report.affix_share_expected = round(
                    expected / without - 1, 3
                )
                report.affix_share_worst = round(worst / without - 1, 3)
    report.warnings = _warnings(report)
    report.warnings.extend(_economy_warnings(framework))
    if not report.combat and "hp" in {attr.key for attr in framework.attributes}:
        report.warnings.append("战斗公式无法安全求值，已跳过 TTK 分析")
    return report


def _economy_warnings(framework: ValueFramework) -> list[str]:
    """经济与掉落表的合理性检查。"""
    warnings: list[str] = []
    for flow in framework.economy.flows:
        net = flow.net_per_hour
        if net < 0:
            warnings.append(
                f"{flow.resource} 净产出为负（{net:.0f}/小时），长期会枯竭"
            )
        final_net = flow.net_at(framework.level_cap)
        if final_net < 0 <= net:
            warnings.append(
                f"{flow.resource} 满级时净产出转负（{final_net:.0f}/小时），"
                f"消耗增速 {flow.cost_growth:+.0%}/级 偏快"
            )
    for table in framework.drop_tables:
        prob_none = 1.0
        for entry in table.entries:
            if not 0 < entry.probability <= 1:
                warnings.append(
                    f"掉落表「{table.name}」的 {entry.item} 掉率 "
                    f"{entry.probability} 不在 (0, 1] 区间"
                )
            prob_none *= 1 - min(max(entry.probability, 0.0), 1.0)
        if table.entries and prob_none > 0.5:
            warnings.append(
                f"掉落表「{table.name}」空手概率 {prob_none:.0%}，偏高于常规设计"
            )
    return warnings


def safe_eval(expression: str, variables: dict[str, float]) -> float:
    """受限表达式求值：只允许算术运算和已知变量，杜绝 eval。"""
    tree = ast.parse(expression, mode="eval")
    return float(_eval(tree.body, variables))


def _eval(node, variables: dict[str, float]) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.Name):
        if node.id not in variables:
            raise ValueError(f"表达式含未知变量: {node.id}")
        return float(variables[node.id])
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        left = _eval(node.left, variables)
        right = _eval(node.right, variables)
        return _BIN_OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_eval(node.operand, variables)
    raise ValueError("表达式包含不支持的语法")


def _levels(framework: ValueFramework) -> list[LevelPoint]:
    points: list[LevelPoint] = []
    cumulative = 0
    for level in range(1, framework.level_cap + 1):
        exp = exp_at(framework, level)
        cumulative += exp
        points.append(LevelPoint(level=level, exp=exp, cumulative_exp=cumulative))
    return points


def _growth(attr: Attribute, level_cap: int) -> AttributeGrowth:
    first = attribute_value(attr, 1)
    last = attribute_value(attr, level_cap)
    steps = [
        attribute_value(attr, lv) / attribute_value(attr, lv - 1)
        for lv in range(2, level_cap + 1)
        if attribute_value(attr, lv - 1) > 0
    ]
    return AttributeGrowth(
        key=attr.key,
        name=attr.name,
        first=round(first, 2),
        last=round(last, 2),
        ratio=round(last / first, 2) if first else 0.0,
        max_step_ratio=round(max(steps), 3) if steps else 1.0,
    )


def _combat(framework: ValueFramework) -> list[CombatPoint]:
    keys = {attr.key for attr in framework.attributes}
    if "hp" not in keys:
        return []

    points: list[CombatPoint] = []
    for level in range(1, framework.level_cap + 1):
        values = {attr.key: attribute_value(attr, level) for attr in framework.attributes}
        values.setdefault("skill_ratio", 1.0)
        try:
            dps = safe_eval(framework.combat.expression, values)
        except (SyntaxError, ValueError):
            return []
        hp = values.get("hp", 0.0)
        points.append(
            CombatPoint(
                level=level,
                dps=round(dps, 2),
                ttk=round(hp / dps, 2) if dps > 0 else 0.0,
            )
        )
    return points


def _warnings(report: AnalysisReport) -> list[str]:
    warnings: list[str] = []
    for growth in report.growths:
        if growth.max_step_ratio > 1.5:
            warnings.append(f"{growth.name} 单级最大增长 {growth.max_step_ratio}x，曲线偏陡")
        if growth.ratio > 1000:
            warnings.append(f"{growth.name} 满级/1级达 {growth.ratio}x，数值膨胀严重")

    positive = [point.ttk for point in report.combat if point.ttk > 0]
    if positive:
        spread = max(positive) / min(positive)
        if spread > 3:
            warnings.append(f"TTK 在等级间波动 {spread:.1f}x，战斗节奏可能失衡")

    if report.power_curve:
        first = report.power_curve[0].power
        last = report.power_curve[-1].power
        if first > 0 and last / first > 1000:
            warnings.append(f"战力满级/1级达 {last / first:.0f}x，跨度偏大")

    if report.equip_share_full > 2.0:
        warnings.append(
            f"满配装备让战力提升 {report.equip_share_full:.0%}，装备权重偏高"
        )
    return warnings
