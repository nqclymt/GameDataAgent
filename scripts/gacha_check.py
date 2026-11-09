"""保底规则验证：基础率 / 硬保底 / 软保底对期望与尾部的影响。"""

from core.infer.simulate import simulate_gacha


def report(label: str, **kwargs) -> None:
    result = simulate_gacha(0.006, trials=20000, **kwargs)
    print(
        f"{label:<30} 平均 {result.mean_draws:>6.1f} 抽 | 中位 {result.median_draws:.0f}"
        f" | P10 {result.p10_draws:.0f} | P90 {result.p90_draws:.0f}"
    )


def main() -> None:
    print("== 0.6% 基础率的四种配置 ==")
    report("无保底")
    report("硬保底 90", pity=90)
    report("硬保底 90 + 软保底 74 起(+6%)", pity=90, soft_pity=74, soft_step=0.06)
    report("硬保底 90 + 软保底 70 起(+10%)", pity=90, soft_pity=70, soft_step=0.10)

    print("\n== 固定软保底 +6%，起点的影响 ==")
    for start in (60, 70, 74, 80):
        report(f"软保底 {start} 起", pity=90, soft_pity=start, soft_step=0.06)

    print("\n== 大小保底（出货时 50% 命中目标）==")
    for guarantee in (False, True):
        result = simulate_gacha(
            0.006,
            pity=90,
            trials=5000,
            soft_pity=74,
            soft_step=0.06,
            win_rate=0.5,
            guarantee=guarantee,
        )
        label = "有大小保底" if guarantee else "无大小保底"
        print(
            f"  {label}：单次出货 {result.mean_draws:.1f} 抽 | "
            f"拿到目标 平均 {result.mean_draws_to_target:.1f} 抽，"
            f"P90 {result.p90_draws_to_target:.0f}"
        )

    print("\n== 参数校验 ==")
    for bad in (
        {"soft_pity": 100, "pity": 90},
        {"soft_step": -0.1},
    ):
        try:
            simulate_gacha(0.006, trials=100, **bad)
            print(f"  {bad} 未报错（异常）")
        except ValueError as exc:
            print(f"  {bad} -> {exc}")


if __name__ == "__main__":
    main()
