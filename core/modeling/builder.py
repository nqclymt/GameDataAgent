"""数值框架构建器：LLM 生成与模板降级双模式。"""

import json

from core.modeling.framework import (
    Affix,
    Breakthrough,
    EquipQuality,
    EquipSlot,
    EquipSet,
    GachaRule,
    InvestmentPlan,
    LevelBandPlan,
    Profession,
    SetEffect,
    SourceTicket,
    Talent,
    ValueFramework,
)
from core.modeling.templates import get_template
from llm.client import LLMClient

_GAME_TYPE_LABELS = {
    "rpg": "RPG",
    "mmorpg": "MMORPG",
    "card": "卡牌",
    "idle": "放置",
    "slg": "SLG",
    "tower": "塔防",
    "shooter": "射击",
    "moba": "MOBA",
    "sim": "模拟经营",
}

# 各类型装备部位规格：(key, 名称, 加成属性, 加成比例)
_EQUIP_SLOTS: dict[str, list[tuple[str, str, str, float]]] = {
    "rpg": [
        ("weapon", "武器", "atk", 0.60),
        ("armor", "护甲", "defense", 0.50),
        ("helmet", "头盔", "hp", 0.25),
        ("ring", "戒指", "crit", 0.30),
        ("boots", "鞋子", "speed", 0.15),
    ],
    "mmorpg": [
        ("weapon", "武器", "atk", 0.65),
        ("armor", "胸甲", "defense", 0.55),
        ("helmet", "头盔", "hp", 0.30),
        ("ring", "饰品", "crit", 0.35),
        ("boots", "战靴", "speed", 0.18),
    ],
    "card": [
        ("weapon", "武器卡", "atk", 0.50),
        ("armor", "护甲卡", "hp", 0.40),
        ("accessory", "饰品卡", "defense", 0.30),
    ],
    "idle": [
        ("weapon", "主武器", "dps", 0.60),
        ("armor", "护甲", "hp", 0.50),
        ("ring", "收益戒指", "gold_rate", 0.30),
    ],
    "slg": [
        ("weapon", "兵器", "atk", 0.50),
        ("armor", "甲胄", "defense", 0.40),
        ("tool", "伐木工具", "wood_rate", 0.30),
        ("farm", "农耕器具", "food_rate", 0.30),
    ],
    "tower": [
        ("turret", "炮塔核心", "atk", 0.50),
        ("ammo", "弹药", "speed", 0.25),
        ("scope", "瞄准镜", "range", 0.20),
    ],
    "shooter": [
        ("gun", "枪械", "atk", 0.50),
        ("vest", "防弹衣", "defense", 0.40),
        ("helmet", "头盔", "hp", 0.20),
    ],
    "moba": [
        ("weapon", "武器", "atk", 0.50),
        ("armor", "护甲", "defense", 0.40),
        ("boots", "鞋子", "speed", 0.15),
    ],
    "sim": [
        ("equipment", "经营设备", "income", 0.40),
        ("decor", "装修", "reputation", 0.30),
        ("staff", "员工配置", "customer_rate", 0.25),
    ],
}


def build_framework(
    title: str,
    level_cap: int = 60,
    theme: str = "东方玄幻",
    game_type: str = "rpg",
    llm: LLMClient | None = None,
) -> ValueFramework:
    """构建数值框架；未提供 LLM 客户端时走对应类型的内置模板。"""
    if llm is None:
        framework = get_template(game_type)(title, level_cap, theme)
    else:
        data = llm.complete_json(
            _system_prompt(game_type),
            _user_prompt(title, level_cap, theme, game_type),
        )
        framework = ValueFramework.model_validate(data)
    _ensure_equipment(framework, game_type)
    _ensure_gacha(framework, game_type)
    _ensure_investment(framework)
    _ensure_progression(framework, game_type)
    _ensure_professions(framework, game_type)
    return framework


# 有职业区分的类型
_PROFESSION_TYPES = {"rpg", "mmorpg"}


def _ensure_professions(framework: ValueFramework, game_type: str) -> None:
    """RPG/MMORPG 默认注入战士 / 法师 / 游侠三职业。"""
    if framework.professions or game_type not in _PROFESSION_TYPES:
        return
    framework.professions = [
        Profession(
            name="战士",
            stat_scale={"hp": 1.25, "defense": 1.30, "atk": 0.85, "speed": 0.90},
        ),
        Profession(
            name="法师",
            stat_scale={"hp": 0.78, "defense": 0.85, "atk": 1.30, "crit": 1.35},
        ),
        Profession(
            name="游侠",
            stat_scale={"hp": 0.90, "atk": 1.10, "speed": 1.30, "crit": 1.15},
        ),
    ]


# 有突破与天赋玩法的类型
_PROGRESSION_TYPES = {"rpg", "mmorpg"}


def _ensure_progression(framework: ValueFramework, game_type: str) -> None:
    """RPG/MMORPG 默认每 20 级一个突破点，并开启天赋。"""
    if (
        framework.progression.breakthroughs
        or game_type not in _PROGRESSION_TYPES
        or framework.level_cap < 21
    ):
        return
    main = (
        framework.economy.flows[0].resource
        if framework.economy.flows
        else "金币"
    )
    framework.progression.breakthroughs = [
        Breakthrough(
            level=level,
            cost_resource=main,
            cost_amount=100000.0 * (level // 20),
            unlock_level=min(level + 20, framework.level_cap),
        )
        for level in range(20, framework.level_cap, 20)
    ]
    framework.progression.talent = Talent(
        enabled=True, points_per_level=0.5, bonus_per_point=0.01
    )


def _ensure_investment(framework: ValueFramework) -> None:
    """未配置投放规划时，按消耗反推一套平衡的默认投放（约 115%）。

    默认给消耗一个温和增速，否则全等级段消耗相同、投放也没梯度。
    """
    for flow in framework.economy.flows:
        if flow.cost_growth == 0 and flow.income_growth == 0:
            flow.income_growth = 0.08
            flow.cost_growth = 0.06

    if framework.investment.bands or not framework.economy.flows:
        return

    cap = framework.level_cap
    flow = framework.economy.flows[0]
    main = flow.resource
    mid_end = max(11, cap // 2)
    segments = [
        (1, min(10, cap)),
        (min(11, cap), mid_end),
        (mid_end + 1, cap),
    ]
    bands: list[LevelBandPlan] = []
    for start, end in segments:
        if start > end:
            continue
        mid = (start + end) // 2
        target = flow.cost_at(mid) * 24 * 1.15
        # 主资源渠道占比：主线 45% / 日常 35% / 打怪 20%
        sources = [
            SourceTicket(
                name="主线任务",
                resource=main,
                amount_per_day=round(target * 0.45),
            ),
            SourceTicket(
                name="日常任务",
                resource=main,
                amount_per_day=round(target * 0.35),
            ),
            SourceTicket(
                name="打怪掉落",
                resource=main,
                amount_per_day=round(target * 0.20),
            ),
        ]
        # 副资源（付费货币等）走活动投放，量与消耗持平
        for extra in framework.economy.flows[1:]:
            sources.append(
                SourceTicket(
                    name="活动",
                    resource=extra.resource,
                    amount_per_day=round(extra.cost_at(mid) * 24 * 1.1),
                )
            )
        bands.append(
            LevelBandPlan(level_start=start, level_end=end, sources=sources)
        )
    framework.investment = InvestmentPlan(bands=bands)


# 有抽卡玩法的类型（其余类型不注入池子）
_GACHA_TYPES = {"rpg", "mmorpg", "card", "idle"}


def _ensure_gacha(framework: ValueFramework, game_type: str) -> None:
    """未配置抽卡池时按类型补一套标准池子。"""
    if framework.gacha or game_type not in _GACHA_TYPES:
        return
    framework.gacha = [
        GachaRule(
            pool="常驻池",
            base_rate=0.02,
            hard_pity=80,
            soft_pity=60,
            soft_step=0.03,
        ),
        GachaRule(
            pool="限定池",
            base_rate=0.006,
            hard_pity=90,
            soft_pity=74,
            soft_step=0.06,
        ),
    ]


def _ensure_equipment(framework: ValueFramework, game_type: str) -> None:
    """装备配置缺项补全（LLM 只给一部分时也补齐）。"""
    equipment = framework.equipment
    specs = _EQUIP_SLOTS.get(game_type, _EQUIP_SLOTS["rpg"])
    keys = [attr.key for attr in framework.attributes]
    primary = keys[0] if keys else "hp"
    secondary = keys[1] if len(keys) > 1 else primary
    tertiary = keys[2] if len(keys) > 2 else primary

    if not equipment.slots:
        equipment.slots = [
            EquipSlot(key=key, name=name, attr_key=attr_key, ratio=ratio)
            for key, name, attr_key, ratio in specs
        ]
    if not equipment.qualities:
        equipment.qualities = [
            EquipQuality(key="common", name="普通", multiplier=1.0, affix_count=0),
            EquipQuality(key="rare", name="稀有", multiplier=1.4, affix_count=1),
            EquipQuality(key="epic", name="史诗", multiplier=1.9, affix_count=2),
            EquipQuality(key="legendary", name="传说", multiplier=2.6, affix_count=3),
        ]
    if not equipment.affixes:
        equipment.affixes = [
            Affix(
                attr_key=primary,
                value_type="percent",
                min_value=0.02,
                max_value=0.12,
                weight=30,
            ),
            Affix(
                attr_key=secondary,
                value_type="percent",
                min_value=0.02,
                max_value=0.10,
                weight=25,
            ),
            Affix(
                attr_key=primary,
                value_type="flat",
                min_value=10,
                max_value=80,
                weight=20,
            ),
            Affix(
                attr_key=tertiary,
                value_type="percent",
                min_value=0.01,
                max_value=0.06,
                weight=15,
            ),
            Affix(
                attr_key=secondary,
                value_type="flat",
                min_value=5,
                max_value=40,
                weight=10,
            ),
        ]
    if not equipment.sets:
        equipment.sets = [
            EquipSet(
                name="破军套",
                effects=[
                    SetEffect(
                        pieces=2,
                        attr_key=primary,
                        value_type="percent",
                        value=0.05,
                    ),
                    SetEffect(
                        pieces=3,
                        attr_key=secondary,
                        value_type="percent",
                        value=0.08,
                    ),
                ],
            )
        ]


def _system_prompt(game_type: str) -> str:
    label = _GAME_TYPE_LABELS.get(game_type, "RPG")
    schema = json.dumps(ValueFramework.model_json_schema(), ensure_ascii=False)
    return (
        f"你是一名资深游戏数值策划。请根据需求输出一个{label}数值框架。"
        "属性 key 必须是小写英文标识符，不能使用 Python 关键字（如 def/class/for）；"
        "战斗公式 expression 只能包含属性 key、数字和 + - * / ( ) 运算符。"
        "严格按下面 JSON Schema 返回纯 JSON（不要 markdown 代码块、不要额外解释）：\n"
        + schema
    )


def _user_prompt(title: str, level_cap: int, theme: str, game_type: str) -> str:
    label = _GAME_TYPE_LABELS.get(game_type, "RPG")
    return (
        f"游戏类型：{label}\n标题：{title}\n题材：{theme}\n等级上限：{level_cap}\n"
        "请给出核心属性、成长曲线、战斗公式与经济循环。"
    )
