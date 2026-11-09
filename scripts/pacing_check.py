"""成长节奏验证：九种类型在给定日均经验下的到级节奏。"""

from core.infer.pacing import analyze_pacing
from core.modeling.builder import build_framework

CASES = [
    ("rpg", 60, 50000),
    ("mmorpg", 80, 80000),
    ("card", 60, 30000),
    ("idle", 200, 500000),
    ("slg", 30, 20000),
    ("tower", 50, 30000),
    ("shooter", 50, 20000),
    ("moba", 18, 10000),
    ("sim", 30, 40000),
]


def main() -> None:
    for game_type, cap, daily in CASES:
        framework = build_framework("测试", cap, game_type=game_type)
        report = analyze_pacing(framework, daily)
        print(f"\n{game_type}（{cap} 级 / 日均 {daily:,} 经验）")
        print(
            f"  满级 {report.total_days:.1f} 天 | 新手 {report.early_days:.1f}"
            f" / 中期 {report.mid_days:.1f} / 后期 {report.late_days:.1f}"
        )
        if report.spikes:
            for spike in report.spikes[:3]:
                print(
                    f"  卡点：{spike.level} 级 {spike.days:.1f} 天"
                    f"（前一级 {spike.prev_days:.1f}，{spike.ratio}x）"
                )
        else:
            print("  卡点：无（曲线平滑）")

    print("\n== RPG 进度抽样（日均 5 万）==")
    framework = build_framework("测试", 60, game_type="rpg")
    report = analyze_pacing(framework, 50000)
    for point in report.points:
        if point.level in (1, 5, 10, 20, 30, 40, 50, 60):
            print(
                f"  {point.level:2d} 级：累计 {point.cumulative_days:>6.2f} 天"
                f"（本级需 {point.days:.2f} 天）"
            )


if __name__ == "__main__":
    main()
