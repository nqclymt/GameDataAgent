"""infer 层验证：框架可行性分析 + 曲线拟合闭环。"""

from core.infer.analysis import analyze
from core.infer.fitting import fit_attribute, fit_exp, parse_points
from core.modeling.builder import build_framework


def main() -> None:
    framework = build_framework("苍梧纪", level_cap=60)
    report = analyze(framework, daily_exp=50000)

    print(f"{report.title}：{report.level_cap} 级，总经验 {report.total_exp:,}")
    print(f"按日均 5 万经验，约 {report.days_to_max} 天满级")
    if report.combat:
        print(
            f"TTK：1级 {report.combat[0].ttk}s -> "
            f"{report.level_cap}级 {report.combat[-1].ttk}s"
        )
    for warning in report.warnings or ["（无警告）"]:
        print(f"  - {warning}")

    points = parse_points("10:100; 30:1000; 60:10000")
    outcome = fit_exp(framework, points)
    print(
        f"\n经验曲线拟合：base={outcome.params['a']:.4f} "
        f"exponent={outcome.params['b']:.4f} R²={outcome.r2:.4f}"
    )
    for warning in outcome.warnings:
        print(f"  ⚠ {warning}")

    hp_points = parse_points("1:100; 20:800; 60:80000")
    hp_outcome = fit_attribute(framework, "hp", hp_points)
    print(
        f"生命曲线拟合：base={hp_outcome.params['base']:.2f} "
        f"growth={hp_outcome.params['growth']:.4f} R²={hp_outcome.r2:.4f}"
    )

    updated = analyze(framework, daily_exp=50000)
    print(
        f"\n拟合后重算：总经验 {updated.total_exp:,}，"
        f"满级 {updated.days_to_max} 天，TTK 1级 {updated.combat[0].ttk}s"
    )


if __name__ == "__main__":
    main()
