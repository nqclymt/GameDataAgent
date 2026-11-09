"""职业横向对比：属性倾向差异与同等级对战胜率。"""

from pydantic import BaseModel, Field

from core.calc.growth import (
    attribute_value,
    power_from_values,
    progression_multiplier,
)
from core.infer.pvp import win_rate_by_power
from core.modeling.framework import Profession, ValueFramework


class ProfessionPower(BaseModel):
    name: str
    power: float


class DuelResult(BaseModel):
    attacker: str
    defender: str
    attacker_power: float
    defender_power: float
    win_rate: float


class ProfessionReport(BaseModel):
    level: int
    powers: list[ProfessionPower] = Field(default_factory=list)
    duels: list[DuelResult] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def profession_power(
    framework: ValueFramework, profession: Profession, level: int
) -> float:
    """按职业系数调整属性后的战力。"""
    values = {
        attr.key: attribute_value(attr, level)
        * profession.stat_scale.get(attr.key, 1.0)
        for attr in framework.attributes
    }
    return power_from_values(framework, values) * progression_multiplier(
        framework, level
    )


def analyze_professions(
    framework: ValueFramework,
    level: int | None = None,
    scale: float = 1.0,
) -> ProfessionReport:
    """同等级下各职业战力与两两对战胜率。"""
    target = level or framework.level_cap
    target = min(max(target, 1), framework.level_cap)
    report = ProfessionReport(level=target)

    if not framework.professions:
        report.warnings.append("未配置职业")
        return report

    powers = {
        profession.name: profession_power(framework, profession, target)
        for profession in framework.professions
    }
    report.powers = [
        ProfessionPower(name=name, power=round(power, 1))
        for name, power in powers.items()
    ]

    names = list(powers)
    for attacker in names:
        for defender in names:
            if attacker == defender:
                continue
            power_a = powers[attacker]
            power_b = powers[defender]
            report.duels.append(
                DuelResult(
                    attacker=attacker,
                    defender=defender,
                    attacker_power=round(power_a, 1),
                    defender_power=round(power_b, 1),
                    win_rate=round(
                        win_rate_by_power(power_a, power_b, scale), 4
                    ),
                )
            )

    for name in names:
        rates = [item.win_rate for item in report.duels if item.attacker == name]
        if not rates:
            continue
        if max(rates) > 0.65:
            report.warnings.append(
                f"{name} 对部分职业胜率 {max(rates):.0%}，压制过强"
            )
        if min(rates) < 0.35:
            report.warnings.append(
                f"{name} 对部分职业胜率 {min(rates):.0%}，处于劣势"
            )

    return report
