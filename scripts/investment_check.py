"""投放规划验证：各等级段每日投放 vs 消耗。"""

from core.infer.investment import analyze_investment
from core.modeling.builder import build_framework

CASES = [
    ("rpg", 60),
    ("mmorpg", 80),
    ("card", 60),
    ("slg", 30),
    ("tower", 50),
    ("moba", 18),
]


def main() -> None:
    for game_type, cap in CASES:
        framework = build_framework("测试", cap, game_type=game_type)
        report = analyze_investment(framework)
        main_resource = framework.economy.flows[0].resource
        print(f"\n{game_type}（{cap} 级，主资源 {main_resource}）")
        for band in report.bands:
            income = band.daily_income.get(main_resource, 0.0)
            cost = band.daily_cost.get(main_resource, 0.0)
            net = band.net.get(main_resource, 0.0)
            flag = " ⚠" if net < 0 else ""
            print(
                f"  {band.band:<8} 投放 {income:>9,.0f} / 消耗 {cost:>9,.0f}"
                f" / 净 {net:>+10,.0f}{flag}"
            )
        for warning in report.warnings[:3]:
            print(f"  ⚠ {warning}")

    print("\n== 消耗随等级增长后（RPG，cost_growth=0.1）==")
    framework = build_framework("测试", 60, game_type="rpg")
    for flow in framework.economy.flows:
        flow.cost_growth = 0.1
    report = analyze_investment(framework)
    for band in report.bands:
        print(
            f"  {band.band:<8} 投放 {band.daily_income.get('金币', 0):>9,.0f}"
            f" / 消耗 {band.daily_cost.get('金币', 0):>9,.0f}"
            f" / 净 {band.net.get('金币', 0):>+10,.0f}"
        )


if __name__ == "__main__":
    main()
