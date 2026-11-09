"""抽卡 / 掉落模拟验证。"""

from core.infer.simulate import simulate_drops, simulate_gacha


def main() -> None:
    no_pity = simulate_gacha(probability=0.01, trials=20000)
    print(
        f"单抽 1% 无保底：平均 {no_pity.mean_draws} 抽，"
        f"中位 {no_pity.median_draws}，P10 {no_pity.p10_draws}，P90 {no_pity.p90_draws}"
    )

    with_pity = simulate_gacha(probability=0.01, pity=90, trials=20000)
    print(
        f"单抽 1% + 90 抽保底：平均 {with_pity.mean_draws} 抽，"
        f"中位 {with_pity.median_draws}，P90 {with_pity.p90_draws}"
    )

    drops = simulate_drops(
        entries=[("稀有材料", 0.05), ("普通材料", 0.30), ("金币", 1.0)],
        kills=1000,
        trials=500,
    )
    print(f"\n掉落模拟（{drops.trials} 轮 x 1000 次击杀）：")
    for item in drops.items:
        print(
            f"  {item.name}: 平均 {item.mean_drops} 个"
            f"（每次击杀 {item.mean_per_kill}）"
        )


if __name__ == "__main__":
    main()
