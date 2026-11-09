"""战斗模拟验证：正确性、暴击影响、可复现性与边界。"""

from core.infer.combat_sim import mitigated_damage, simulate_combat, simulate_combat_curve
from core.modeling.builder import build_framework


def main() -> None:
    print("== 1. 无暴击无浮动：模拟应接近解析（误差 <= 1 次攻击）==")
    hp, atk, defense = 1000.0, 10.0, 5.0
    analytic = hp / mitigated_damage(atk, defense)
    base = simulate_combat(hp, atk, defense, crit=0.0, variance=0.0, trials=2000)
    diff = abs(base.mean_hits - analytic)
    print(
        f"  解析 {analytic:.2f} 次 | 模拟均值 {base.mean_hits} 次"
        f"（差 {diff:.2f} 次，P90 {base.p90_hits}）"
    )
    assert diff <= 1.0, "无随机性时模拟应贴合解析值"

    print("\n== 2. 暴击影响：30% 暴击应明显快于 0% ==")
    low = simulate_combat(hp, atk, defense, crit=0.0, variance=0.0, trials=2000)
    high = simulate_combat(hp, atk, defense, crit=0.3, variance=0.0, trials=2000)
    speedup = (1 - high.mean_hits / low.mean_hits) * 100
    print(
        f"  0% 暴击 {low.mean_hits} 次 → 30% 暴击 {high.mean_hits} 次"
        f"（快 {speedup:.1f}%）"
    )
    assert speedup > 15, "30% 暴击应带来明显加速"

    print("\n== 3. 可复现：同种子两次结果一致 ==")
    a = simulate_combat(hp, atk, defense, crit=0.2, trials=500, seed=7)
    b = simulate_combat(hp, atk, defense, crit=0.2, trials=500, seed=7)
    print(f"  {a.mean_hits} == {b.mean_hits} -> {'一致' if a.mean_hits == b.mean_hits else '不一致'}")
    assert a.mean_hits == b.mean_hits, "固定种子必须可复现"

    print("\n== 4. 边界：缺 hp/atk 的框架返回空 ==")
    sim_framework = build_framework("模拟经营", 30, game_type="sim")
    points = simulate_combat_curve(sim_framework, trials=100)
    print(f"  模拟经营曲线点数：{len(points)}（期望 0）")
    assert points == [], "无 hp/atk 时应返回空"

    print("\n== 5. 各类型曲线（1 级与满级对照）==")
    for game_type, cap in [("rpg", 60), ("card", 60), ("tower", 50), ("slg", 30)]:
        framework = build_framework("测试", cap, game_type=game_type)
        curves = simulate_combat_curve(framework, trials=600)
        if not curves:
            print(f"  {game_type}: 无战斗模拟")
            continue
        first, last = curves[0], curves[-1]
        print(
            f"  {game_type:6s} 1级 解析 {first.analytic_hits:>7.2f} / 模拟 {first.sim_mean:>7.2f}"
            f" (P90 {first.sim_p90:>4d}) | {cap}级 解析 {last.analytic_hits:>9.2f}"
            f" / 模拟 {last.sim_mean:>9.2f} (P90 {last.sim_p90:>5d}) | 波动 {last.volatility}"
        )

    print("\n全部断言通过")


if __name__ == "__main__":
    main()
