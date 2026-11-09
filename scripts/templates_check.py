"""多游戏类型模板验证。"""

from core.infer.analysis import analyze
from core.modeling.builder import build_framework


def main() -> None:
    cases = [
        ("rpg", "RPG", 60),
        ("mmorpg", "MMORPG", 80),
        ("card", "卡牌", 60),
        ("idle", "放置", 200),
        ("slg", "SLG", 30),
        ("tower", "塔防", 50),
        ("shooter", "射击", 50),
        ("moba", "MOBA", 18),
        ("sim", "模拟经营", 30),
    ]
    for game_type, label, level_cap in cases:
        framework = build_framework(f"测试{label}", level_cap=level_cap, game_type=game_type)
        report = analyze(framework, daily_exp=50000)
        attrs = "、".join(f"{a.name}({a.key})" for a in framework.attributes)
        print(f"[{label}] type={framework.game_type} | {len(framework.attributes)} 属性: {attrs}")
        ttk = f"{report.combat[0].ttk}s" if report.combat else "跳过"
        print(f"    总经验 {report.total_exp:,} | TTK {ttk}")
        print(f"    警告: {report.warnings or '无'}")
        print()


if __name__ == "__main__":
    main()
