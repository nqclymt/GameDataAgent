"""经济长期模拟验证：默认消耗 vs 消耗随等级增长。"""

from core.infer.economy_sim import simulate_economy
from core.modeling.builder import build_framework


def report(label: str, framework, days: int = 30) -> None:
    result = simulate_economy(framework, daily_exp=50000, days=days)
    print(f"\n{label}")
    for series in result.series:
        row = (
            f"  {series.resource:<6} 最终 {series.final_balance:>12,.0f}"
            f" | 峰值第 {series.peak_day} 天（{series.peak_balance:,.0f}）"
        )
        if series.negative_day:
            row += f" | 第 {series.negative_day} 天转负"
        print(row)
    for warning in result.warnings:
        print(f"  ⚠ {warning}")


def main() -> None:
    print("== RPG 30 天经济模拟 ==")
    framework = build_framework("测试", 60, game_type="rpg")
    report("默认（收支均不随等级增长）", framework)

    for flow in framework.economy.flows:
        flow.income_growth = 0.10
        flow.cost_growth = 0.10
    report("收支同步 +10%/级（应稳定）", framework)

    for flow in framework.economy.flows:
        flow.income_growth = 0.08
        flow.cost_growth = 0.12
    report("收入 +8% / 消耗 +12%/级（后期会紧）", framework)

    for flow in framework.economy.flows:
        flow.income_growth = 0.15
        flow.cost_growth = 0.05
    report("收入 +15% / 消耗 +5%/级（会通胀）", framework)

    for flow in framework.economy.flows:
        flow.income_growth = 0.08
        flow.cost_growth = 0.12
    print("\n== 关键天数抽样（收入 +8% / 消耗 +12%）==")
    result = simulate_economy(framework, daily_exp=50000, days=30)
    for series in result.series:
        if series.resource != "金币":
            continue
        for item in series.days:
            if item.day in (1, 5, 10, 15, 20, 25, 30):
                print(
                    f"  第 {item.day:2d} 天（{item.level:2d} 级）："
                    f"产出 {item.income:>8,.0f} / 消耗 {item.cost:>8,.0f}"
                    f" / 余额 {item.balance:>12,.0f}"
                )


if __name__ == "__main__":
    main()
