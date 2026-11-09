"""词条与套装验证：双类型、期望/最差、套装阶梯、边界。"""

from core.calc.equipment import (
    affix_bonus,
    equipment_power_share,
    power_with_equipment,
    set_bonus,
    validate_equipment,
)
from core.calc.growth import power_at
from core.modeling.builder import build_framework


def main() -> None:
    framework = build_framework("测试", 60, game_type="rpg")
    equipment = framework.equipment
    print("== 词条池 ==")
    for affix in equipment.affixes:
        kind = "百分比" if affix.value_type == "percent" else "固定值"
        print(
            f"  {affix.attr_key:<8} {kind}  "
            f"{affix.min_value:g}~{affix.max_value:g}  权重 {affix.weight:g}"
        )

    print("\n== 3 条词条：期望 vs 最差 ==")
    percent, flat = affix_bonus(framework, 3)
    worst_percent, worst_flat = affix_bonus(framework, 3, worst=True)
    print(
        "  期望：百分比 "
        + "，".join(f"{k} {v:+.2%}" for k, v in percent.items())
    )
    print(
        "  期望：固定值 "
        + "，".join(f"{k} {v:+.1f}" for k, v in flat.items())
    )
    print(
        "  最差：百分比 "
        + "，".join(f"{k} {v:+.2%}" for k, v in worst_percent.items())
    )
    print(
        "  最差：固定值 "
        + "，".join(f"{k} {v:+.1f}" for k, v in worst_flat.items())
    )

    print("\n== 套装阶梯（穿戴件数）==")
    for worn in (1, 2, 3):
        percent, _ = set_bonus(equipment, worn)
        summary = (
            "，".join(f"{k} {v:+.0%}" for k, v in percent.items()) or "未激活"
        )
        print(f"  穿 {worn} 件：{summary}")

    print("\n== 装备战力占比（含词条与套装）==")
    for quality in ("common", "rare", "epic", "legendary"):
        share = equipment_power_share(framework, 60, quality, 0)
        print(f"  {quality:<10} +{share:.0%}")

    print("\n== 期望 vs 最差（传说 +10）==")
    bare = power_at(framework, 60)
    expected = power_with_equipment(framework, 60, "legendary", 10)
    worst = power_with_equipment(framework, 60, "legendary", 10, worst=True)
    print(f"  裸装：{bare:,.0f}")
    print(f"  期望：{expected:,.0f}（+{expected / bare - 1:.0%}）")
    print(f"  最差：{worst:,.0f}（+{worst / bare - 1:.0%}）")
    print(
        f"  随机区间：+{worst / bare - 1:.0%} ~ +{expected / bare - 1:.0%}"
    )

    print("\n== 逐层叠加对比（传说 +10）==")
    base_only = power_with_equipment(
        framework, 60, "legendary", 10, with_affix=False, with_set=False
    )
    with_affix_only = power_with_equipment(
        framework, 60, "legendary", 10, with_affix=True, with_set=False
    )
    with_set_only = power_with_equipment(
        framework, 60, "legendary", 10, with_affix=False, with_set=True
    )
    print(f"  部位 + 强化：+{base_only / bare - 1:.0%}")
    print(f"  + 词条：+{with_affix_only / bare - 1:.0%}")
    print(f"  + 套装：+{with_set_only / bare - 1:.0%}")
    print(f"  + 词条 + 套装：+{expected / bare - 1:.0%}")

    print("\n== 非法配置校验 ==")
    equipment.affixes[0].min_value = 0.2
    equipment.affixes[0].max_value = 0.1
    equipment.sets[0].effects[0].pieces = 99
    for warning in validate_equipment(framework):
        print(f"  ⚠ {warning}")


if __name__ == "__main__":
    main()
