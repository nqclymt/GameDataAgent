"""多方案对比验证：同类型不同参数 + 跨类型横向对比。"""

from core.infer.compare import compare_frameworks
from core.modeling.builder import build_framework


def main() -> None:
    variant_a = build_framework("方案A", 60, game_type="rpg")
    variant_b = build_framework("方案B", 60, game_type="rpg")
    for attr in variant_b.attributes:
        if attr.key == "atk":
            attr.growth = 1.12
    variant_c = build_framework("方案C", 60, game_type="card")

    items = [
        ("A 攻击1.10", variant_a),
        ("B 攻击1.12", variant_b),
        ("C 卡牌", variant_c),
    ]
    result = compare_frameworks(items, daily_exp=50000)

    print("\t".join(["指标", *result.names]))
    for row in result.rows:
        print("\t".join([row.label, *row.values]))


if __name__ == "__main__":
    main()
