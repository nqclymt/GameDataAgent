"""职业横向对比验证：战力、对战矩阵、平衡度。"""

from core.infer.profession import analyze_professions
from core.modeling.builder import build_framework


def print_matrix(report) -> None:
    names = [item.name for item in report.powers]
    print("            " + "".join(f"{name:<10}" for name in names))
    for attacker in names:
        row = f"  {attacker:<10}"
        for defender in names:
            if attacker == defender:
                row += f"{'—':<10}"
                continue
            rate = next(
                item.win_rate
                for item in report.duels
                if item.attacker == attacker and item.defender == defender
            )
            row += f"{rate:<10.0%}"
        print(row)


def main() -> None:
    for game_type, cap in (("rpg", 60), ("mmorpg", 80)):
        framework = build_framework("测试", cap, game_type=game_type)
        report = analyze_professions(framework)
        print(f"\n== {game_type}（满级 {cap}）==")
        for item in report.powers:
            print(f"  {item.name:<6} 战力 {item.power:>12,.0f}")
        print("  对战矩阵（行=攻方，列=守方）：")
        print_matrix(report)
        for warning in report.warnings:
            print(f"  ⚠ {warning}")

    print("\n== 不同等级下的平衡度（RPG）==")
    framework = build_framework("测试", 60, game_type="rpg")
    for level in (10, 30, 60):
        report = analyze_professions(framework, level=level)
        rates = [item.win_rate for item in report.duels]
        print(
            f"  {level:>2} 级：最高 {max(rates):.0%} / 最低 {min(rates):.0%}"
        )

    print("\n== 系数对平衡的影响（法师 atk 从 1.30 调到 1.45）==")
    framework = build_framework("测试", 60, game_type="rpg")
    mage = next(item for item in framework.professions if item.name == "法师")
    mage.stat_scale["atk"] = 1.45
    report = analyze_professions(framework)
    for item in report.powers:
        print(f"  {item.name:<6} 战力 {item.power:>12,.0f}")
    rates = [d.win_rate for d in report.duels if d.attacker == "法师"]
    print(f"  法师胜率范围：{min(rates):.0%} ~ {max(rates):.0%}")

    print("\n== 未配置职业 ==")
    framework = build_framework("测试", 60, game_type="card")
    report = analyze_professions(framework)
    print(f"  {report.warnings}")


if __name__ == "__main__":
    main()
