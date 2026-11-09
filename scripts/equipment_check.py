"""装备系统验证：部位注入、品质/强化加成、战力占比与消耗曲线。"""

from core.calc.equipment import equipment_power_share, power_with_equipment
from core.calc.growth import power_at
from core.modeling.builder import build_framework

CASES = [
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


def main() -> None:
    print("== 1. 各类型装备部位 ==")
    for game_type, cap in CASES:
        framework = build_framework("测试", cap, game_type=game_type)
        slots = "、".join(slot.name for slot in framework.equipment.slots)
        print(f"  {game_type:8s} {len(framework.equipment.slots)} 个部位：{slots}")

    print("\n== 2. RPG 裸装 vs 带装备（1 级 / 60 级）==")
    framework = build_framework("测试", 60, game_type="rpg")
    for level in (1, 60):
        base = power_at(framework, level)
        common = power_with_equipment(framework, level, "common", 0)
        legend = power_with_equipment(framework, level, "legendary", 10)
        print(
            f"  {level:2d}级 裸装 {base:>10,.0f} | 普通+0 {common:>10,.0f}"
            f"（{common / base - 1:+.0%}）| 传说+10 {legend:>12,.0f}"
            f"（{legend / base - 1:+.0%}）"
        )

    print("\n== 3. 强化等级递增（RPG 60 级，传说品质）==")
    for enhance in (0, 3, 5, 10):
        share = equipment_power_share(framework, 60, "legendary", enhance)
        print(f"  强化 +{enhance:<2d} 装备战力占比 {share:+.0%}")

    print("\n== 4. 各类型装备占比（普通+0 → 传说+10）==")
    for game_type, cap in CASES:
        item = build_framework("测试", cap, game_type=game_type)
        plain = equipment_power_share(item, cap, "common", 0)
        full = equipment_power_share(item, cap, "legendary", 10)
        print(f"  {game_type:8s} {plain:+.0%} → {full:+.0%}")

    print("\n== 5. 强化消耗曲线（RPG）==")
    rule = framework.equipment.enhance
    costs = [rule.cost(level) for level in range(1, rule.max_level + 1)]
    print(f"  +1~+{rule.max_level} 消耗：{costs}")
    print(f"  满级总消耗：{sum(costs):,}")


if __name__ == "__main__":
    main()
