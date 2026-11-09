"""进阶系统验证：突破 / 转生 / 天赋。"""

from core.calc.growth import power_at, progression_multiplier
from core.infer.progression import analyze_progression
from core.modeling.builder import build_framework


def main() -> None:
    print("== RPG 60 级：突破与天赋 ==")
    framework = build_framework("测试", 60, game_type="rpg")
    report = analyze_progression(framework)
    print("  突破节点：")
    for line in report.breakthroughs:
        print(f"    {line}")
    print(f"  突破总消耗：{report.breakthrough_cost}")
    print(
        f"  满级天赋点 {report.talent_points_at_cap:.0f}，"
        f"加成 {report.talent_bonus:.0%}"
    )

    base = power_at(framework, 1)
    cap_power = power_at(framework, 60)
    without_talent = cap_power / progression_multiplier(framework, 60)
    print(f"\n  战力：1 级 {base:,.0f} → 60 级 {cap_power:,.0f}")
    print(
        f"  去掉天赋：{without_talent:,.0f}"
        f"（天赋贡献 {cap_power / without_talent - 1:.0%}）"
    )

    print("\n== 转生倍率（最多 5 次，每次 +5%）==")
    framework.progression.rebirth.enabled = True
    framework.progression.rebirth.stat_bonus = 0.05
    framework.progression.rebirth.max_rebirths = 5
    report = analyze_progression(framework)
    for index, multiplier in enumerate(report.rebirth_multipliers):
        power = power_at(framework, 60, rebirths=index)
        print(f"  转生 {index} 次：×{multiplier:.2f} → 战力 {power:,.0f}")

    print("\n== 其他类型的进阶配置 ==")
    for game_type, cap in (("mmorpg", 80), ("card", 60), ("moba", 18)):
        framework = build_framework("测试", cap, game_type=game_type)
        report = analyze_progression(framework)
        print(
            f"  {game_type:8s} 突破 {len(report.breakthroughs)} 个"
            f" / 天赋 {report.talent_bonus:.0%}"
            f" / 转生 {report.rebirth_enabled}"
        )

    print("\n== 边界：突破点不低于上限 ==")
    framework = build_framework("测试", 60, game_type="rpg")
    framework.progression.breakthroughs[0].level = 60
    report = analyze_progression(framework)
    for warning in report.warnings:
        print(f"  ⚠ {warning}")


if __name__ == "__main__":
    main()
