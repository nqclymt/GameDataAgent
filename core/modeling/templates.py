"""内置游戏类型数值模板（9 种）。

每种类型包含：属性成长、经验曲线、战斗公式、量化经济流、掉落表。
"""

from core.modeling.framework import (
    Attribute,
    CombatFormula,
    DropEntry,
    DropTable,
    Economy,
    GrowthCurve,
    ResourceFlow,
    ValueFramework,
)


def build_rpg_framework(
    title: str,
    level_cap: int = 60,
    theme: str = "东方玄幻",
) -> ValueFramework:
    """RPG：指数成长、防御减伤、任务/掉落驱动经济。"""
    return ValueFramework(
        game_type="rpg",
        title=title,
        level_cap=level_cap,
        attributes=[
            Attribute(key="hp", name="生命", base=100, growth=1.12, growth_type="exponential"),
            Attribute(key="atk", name="攻击", base=10, growth=1.10, growth_type="exponential"),
            Attribute(key="defense", name="防御", base=5, growth=1.08, growth_type="exponential"),
            Attribute(key="crit", name="暴击率", base=0.05, growth=0.001, growth_type="linear"),
            Attribute(key="speed", name="速度", base=100, growth=1.01, growth_type="linear"),
        ],
        exp_curve=GrowthCurve(
            name="等级经验曲线",
            formula="base * level^exponent",
            params={"base": 100.0, "exponent": 1.5},
        ),
        combat=CombatFormula(
            name="伤害公式",
            expression="atk * skill_ratio * (1 - defense / (defense + 1000))",
            description="防御采用收益递减减伤，避免高防无敌",
        ),
        economy=Economy(
            currencies=["金币", "钻石"],
            sources=["任务奖励", "怪物掉落", "日常活动"],
            sinks=["装备强化", "商店购买", "技能升级"],
            flows=[
                ResourceFlow(resource="金币", income_per_hour=1200, cost_per_hour=900),
                ResourceFlow(resource="钻石", income_per_hour=5, cost_per_hour=8),
            ],
        ),
        drop_tables=[
            DropTable(
                name="普通怪物",
                entries=[
                    DropEntry(item="金币", probability=1.0, min_count=20, max_count=50),
                    DropEntry(item="装备", probability=0.08),
                    DropEntry(item="材料", probability=0.35, min_count=1, max_count=3),
                ],
            ),
            DropTable(
                name="精英怪物",
                entries=[
                    DropEntry(item="金币", probability=1.0, min_count=100, max_count=200),
                    DropEntry(item="稀有装备", probability=0.25),
                    DropEntry(item="稀有材料", probability=0.10),
                ],
            ),
        ],
        notes=[f"题材：{theme}", f"等级上限：{level_cap}"],
    )


def build_mmorpg_framework(
    title: str,
    level_cap: int = 80,
    theme: str = "多人玄幻",
) -> ValueFramework:
    """MMORPG：更长养成线、经济双轨（金币+钻石）、副本/团本掉落。"""
    return ValueFramework(
        game_type="mmorpg",
        title=title,
        level_cap=level_cap,
        attributes=[
            Attribute(key="hp", name="生命", base=150, growth=1.10, growth_type="exponential"),
            Attribute(key="atk", name="攻击", base=15, growth=1.09, growth_type="exponential"),
            Attribute(key="defense", name="防御", base=8, growth=1.08, growth_type="exponential"),
            Attribute(key="crit", name="暴击率", base=0.05, growth=0.0008, growth_type="linear"),
            Attribute(key="speed", name="速度", base=100, growth=1.008, growth_type="linear"),
        ],
        exp_curve=GrowthCurve(
            name="等级经验曲线",
            formula="base * level^exponent",
            params={"base": 120.0, "exponent": 1.6},
        ),
        combat=CombatFormula(
            name="伤害公式",
            expression="atk * skill_ratio * (1 - defense / (defense + 1200))",
            description="MMO 常用减伤系数，配合团本血量设计",
        ),
        economy=Economy(
            currencies=["金币", "钻石", "荣誉"],
            sources=["任务", "副本", "团本", "拍卖行"],
            sinks=["装备强化", "宝石镶嵌", "坐骑培养", "修理"],
            flows=[
                ResourceFlow(resource="金币", income_per_hour=2000, cost_per_hour=1700),
                ResourceFlow(resource="钻石", income_per_hour=8, cost_per_hour=12),
                ResourceFlow(resource="荣誉", income_per_hour=120, cost_per_hour=100),
            ],
        ),
        drop_tables=[
            DropTable(
                name="五人副本",
                entries=[
                    DropEntry(item="金币", probability=1.0, min_count=500, max_count=800),
                    DropEntry(item="蓝装", probability=0.35),
                    DropEntry(item="紫装", probability=0.08),
                ],
            ),
            DropTable(
                name="团队副本",
                entries=[
                    DropEntry(item="金币", probability=1.0, min_count=2000, max_count=3000),
                    DropEntry(item="紫装", probability=0.30),
                    DropEntry(item="橙装", probability=0.05),
                ],
            ),
        ],
        notes=[f"题材：{theme}", f"等级上限：{level_cap}", "MMO：长养成 + 双轨经济"],
    )


def build_card_framework(
    title: str,
    level_cap: int = 60,
    theme: str = "卡牌对战",
) -> ValueFramework:
    """卡牌：线性成长、小数值区间、碎片驱动养成。"""
    return ValueFramework(
        game_type="card",
        title=title,
        level_cap=level_cap,
        attributes=[
            Attribute(key="atk", name="攻击", base=30, growth=4.5, growth_type="linear"),
            Attribute(key="hp", name="生命", base=300, growth=55, growth_type="linear"),
            Attribute(key="defense", name="防御", base=10, growth=2.0, growth_type="linear"),
            Attribute(key="speed", name="速度", base=80, growth=1.2, growth_type="linear"),
        ],
        exp_curve=GrowthCurve(
            name="卡牌升级经验",
            formula="base * level^exponent",
            params={"base": 80.0, "exponent": 1.8},
        ),
        combat=CombatFormula(
            name="结算伤害",
            expression="atk * (1 - defense / (defense + 300))",
            description="卡牌对战常用减伤系数，数值区间更小",
        ),
        economy=Economy(
            currencies=["金币", "钻石", "卡牌碎片"],
            sources=["副本掉落", "每日任务", "竞技场奖励"],
            sinks=["卡牌升级", "升星", "装备强化"],
            flows=[
                ResourceFlow(resource="金币", income_per_hour=800, cost_per_hour=600),
                ResourceFlow(resource="卡牌碎片", income_per_hour=50, cost_per_hour=60),
            ],
        ),
        drop_tables=[
            DropTable(
                name="经验副本",
                entries=[
                    DropEntry(item="金币", probability=1.0, min_count=80, max_count=120),
                    DropEntry(item="卡牌碎片", probability=0.6, min_count=1, max_count=5),
                ],
            ),
            DropTable(
                name="抽卡",
                entries=[
                    DropEntry(item="R 卡", probability=0.70),
                    DropEntry(item="SR 卡", probability=0.25),
                    DropEntry(item="SSR 卡", probability=0.05),
                ],
            ),
        ],
        notes=[f"题材：{theme}", f"等级上限：{level_cap}", "卡牌：线性成长 + 品质倍率"],
    )


def build_idle_framework(
    title: str,
    level_cap: int = 200,
    theme: str = "放置",
) -> ValueFramework:
    """放置：指数膨胀、等级上限更高、离线收益驱动。"""
    return ValueFramework(
        game_type="idle",
        title=title,
        level_cap=level_cap,
        attributes=[
            Attribute(key="dps", name="秒伤", base=10, growth=1.15, growth_type="exponential"),
            Attribute(key="hp", name="生命", base=100, growth=1.15, growth_type="exponential"),
            Attribute(key="defense", name="防御", base=5, growth=1.12, growth_type="exponential"),
            Attribute(key="gold_rate", name="金币收益", base=1, growth=1.12, growth_type="exponential"),
        ],
        exp_curve=GrowthCurve(
            name="关卡经验",
            formula="base * level^exponent",
            params={"base": 50.0, "exponent": 2.2},
        ),
        combat=CombatFormula(
            name="闯关伤害",
            expression="dps * (1 - defense / (defense + 500))",
            description="放置类以 DPS 推图为主",
        ),
        economy=Economy(
            currencies=["金币", "钻石", "离线收益"],
            sources=["挂机产出", "离线奖励", "宝箱"],
            sinks=["升级", "转生", "装备"],
            flows=[
                ResourceFlow(resource="金币", income_per_hour=5000, cost_per_hour=4000),
                ResourceFlow(resource="钻石", income_per_hour=12, cost_per_hour=15),
            ],
        ),
        drop_tables=[
            DropTable(
                name="挂机宝箱",
                entries=[
                    DropEntry(item="金币", probability=1.0, min_count=200, max_count=500),
                    DropEntry(item="装备", probability=0.05),
                    DropEntry(item="转生石", probability=0.01),
                ],
            ),
        ],
        notes=[f"题材：{theme}", f"等级上限：{level_cap}", "放置：指数膨胀 + 离线收益"],
    )


def build_slg_framework(
    title: str,
    level_cap: int = 30,
    theme: str = "策略",
) -> ValueFramework:
    """SLG：资源产出驱动、建筑等级、部队攻防。"""
    return ValueFramework(
        game_type="slg",
        title=title,
        level_cap=level_cap,
        attributes=[
            Attribute(key="hp", name="部队生命", base=100, growth=1.10, growth_type="exponential"),
            Attribute(key="atk", name="部队攻击", base=10, growth=1.10, growth_type="exponential"),
            Attribute(key="defense", name="部队防御", base=5, growth=1.08, growth_type="exponential"),
            Attribute(key="wood_rate", name="木材产出", base=100, growth=1.12, growth_type="exponential"),
            Attribute(key="food_rate", name="粮食产出", base=120, growth=1.12, growth_type="exponential"),
            Attribute(key="stone_rate", name="石料产出", base=80, growth=1.12, growth_type="exponential"),
        ],
        exp_curve=GrowthCurve(
            name="建筑升级耗时（秒）",
            formula="base * level^exponent",
            params={"base": 60.0, "exponent": 1.8},
        ),
        combat=CombatFormula(
            name="部队对战伤害",
            expression="atk * (1 - defense / (defense + 400))",
            description="SLG 部队对战，防御收益递减",
        ),
        economy=Economy(
            currencies=["木材", "粮食", "石料", "金币"],
            sources=["资源建筑产出", "采集", "任务"],
            sinks=["建筑升级", "部队训练", "科技研究"],
            flows=[
                ResourceFlow(resource="木材", income_per_hour=2000, cost_per_hour=1800),
                ResourceFlow(resource="粮食", income_per_hour=2500, cost_per_hour=2200),
                ResourceFlow(resource="石料", income_per_hour=1500, cost_per_hour=1400),
            ],
        ),
        drop_tables=[
            DropTable(
                name="野外采集",
                entries=[
                    DropEntry(item="木材", probability=1.0, min_count=50, max_count=150),
                    DropEntry(item="石料", probability=0.8, min_count=30, max_count=100),
                ],
            ),
            DropTable(
                name="攻打据点",
                entries=[
                    DropEntry(item="金币", probability=1.0, min_count=500, max_count=1000),
                    DropEntry(item="加速道具", probability=0.3),
                ],
            ),
        ],
        notes=[f"题材：{theme}", f"建筑等级上限：{level_cap}", "SLG：资源产出驱动"],
    )


def build_tower_framework(
    title: str,
    level_cap: int = 50,
    theme: str = "塔防",
) -> ValueFramework:
    """塔防：塔的 DPS 对抗敌人生命，波次推进。"""
    return ValueFramework(
        game_type="tower",
        title=title,
        level_cap=level_cap,
        attributes=[
            Attribute(key="hp", name="敌人生命", base=100, growth=1.18, growth_type="exponential"),
            Attribute(key="atk", name="塔攻击", base=20, growth=1.15, growth_type="exponential"),
            Attribute(key="speed", name="攻击速度", base=1.0, growth=0.02, growth_type="linear"),
            Attribute(key="range", name="射程", base=3.0, growth=0.05, growth_type="linear"),
        ],
        exp_curve=GrowthCurve(
            name="波次经验",
            formula="base * level^exponent",
            params={"base": 40.0, "exponent": 1.4},
        ),
        combat=CombatFormula(
            name="塔输出",
            expression="atk * speed",
            description="塔的持续输出；敌人生命增长快于塔攻击，后期需要升级",
        ),
        economy=Economy(
            currencies=["金币", "星核"],
            sources=["击杀奖励", "波次结算", "成就"],
            sinks=["建塔", "升级塔", "解锁新塔"],
            flows=[
                ResourceFlow(resource="金币", income_per_hour=600, cost_per_hour=520),
                ResourceFlow(resource="星核", income_per_hour=3, cost_per_hour=5),
            ],
        ),
        drop_tables=[
            DropTable(
                name="波次结算",
                entries=[
                    DropEntry(item="金币", probability=1.0, min_count=30, max_count=80),
                    DropEntry(item="星核", probability=0.15),
                ],
            ),
        ],
        notes=[f"题材：{theme}", f"波次上限：{level_cap}", "塔防：DPS 对抗敌人生命"],
    )


def build_shooter_framework(
    title: str,
    level_cap: int = 50,
    theme: str = "战术射击",
) -> ValueFramework:
    """射击：数值区间压缩、护甲固定、对局奖励驱动。"""
    return ValueFramework(
        game_type="shooter",
        title=title,
        level_cap=level_cap,
        attributes=[
            Attribute(key="hp", name="生命", base=100, growth=1.04, growth_type="exponential"),
            Attribute(key="atk", name="武器伤害", base=25, growth=1.07, growth_type="exponential"),
            Attribute(key="defense", name="护甲", base=20, growth=1.03, growth_type="exponential"),
            Attribute(key="speed", name="移动速度", base=5.0, growth=1.01, growth_type="linear"),
        ],
        exp_curve=GrowthCurve(
            name="军衔经验",
            formula="base * level^exponent",
            params={"base": 500.0, "exponent": 1.6},
        ),
        combat=CombatFormula(
            name="射击伤害",
            expression="atk * (1 - defense / (defense + 100))",
            description="护甲减伤，数值区间刻意压缩以保持手感稳定",
        ),
        economy=Economy(
            currencies=["金币", "军功"],
            sources=["对局奖励", "任务", "赛季奖励"],
            sinks=["解锁武器", "改装配件", "皮肤"],
            flows=[
                ResourceFlow(resource="金币", income_per_hour=400, cost_per_hour=350),
                ResourceFlow(resource="军功", income_per_hour=80, cost_per_hour=70),
            ],
        ),
        drop_tables=[
            DropTable(
                name="对局结算",
                entries=[
                    DropEntry(item="金币", probability=1.0, min_count=50, max_count=120),
                    DropEntry(item="军功", probability=1.0, min_count=10, max_count=30),
                    DropEntry(item="皮肤碎片", probability=0.03),
                ],
            ),
        ],
        notes=[f"题材：{theme}", f"军衔上限：{level_cap}", "射击：数值压缩 + 手感优先"],
    )


def build_moba_framework(
    title: str,
    level_cap: int = 18,
    theme: str = "MOBA",
) -> ValueFramework:
    """MOBA：短周期单局成长（1~18 级），英雄数值克制关系。"""
    return ValueFramework(
        game_type="moba",
        title=title,
        level_cap=level_cap,
        attributes=[
            Attribute(key="hp", name="生命", base=600, growth=1.12, growth_type="exponential"),
            Attribute(key="atk", name="攻击", base=60, growth=1.10, growth_type="exponential"),
            Attribute(key="defense", name="护甲", base=20, growth=1.08, growth_type="exponential"),
            Attribute(key="speed", name="移速", base=350, growth=1.005, growth_type="linear"),
        ],
        exp_curve=GrowthCurve(
            name="单局升级经验",
            formula="base * level^exponent",
            params={"base": 280.0, "exponent": 1.5},
        ),
        combat=CombatFormula(
            name="技能伤害",
            expression="atk * (1 - defense / (defense + 100))",
            description="单局内 1~18 级成长，后期靠装备补足",
        ),
        economy=Economy(
            currencies=["金币", "点券", "英雄碎片"],
            sources=["对局奖励", "每日首胜", "赛季奖励"],
            sinks=["购买英雄", "皮肤", "符文"],
            flows=[
                ResourceFlow(resource="金币", income_per_hour=1000, cost_per_hour=800),
                ResourceFlow(resource="英雄碎片", income_per_hour=20, cost_per_hour=25),
            ],
        ),
        drop_tables=[
            DropTable(
                name="对局奖励",
                entries=[
                    DropEntry(item="金币", probability=1.0, min_count=80, max_count=150),
                    DropEntry(item="英雄碎片", probability=0.10, min_count=1, max_count=2),
                ],
            ),
        ],
        notes=[f"题材：{theme}", f"单局等级上限：{level_cap}", "MOBA：短周期成长"],
    )


def build_sim_framework(
    title: str,
    level_cap: int = 30,
    theme: str = "模拟经营",
) -> ValueFramework:
    """模拟经营：无战斗，收益/客流/声望驱动，等级=店铺等级。"""
    return ValueFramework(
        game_type="sim",
        title=title,
        level_cap=level_cap,
        attributes=[
            Attribute(key="income", name="金币收益", base=100, growth=1.15, growth_type="exponential"),
            Attribute(key="customer_rate", name="客流量", base=10, growth=1.10, growth_type="exponential"),
            Attribute(key="reputation", name="声望", base=0, growth=5, growth_type="linear"),
            Attribute(key="build_speed", name="建造速度", base=1.0, growth=0.03, growth_type="linear"),
        ],
        exp_curve=GrowthCurve(
            name="店铺升级经验",
            formula="base * level^exponent",
            params={"base": 200.0, "exponent": 1.7},
        ),
        combat=CombatFormula(
            name="无战斗",
            expression="income",
            description="模拟经营没有战斗，公式位保留用于收益计算",
        ),
        economy=Economy(
            currencies=["金币", "声望"],
            sources=["顾客消费", "任务奖励", "连锁分红"],
            sinks=["店铺扩建", "员工雇佣", "装修升级"],
            flows=[
                ResourceFlow(resource="金币", income_per_hour=3000, cost_per_hour=2500),
                ResourceFlow(resource="声望", income_per_hour=60, cost_per_hour=45),
            ],
        ),
        drop_tables=[
            DropTable(
                name="顾客消费",
                entries=[
                    DropEntry(item="金币", probability=1.0, min_count=20, max_count=60),
                    DropEntry(item="声望", probability=0.2, min_count=1, max_count=3),
                ],
            ),
        ],
        notes=[f"题材：{theme}", f"店铺等级上限：{level_cap}", "模拟经营：收益/客流驱动"],
    )


TEMPLATES = {
    "rpg": build_rpg_framework,
    "mmorpg": build_mmorpg_framework,
    "card": build_card_framework,
    "idle": build_idle_framework,
    "slg": build_slg_framework,
    "tower": build_tower_framework,
    "shooter": build_shooter_framework,
    "moba": build_moba_framework,
    "sim": build_sim_framework,
}


def get_template(game_type: str):
    """按类型取模板，未匹配时回退 RPG。"""
    return TEMPLATES.get(game_type, build_rpg_framework)
