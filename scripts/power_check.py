"""战力曲线验证：九种类型的战力跨度。"""

from core.infer.analysis import analyze
from core.modeling.builder import build_framework


def main() -> None:
    cases = [
        ("rpg", 60),
        ("mmorpg", 80),
        ("card", 60),
        ("idle", 200),
        ("slg", 30),
        ("tower", 50),
        ("shooter", 50),
        ("moba", 18),
        ("sim", 30),
    ]
    for game_type, cap in cases:
        report = analyze(build_framework("战力测试", cap, game_type=game_type))
        first = report.power_curve[0].power
        last = report.power_curve[-1].power
        print(
            f"{game_type:8s} 1级 {first:>10,.0f} → {cap:>3d}级 {last:>14,.0f}"
            f"（{last / first:.1f}x）"
        )


if __name__ == "__main__":
    main()
