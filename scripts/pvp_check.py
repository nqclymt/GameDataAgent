"""PVP 胜率验证：各类型在满级基准下，等级差对应的胜率。"""

from core.infer.pvp import pvp_curve
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
    print("等级差\t" + "\t".join(f"+{delta}" for delta in (1, 2, 3, 5, 10)))
    for game_type, cap in CASES:
        framework = build_framework("测试", cap, game_type=game_type)
        base = cap // 2
        rows = pvp_curve(framework, base, deltas=(1, 2, 3, 5, 10))
        print(
            f"{game_type:8s}\t"
            + "\t".join(f"{result.win_rate:.0%}" for _, _, result in rows)
        )

    print("\n== 同战力应为 50% ==")
    from core.infer.pvp import compare_pvp, win_rate_by_power

    framework = build_framework("测试", 60, game_type="rpg")
    same = compare_pvp(framework, 30, 30)
    print(f"  同等级 30 vs 30：{same.win_rate:.0%}（比值 {same.ratio}）")
    print(f"  纯函数 100 vs 100：{win_rate_by_power(100, 100):.0%}")

    print("\n== 战力比与胜率对照 ==")
    for ratio in (0.5, 0.8, 1.0, 1.2, 1.5, 2.0, 3.0):
        print(f"  战力比 {ratio:.1f}x -> 胜率 {win_rate_by_power(ratio, 1.0):.0%}")


if __name__ == "__main__":
    main()
