"""分段经验曲线验证：加段后节奏卡点是否被识别。"""

from core.infer.pacing import analyze_pacing
from core.modeling.builder import build_framework
from core.modeling.framework import ExpSegment


def main() -> None:
    framework = build_framework("测试", 60, game_type="rpg")

    print("== 平滑曲线（无分段）==")
    base = analyze_pacing(framework, 50000)
    print(f"  满级 {base.total_days:.1f} 天，卡点 {len(base.spikes)} 个")

    framework.exp_curve.segments = [
        ExpSegment(start_level=1, end_level=10, multiplier=0.5, note="新手保护"),
        ExpSegment(start_level=31, end_level=50, multiplier=1.5, note="中期拉长"),
        ExpSegment(start_level=51, end_level=60, multiplier=2.5, note="满级冲刺"),
    ]

    print("\n== 加分段后 ==")
    segmented = analyze_pacing(framework, 50000)
    print(f"  满级 {segmented.total_days:.1f} 天，卡点 {len(segmented.spikes)} 个")
    for spike in segmented.spikes:
        print(
            f"  第 {spike.level} 级需 {spike.days:.2f} 天"
            f"（前一级 {spike.prev_days:.2f}，{spike.ratio}x）"
        )

    print(f"\n  新手段 1-10 级累计：{segmented.points[9].cumulative_days:.2f} 天")
    print(f"  中期段 11-50 级耗时：{segmented.points[49].cumulative_days - segmented.points[9].cumulative_days:.2f} 天")
    print(f"  冲刺段 51-60 级耗时：{segmented.total_days - segmented.points[49].cumulative_days:.2f} 天")


if __name__ == "__main__":
    main()
