"""分析：可行性验证 + 目标点拟合闭环。"""

import flet as ft

from app.state import AppState
from app.theme import ACCENT, BORDER, DANGER, FG, MUTED, WARNING
from app.widgets import card, primary_button, section_title, select, text_input
from core.infer.analysis import analyze
from core.infer.combat_sim import simulate_combat_curve
from core.infer.compare import compare_frameworks
from core.infer.economy_sim import simulate_economy
from core.infer.investment import analyze_investment
from core.infer.fitting import fit_attribute, fit_exp, parse_points
from core.infer.pacing import analyze_pacing
from core.infer.profession import analyze_professions
from core.infer.progression import analyze_progression
from core.infer.pvp import pvp_curve
from core.infer.simulate import simulate_gacha


def build_analysis(page: ft.Page, state: AppState) -> ft.Control:
    daily_exp = text_input("日均经验产出（可选）", "50000", width=260)
    result = ft.Column(spacing=6)

    def on_run(_e) -> None:
        if state.framework is None:
            result.controls = [ft.Text("请先在工作台生成数值框架", color=MUTED)]
            page.update()
            return
        try:
            daily = float(daily_exp.value) if daily_exp.value.strip() else None
            report = analyze(state.framework, daily)
            result.controls = _render(report)
        except Exception as exc:
            result.controls = [ft.Text(f"分析失败：{exc}", color=DANGER)]
        page.update()

    fit_options = [ft.DropdownOption(key="exp", text="经验曲线")]
    if state.framework is not None:
        fit_options += [
            ft.DropdownOption(key=attr.key, text=attr.name)
            for attr in state.framework.attributes
        ]

    fit_points = text_input(
        "目标点（等级:数值，分号分隔）",
        "10:100; 30:1000; 60:10000",
        width=420,
    )
    fit_target = select("拟合目标", fit_options, value="exp", width=200)
    fit_status = ft.Text("", size=12, color=MUTED)

    def on_fit(_e) -> None:
        if state.framework is None:
            fit_status.value = "请先在工作台生成数值框架"
            page.update()
            return
        try:
            points = parse_points(fit_points.value)
            if fit_target.value == "exp":
                outcome = fit_exp(state.framework, points)
                fit_status.value = (
                    f"经验曲线已更新：base={outcome.params['a']:.4f} "
                    f"exponent={outcome.params['b']:.4f}，R²={outcome.r2:.4f}"
                    + _warn_text(outcome.warnings)
                )
            else:
                outcome = fit_attribute(state.framework, fit_target.value, points)
                fit_status.value = (
                    f"{fit_target.value} 已更新：base={outcome.params['base']:.4f} "
                    f"growth={outcome.params['growth']:.6f}，R²={outcome.r2:.4f}"
                    + _warn_text(outcome.warnings)
                )
        except Exception as exc:
            fit_status.value = f"拟合失败：{exc}"
        page.update()

    gacha_prob = text_input("单抽概率(%)", "1", width=160)
    gacha_pity = text_input("保底次数(可选)", "90", width=160)
    gacha_soft = text_input("软保底起点(可选)", "74", width=170)
    gacha_step = text_input("软保底增幅(%)", "6", width=170)
    gacha_win = text_input("目标命中率", "1.0", width=150)
    gacha_guarantee = ft.Checkbox(label="大小保底", value=False)
    gacha_trials = text_input("模拟次数", "20000", width=160)
    gacha_status = ft.Text("", size=12, color=MUTED)

    def on_simulate(_e) -> None:
        gacha_status.value = "模拟中..."
        page.update()

        def work() -> None:
            try:
                probability = float(gacha_prob.value.strip()) / 100
                pity_text = gacha_pity.value.strip()
                pity = int(pity_text) if pity_text else None
                soft_text = gacha_soft.value.strip()
                soft_pity = int(soft_text) if soft_text else None
                soft_step = float(gacha_step.value.strip() or "6") / 100
                win_rate = float(gacha_win.value.strip() or "1")
                guarantee = bool(gacha_guarantee.value)
                trials = int(gacha_trials.value.strip() or "20000")
                result = simulate_gacha(
                    probability,
                    pity,
                    trials,
                    soft_pity=soft_pity,
                    soft_step=soft_step,
                    win_rate=win_rate,
                    guarantee=guarantee,
                )
                text = (
                    f"平均 {result.mean_draws} 抽，中位数 {result.median_draws}，"
                    f"P10 {result.p10_draws}，P90 {result.p90_draws}"
                )
                if pity:
                    baseline = simulate_gacha(probability, None, trials)
                    cut = (1 - result.mean_draws / baseline.mean_draws) * 100
                    text += f"\n无保底时平均 {baseline.mean_draws} 抽，保底降低 {cut:.1f}%"
                if soft_pity:
                    hard_only = simulate_gacha(probability, pity, trials)
                    soft_cut = (1 - result.mean_draws / hard_only.mean_draws) * 100
                    text += (
                        f"\n仅硬保底平均 {hard_only.mean_draws} 抽，"
                        f"软保底再降 {soft_cut:.1f}%"
                    )
                if result.mean_draws_to_target:
                    text += (
                        f"\n拿到目标：平均 {result.mean_draws_to_target} 抽，"
                        f"P90 {result.p90_draws_to_target:.0f}"
                    )
                gacha_status.value = text
            except Exception as exc:
                gacha_status.value = f"模拟失败：{exc}"
            page.update()

        page.run_thread(work)

    pvp_base = text_input("基准等级", "30", width=150)
    pvp_status = ft.Text("", size=12, color=MUTED)
    pvp_box = ft.Column(spacing=4)

    def on_pvp(_e) -> None:
        if state.framework is None:
            pvp_status.value = "请先在工作台生成框架"
            page.update()
            return
        try:
            base = int(pvp_base.value.strip() or "30")
            rows = pvp_curve(state.framework, base)
            pvp_status.value = f"基准 {base} 级，攻方比守方高 N 级时的胜率"
            pvp_box.controls = _render_pvp(rows)
        except Exception as exc:
            pvp_status.value = f"计算失败：{exc}"
            pvp_box.controls = []
        page.update()

    compare_status = ft.Text("", size=12, color=MUTED)
    compare_box = ft.Column(spacing=4)

    def on_compare(_e) -> None:
        if len(state.variants) < 2:
            compare_status.value = (
                f"至少需要 2 个方案（当前 {len(state.variants)} 个，"
                f"先在工作台点「保存为方案」）"
            )
            compare_box.controls = []
            page.update()
            return
        try:
            daily_text = pacing_daily.value.strip()
            daily = float(daily_text) if daily_text else None
            result = compare_frameworks(list(state.variants.items()), daily)
            compare_status.value = f"对比 {len(result.names)} 个方案"
            compare_box.controls = _render_compare(result)
        except Exception as exc:
            compare_status.value = f"对比失败：{exc}"
            compare_box.controls = []
        page.update()

    prof_level = text_input("对比等级", "60", width=150)
    prof_status = ft.Text("", size=12, color=MUTED)
    prof_box = ft.Column(spacing=4)

    def on_professions(_e) -> None:
        if state.framework is None:
            prof_status.value = "请先在工作台生成框架"
            page.update()
            return
        try:
            level = int(prof_level.value.strip() or "60")
            report = analyze_professions(state.framework, level)
            if not report.powers:
                prof_status.value = "该框架未配置职业"
                prof_box.controls = []
            else:
                prof_status.value = (
                    f"{report.level} 级，{len(report.powers)} 个职业"
                )
                prof_box.controls = _render_professions(report)
        except Exception as exc:
            prof_status.value = f"计算失败：{exc}"
            prof_box.controls = []
        page.update()

    prog_status = ft.Text("", size=12, color=MUTED)
    prog_box = ft.Column(spacing=4)

    def on_progression(_e) -> None:
        if state.framework is None:
            prog_status.value = "请先在工作台生成框架"
            page.update()
            return
        try:
            report = analyze_progression(state.framework)
            prog_status.value = "进阶系统"
            prog_box.controls = _render_progression(report)
        except Exception as exc:
            prog_status.value = f"分析失败：{exc}"
            prog_box.controls = []
        page.update()

    invest_status = ft.Text("", size=12, color=MUTED)
    invest_box = ft.Column(spacing=4)

    def on_invest(_e) -> None:
        if state.framework is None:
            invest_status.value = "请先在工作台生成框架"
            page.update()
            return
        try:
            report = analyze_investment(state.framework)
            if not report.bands:
                invest_status.value = "该框架没有投放规划"
                invest_box.controls = []
            else:
                invest_status.value = f"{len(report.bands)} 个等级段"
                invest_box.controls = _render_investment(report, state.framework)
        except Exception as exc:
            invest_status.value = f"分析失败：{exc}"
            invest_box.controls = []
        page.update()

    economy_days = text_input("模拟天数", "30", width=150)
    economy_status = ft.Text("", size=12, color=MUTED)
    economy_box = ft.Column(spacing=4)

    def on_economy(_e) -> None:
        if state.framework is None:
            economy_status.value = "请先在工作台生成框架"
            page.update()
            return
        try:
            days = int(economy_days.value.strip() or "30")
            daily = float(pacing_daily.value.strip() or "50000")
            result = simulate_economy(
                state.framework, daily_exp=daily, days=days
            )
            if not result.series:
                economy_status.value = "该框架没有经济流"
                economy_box.controls = []
            else:
                economy_status.value = f"模拟 {days} 天"
                economy_box.controls = _render_economy(result)
        except Exception as exc:
            economy_status.value = f"模拟失败：{exc}"
            economy_box.controls = []
        page.update()

    pacing_daily = text_input("日均经验", "50000", width=180)
    pacing_status = ft.Text("", size=12, color=MUTED)
    pacing_box = ft.Column(spacing=4)

    def on_pacing(_e) -> None:
        if state.framework is None:
            pacing_status.value = "请先在工作台生成框架"
            page.update()
            return
        try:
            daily = float(pacing_daily.value.strip() or "50000")
            report = analyze_pacing(state.framework, daily)
            pacing_status.value = (
                f"满级 {report.total_days:.1f} 天"
                f"（新手 {report.early_days:.1f} / 中期 {report.mid_days:.1f}"
                f" / 后期 {report.late_days:.1f}）"
            )
            pacing_box.controls = _render_pacing(report)
        except Exception as exc:
            pacing_status.value = f"分析失败：{exc}"
            pacing_box.controls = []
        page.update()

    combat_mult = text_input("暴击倍率", "2.0", width=150)
    combat_var = text_input("伤害浮动(%)", "10", width=150)
    combat_trials = text_input("模拟次数", "1000", width=150)
    combat_status = ft.Text("", size=12, color=MUTED)
    combat_box = ft.Column(spacing=4)

    def on_combat_sim(_e) -> None:
        if state.framework is None:
            combat_status.value = "请先在工作台生成框架"
            page.update()
            return
        combat_status.value = "模拟中..."
        combat_box.controls = []
        page.update()

        def work() -> None:
            try:
                mult = float(combat_mult.value.strip() or "2")
                variance = float(combat_var.value.strip() or "10") / 100
                trials = int(combat_trials.value.strip() or "1000")
                points = simulate_combat_curve(
                    state.framework,
                    crit_mult=mult,
                    variance=variance,
                    trials=trials,
                )
                if not points:
                    combat_status.value = "该框架缺少 hp/atk，无法做战斗模拟"
                    combat_box.controls = []
                else:
                    combat_status.value = (
                        f"已模拟 {len(points)} 个等级"
                        f"（暴击 ×{mult:g}，浮动 ±{variance:.0%}）"
                    )
                    combat_box.controls = _render_combat(points)
            except Exception as exc:
                combat_status.value = f"模拟失败：{exc}"
                combat_box.controls = []
            page.update()

        page.run_thread(work)

    check_status = ft.Text("", size=12, color=MUTED)
    check_box = ft.Column(spacing=6)

    def on_full_check(_e) -> None:
        if state.framework is None:
            check_status.value = "请先在工作台生成框架"
            page.update()
            return
        check_status.value = "体检中..."
        check_box.controls = []
        page.update()

        def work() -> None:
            try:
                framework = state.framework
                daily = float(pacing_daily.value.strip() or "50000")
                blocks: list[ft.Control] = []

                def section(title: str, controls: list) -> None:
                    blocks.append(
                        ft.Text(
                            f"【{title}】",
                            size=13,
                            color=ACCENT,
                            weight=ft.FontWeight.W_600,
                        )
                    )
                    blocks.extend(controls)
                    blocks.append(ft.Divider(height=1, color=BORDER))

                report = analyze(framework)
                section("可行性", _render(report))

                pacing = analyze_pacing(framework, daily)
                section("成长节奏", _render_pacing(pacing))

                economy = simulate_economy(
                    framework, daily_exp=daily, days=30
                )
                section("经济 30 天", _render_economy(economy))

                invest = analyze_investment(framework)
                section("投放平衡", _render_investment(invest, framework))

                progression = analyze_progression(framework)
                section("进阶", _render_progression(progression))

                prof_target = int(prof_level.value.strip() or "60")
                professions = analyze_professions(framework, prof_target)
                section("职业对比", _render_professions(professions))

                base = int(pvp_base.value.strip() or "30")
                section("PVP 胜率", _render_pvp(pvp_curve(framework, base)))

                check_status.value = (
                    f"体检完成：{len(framework.attributes)} 属性 / "
                    f"{framework.level_cap} 级 / "
                    f"{len(report.warnings)} 条警告"
                )
                check_box.controls = blocks
            except Exception as exc:
                check_status.value = f"体检失败：{exc}"
                check_box.controls = []
            page.update()

        page.run_thread(work)

    return ft.Column(
        spacing=16,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Text("分析", size=20, weight=ft.FontWeight.W_600, color=FG),
            ft.Text("对当前数值框架做可行性验证与预测", size=12, color=MUTED),
            card(
                section_title("一键体检"),
                ft.Text(
                    "依次跑完可行性 / 节奏 / 经济 / 投放 / 进阶 / 职业 / PVP",
                    size=11,
                    color=MUTED,
                ),
                primary_button(
                    "开始体检", on_full_check, icon=ft.Icons.HEALTH_AND_SAFETY
                ),
                check_status,
                check_box,
            ),
            card(
                section_title("可行性分析"),
                ft.Row(
                    [daily_exp, primary_button("运行分析", on_run)],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                result,
            ),
            card(
                section_title("目标点拟合（反推曲线并写回框架）"),
                ft.Text("给几个目标点，自动反推曲线参数", size=11, color=MUTED),
                fit_points,
                ft.Row(
                    [fit_target, primary_button("拟合并应用", on_fit)],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                fit_status,
            ),
            card(
                section_title("成长节奏（升级耗时）"),
                ft.Text(
                    "按日均经验产出，算出每级耗时与节奏卡点",
                    size=11,
                    color=MUTED,
                ),
                ft.Row(
                    [pacing_daily, primary_button("分析节奏", on_pacing)],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                pacing_status,
                pacing_box,
            ),
            card(
                section_title("经济长期模拟"),
                ft.Text(
                    "按成长节奏推进等级，逐日累计货币余额",
                    size=11,
                    color=MUTED,
                ),
                ft.Row(
                    [economy_days, primary_button("运行模拟", on_economy)],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                economy_status,
                economy_box,
            ),
            card(
                section_title("投放规划（任务/活动）"),
                ft.Text(
                    "各等级段每日投放 vs 每日消耗，找出资金缺口",
                    size=11,
                    color=MUTED,
                ),
                primary_button("分析投放", on_invest),
                invest_status,
                invest_box,
            ),
            card(
                section_title("进阶（突破/转生/天赋）"),
                ft.Text(
                    "突破卡点、转生倍率、天赋加成",
                    size=11,
                    color=MUTED,
                ),
                primary_button("分析进阶", on_progression),
                prog_status,
                prog_box,
            ),
            card(
                section_title("抽卡模拟（蒙特卡洛）"),
                ft.Row(
                    [gacha_prob, gacha_pity, gacha_trials],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Row(
                    [gacha_soft, gacha_step, gacha_win, gacha_guarantee],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                primary_button("运行模拟", on_simulate),
                gacha_status,
            ),
            card(
                section_title("战斗模拟（蒙特卡洛）"),
                ft.Text(
                    "带暴击与伤害浮动，对比解析 TTK 的真实差异",
                    size=11,
                    color=MUTED,
                ),
                ft.Row(
                    [combat_mult, combat_var, combat_trials],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                primary_button("运行战斗模拟", on_combat_sim),
                combat_status,
                combat_box,
            ),
            card(
                section_title("职业横向对比"),
                ft.Text(
                    "同等级下各职业战力与对战胜率，看谁压制谁",
                    size=11,
                    color=MUTED,
                ),
                ft.Row(
                    [prof_level, primary_button("对比职业", on_professions)],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                prof_status,
                prof_box,
            ),
            card(
                section_title("PVP 胜率（战力比）"),
                ft.Text(
                    "按战力比估算胜率，判断匹配区间该放多宽",
                    size=11,
                    color=MUTED,
                ),
                ft.Row(
                    [pvp_base, primary_button("计算胜率", on_pvp)],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                pvp_status,
                pvp_box,
            ),
            card(
                section_title("方案对比"),
                ft.Text(
                    "对比已保存方案的战力 / TTK / 装备 / 经济，找出更好的那套",
                    size=11,
                    color=MUTED,
                ),
                primary_button("对比全部方案", on_compare),
                compare_status,
                compare_box,
            ),
        ],
    )


def _render_professions(report) -> list[ft.Control]:
    """职业对比：战力列表 + 对战矩阵。"""
    controls: list[ft.Control] = []
    for item in report.powers:
        controls.append(
            ft.Text(
                f"{item.name}：战力 {item.power:,.0f}", size=12, color=FG
            )
        )

    names = [item.name for item in report.powers]
    controls.append(ft.Divider(height=1, color=BORDER))
    controls.append(
        ft.Row(
            [ft.Text("攻 \\ 守", size=11, color=MUTED, width=70)]
            + [
                ft.Text(name, size=11, color=MUTED, width=90)
                for name in names
            ],
            spacing=8,
        )
    )
    for attacker in names:
        row: list[ft.Control] = [
            ft.Text(attacker, size=11, color=FG, width=70)
        ]
        for defender in names:
            if attacker == defender:
                row.append(ft.Text("—", size=11, color=MUTED, width=90))
                continue
            rate = next(
                item.win_rate
                for item in report.duels
                if item.attacker == attacker and item.defender == defender
            )
            row.append(
                ft.Text(
                    f"{rate:.0%}",
                    size=11,
                    color=(
                        WARNING if rate > 0.6 or rate < 0.4 else ACCENT
                    ),
                    width=90,
                )
            )
        controls.append(ft.Row(row, spacing=8))

    for warning in report.warnings:
        controls.append(ft.Text(f"⚠ {warning}", size=12, color=WARNING))
    return controls


def _render_progression(report) -> list[ft.Control]:
    """进阶结果：突破节点 / 天赋加成 / 转生倍率。"""
    controls: list[ft.Control] = []

    if report.breakthroughs:
        for line in report.breakthroughs:
            controls.append(ft.Text(f"• {line}", size=12, color=FG))
        if report.breakthrough_cost:
            total = "，".join(
                f"{resource} {amount:,.0f}"
                for resource, amount in report.breakthrough_cost.items()
            )
            controls.append(ft.Text(f"突破总消耗：{total}", size=12, color=MUTED))
    else:
        controls.append(ft.Text("未配置突破节点", size=12, color=MUTED))

    if report.talent_bonus:
        controls.append(
            ft.Text(
                f"天赋：满级 {report.talent_points_at_cap:.0f} 点，"
                f"加成 {report.talent_bonus:.0%}",
                size=12,
                color=ACCENT,
            )
        )
    else:
        controls.append(ft.Text("未开启天赋", size=12, color=MUTED))

    if report.rebirth_enabled:
        curve = "，".join(
            f"{index} 次 ×{multiplier:.2f}"
            for index, multiplier in enumerate(report.rebirth_multipliers)
        )
        controls.append(ft.Text(f"转生倍率：{curve}", size=12, color=MUTED))
    else:
        controls.append(ft.Text("未开启转生", size=12, color=MUTED))

    for warning in report.warnings:
        controls.append(ft.Text(f"⚠ {warning}", size=12, color=WARNING))
    return controls


def _render_investment(report, framework) -> list[ft.Control]:
    """投放平衡表：每等级段一行（投放/消耗/净），缺口标红。"""
    main = (
        framework.economy.flows[0].resource if framework.economy.flows else ""
    )
    controls: list[ft.Control] = []
    for band in report.bands:
        income = band.daily_income.get(main, 0.0)
        cost = band.daily_cost.get(main, 0.0)
        net = band.net.get(main, 0.0)
        controls.append(
            ft.Text(
                f"{band.band} 级段：投放 {income:,.0f}"
                f" / 消耗 {cost:,.0f} / 净 {net:+,.0f}",
                size=12,
                color=WARNING if net < 0 else FG,
            )
        )
    for warning in report.warnings:
        controls.append(ft.Text(f"⚠ {warning}", size=12, color=WARNING))
    return controls


def _render_economy(result) -> list[ft.Control]:
    """经济长期模拟结果：每资源一行摘要 + 警告。"""
    controls: list[ft.Control] = []
    for series in result.series:
        line = (
            f"{series.resource}：最终 {series.final_balance:,.0f}"
            f" | 峰值第 {series.peak_day} 天（{series.peak_balance:,.0f}）"
        )
        if series.negative_day:
            line += f" | 第 {series.negative_day} 天转负"
        controls.append(ft.Text(line, size=12, color=FG))
    for warning in result.warnings:
        controls.append(ft.Text(f"⚠ {warning}", size=12, color=WARNING))
    return controls


def _render_pvp(rows) -> list[ft.Control]:
    """PVP 胜率表：等级差 / 双方战力 / 胜率。"""
    controls: list[ft.Control] = [
        ft.Row(
            [
                ft.Text("等级差", size=11, color=MUTED, width=80),
                ft.Text("攻方战力", size=11, color=MUTED, width=130),
                ft.Text("守方战力", size=11, color=MUTED, width=130),
                ft.Text("胜率", size=11, color=MUTED, width=80),
            ],
            spacing=8,
        )
    ]
    for delta, _level, result in rows:
        controls.append(
            ft.Row(
                [
                    ft.Text(f"+{delta}" if delta else "0", size=11, color=FG, width=80),
                    ft.Text(
                        f"{result.attacker_power:,.0f}",
                        size=11,
                        color=MUTED,
                        width=130,
                    ),
                    ft.Text(
                        f"{result.defender_power:,.0f}",
                        size=11,
                        color=MUTED,
                        width=130,
                    ),
                    ft.Text(
                        f"{result.win_rate:.0%}",
                        size=11,
                        color=WARNING if result.win_rate > 0.65 else ACCENT,
                        width=80,
                    ),
                ],
                spacing=8,
            )
        )
    return controls


def _render_compare(result) -> list[ft.Control]:
    """方案对比表：首列指标，其后每列一个方案。"""
    if not result.names:
        return []
    controls: list[ft.Control] = [
        ft.Row(
            [ft.Text("指标", size=11, color=MUTED, width=90)]
            + [
                ft.Text(name, size=11, color=ACCENT, width=180)
                for name in result.names
            ],
            spacing=8,
        )
    ]
    for row in result.rows:
        controls.append(
            ft.Row(
                [ft.Text(row.label, size=11, color=FG, width=90)]
                + [
                    ft.Text(value, size=11, color=MUTED, width=180)
                    for value in row.values
                ],
                spacing=8,
            )
        )
    return controls


def _render_pacing(report) -> list[ft.Control]:
    """成长节奏：卡点提示 + 阶段汇总 + 抽样进度表。"""
    controls: list[ft.Control] = []

    if report.spikes:
        for spike in report.spikes[:5]:
            controls.append(
                ft.Text(
                    f"⚠ {spike.level} 级需 {spike.days:.1f} 天"
                    f"（前一级 {spike.prev_days:.1f}，{spike.ratio}x）",
                    size=12,
                    color=WARNING,
                )
            )
    else:
        controls.append(ft.Text("节奏平滑，无明显卡点", size=12, color=MUTED))

    points = report.points
    if not points:
        return controls
    step = max(1, len(points) // 8)
    selected = list(points[::step])
    if selected[-1] is not points[-1]:
        selected.append(points[-1])

    controls.append(
        ft.Row(
            [
                ft.Text("等级", size=11, color=MUTED, width=55),
                ft.Text("本级天数", size=11, color=MUTED, width=80),
                ft.Text("累计天数", size=11, color=MUTED, width=80),
            ],
            spacing=8,
        )
    )
    for point in selected:
        controls.append(
            ft.Row(
                [
                    ft.Text(str(point.level), size=11, color=FG, width=55),
                    ft.Text(f"{point.days:.2f}", size=11, color=MUTED, width=80),
                    ft.Text(f"{point.cumulative_days:.1f}", size=11, color=ACCENT, width=80),
                ],
                spacing=8,
            )
        )
    return controls


def _render_combat(points) -> list[ft.Control]:
    """战斗模拟结果：抽样展示（避免长表刷屏）+ 汇总 + 波动警告。"""
    if len(points) <= 12:
        selected = list(points)
    else:
        step = max(1, len(points) // 10)
        selected = list(points[::step])
        if selected[-1] is not points[-1]:
            selected.append(points[-1])

    controls: list[ft.Control] = [
        ft.Row(
            [
                ft.Text("等级", size=11, color=MUTED, width=50),
                ft.Text("解析", size=11, color=MUTED, width=70),
                ft.Text("模拟均值", size=11, color=MUTED, width=80),
                ft.Text("P90", size=11, color=MUTED, width=55),
                ft.Text("波动", size=11, color=MUTED, width=55),
            ],
            spacing=8,
        )
    ]
    for point in selected:
        controls.append(
            ft.Row(
                [
                    ft.Text(str(point.level), size=11, color=FG, width=50),
                    ft.Text(f"{point.analytic_hits:.1f}", size=11, color=MUTED, width=70),
                    ft.Text(f"{point.sim_mean:.1f}", size=11, color=ACCENT, width=80),
                    ft.Text(str(point.sim_p90), size=11, color=MUTED, width=55),
                    ft.Text(
                        f"{point.volatility:.0%}",
                        size=11,
                        color=WARNING if point.volatility > 0.3 else MUTED,
                        width=55,
                    ),
                ],
                spacing=8,
            )
        )

    last = points[-1]
    delta = (last.sim_mean / last.analytic_hits - 1) * 100 if last.analytic_hits else 0
    controls.append(ft.Divider(height=1, color=BORDER))
    controls.append(
        ft.Text(
            f"满级：解析 {last.analytic_hits:.1f} 次 → 模拟 {last.sim_mean:.1f} 次"
            f"（{delta:+.1f}%）",
            size=12,
            color=FG,
        )
    )

    worst = max(points, key=lambda p: p.volatility)
    if worst.volatility > 0.3:
        controls.append(
            ft.Text(
                f"⚠ 第 {worst.level} 级波动率 {worst.volatility:.0%}，"
                f"战斗运气成分偏重（P10 {worst.sim_p10} / P90 {worst.sim_p90}）",
                size=12,
                color=WARNING,
            )
        )
    return controls


def _warn_text(warnings: list[str]) -> str:
    return "".join(f"\n  ⚠ {warning}" for warning in warnings)


def _render(report) -> list[ft.Control]:
    controls: list[ft.Control] = [
        ft.Text(
            f"{report.title}｜{report.level_cap} 级｜总经验 {report.total_exp:,}",
            size=14,
            weight=ft.FontWeight.W_600,
            color=FG,
        )
    ]
    if report.days_to_max:
        controls.append(ft.Text(f"预计满级：{report.days_to_max} 天", size=12, color=FG))

    for growth in report.growths:
        controls.append(
            ft.Text(
                f"{growth.name}: {growth.first} → {growth.last}"
                f"（{growth.ratio}x，单级最大 {growth.max_step_ratio}x）",
                size=12,
                color=MUTED,
            )
        )
    if report.combat:
        controls.append(
            ft.Text(
                f"TTK: 1级 {report.combat[0].ttk}s → {report.level_cap}级 {report.combat[-1].ttk}s",
                size=12,
                color=MUTED,
            )
        )
    if report.power_curve:
        first = report.power_curve[0].power
        last = report.power_curve[-1].power
        ratio = last / first if first else 0
        controls.append(
            ft.Text(
                f"战力：1级 {first:,.0f} → {report.level_cap}级 {last:,.0f}"
                f"（{ratio:.1f}x）",
                size=12,
                color=MUTED,
            )
        )
    if report.equip_share_full:
        controls.append(
            ft.Text(
                f"装备战力：普通 +{report.equip_share_common:.0%}"
                f" → 满配 +{report.equip_share_full:.0%}",
                size=12,
                color=MUTED,
            )
        )
    if report.affix_share_expected:
        controls.append(
            ft.Text(
                f"词条贡献：最差 +{report.affix_share_worst:.0%}"
                f" ~ 期望 +{report.affix_share_expected:.0%}"
                f"（波动 {report.affix_share_expected - report.affix_share_worst:.0%}）",
                size=12,
                color=MUTED,
            )
        )
    if report.warnings:
        controls.extend(ft.Text(f"⚠ {w}", size=12, color=WARNING) for w in report.warnings)
    else:
        controls.append(ft.Text("无可行性问题", size=12, color=MUTED))
    return controls
