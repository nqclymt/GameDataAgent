"""数值框架数据结构（跨游戏类型的通用骨架）。"""

from pydantic import BaseModel, Field


class Attribute(BaseModel):
    """一条可成长属性。

    growth_type 仅支持 linear（每级加 growth）与 exponential（每级乘 growth）。
    """

    key: str
    name: str
    base: float
    growth: float
    growth_type: str = "linear"  # linear | exponential


class ExpSegment(BaseModel):
    """分段经验倍率：在 [start_level, end_level] 内，经验乘以 multiplier。

    用于制造出生点、卡点与满级冲刺（如 31-50 级 ×1.5、51-60 级 ×2.5）。
    区间重叠时按列表中第一个命中的分段生效。
    """

    start_level: int
    end_level: int
    multiplier: float = 1.0
    note: str = ""


class GrowthCurve(BaseModel):
    """成长曲线：全局参数 + 可选的分段倍率。"""

    name: str
    formula: str
    params: dict[str, float] = Field(default_factory=dict)
    segments: list[ExpSegment] = Field(default_factory=list)


class CombatFormula(BaseModel):
    """战斗公式。"""

    name: str
    expression: str
    description: str = ""


class ResourceFlow(BaseModel):
    """资源流：产出与消耗速率；消耗可选随等级增长。"""

    resource: str
    income_per_hour: float = 0.0
    cost_per_hour: float = 0.0
    income_growth: float = 0.0
    cost_growth: float = 0.0

    @property
    def net_per_hour(self) -> float:
        return round(self.income_per_hour - self.cost_per_hour, 2)

    def income_at(self, level: int) -> float:
        """某等级时的每小时产出（income_growth 为每级增幅）。"""
        return self.income_per_hour * (1 + self.income_growth * max(level - 1, 0))

    def cost_at(self, level: int) -> float:
        """某等级时的每小时消耗（cost_growth 为每级增幅）。"""
        return self.cost_per_hour * (1 + self.cost_growth * max(level - 1, 0))

    def net_at(self, level: int) -> float:
        """某等级时的每小时净产出。"""
        return round(self.income_at(level) - self.cost_at(level), 2)


class DropEntry(BaseModel):
    """掉落条目。

    probability 为单次击杀/结算时该物品的**独立判定**概率（0~1]，
    各项独立 roll，因此同一张表内合计可以超过 100%。
    """

    item: str
    probability: float
    min_count: int = 1
    max_count: int = 1


class DropTable(BaseModel):
    """掉落表：一组掉落条目的概率集合。"""

    name: str
    entries: list[DropEntry] = Field(default_factory=list)


class PowerFormula(BaseModel):
    """战力公式：把多个属性按权重合成一个可横向比较的数值。

    weights 为空时按属性的通用权重兜底（见 core.calc.growth）。
    """

    name: str = "战力"
    weights: dict[str, float] = Field(default_factory=dict)


class Affix(BaseModel):
    """装备词条：百分比（乘基础）或固定值（直接相加）。

    词条从池中按权重抽取，条数由品质的 affix_count 决定。
    """

    attr_key: str
    value_type: str = "percent"  # percent | flat
    min_value: float = 0.0
    max_value: float = 0.0
    weight: float = 1.0

    @property
    def expected(self) -> float:
        return (self.min_value + self.max_value) / 2


class SetEffect(BaseModel):
    """套装效果：穿够 pieces 件后生效。"""

    pieces: int
    attr_key: str
    value_type: str = "percent"  # percent | flat
    value: float = 0.0


class EquipSet(BaseModel):
    """套装：多个件数门槛，逐级解锁。"""

    name: str
    effects: list[SetEffect] = Field(default_factory=list)


class EquipQuality(BaseModel):
    """装备品质：决定属性倍率与词条数量。"""

    key: str
    name: str
    multiplier: float = 1.0
    affix_count: int = 0


class EquipSlot(BaseModel):
    """装备部位：提供某属性的百分比加成。"""

    key: str
    name: str
    attr_key: str
    ratio: float = 0.3


class EnhanceRule(BaseModel):
    """强化规则：等级越高加成越多、消耗越贵。"""

    max_level: int = 10
    growth: float = 0.12
    cost_base: float = 100.0
    cost_exponent: float = 1.5

    def multiplier(self, level: int) -> float:
        """强化 level 级后的总加成倍率。"""
        return 1 + self.growth * level

    def cost(self, level: int) -> int:
        """从 level-1 强化到 level 的消耗。"""
        return int(self.cost_base * (level**self.cost_exponent))


class Equipment(BaseModel):
    """装备系统配置：部位 + 品质 + 强化 + 词条池 + 套装。"""

    slots: list[EquipSlot] = Field(default_factory=list)
    qualities: list[EquipQuality] = Field(default_factory=list)
    enhance: EnhanceRule = Field(default_factory=EnhanceRule)
    affixes: list[Affix] = Field(default_factory=list)
    sets: list[EquipSet] = Field(default_factory=list)


class GachaRule(BaseModel):
    """抽卡池规则：基础概率 + 软保底（概率递增）+ 硬保底（第 N 抽必出）。

    软保底从 soft_pity 抽开始，每抽概率增加 soft_step，直到 hard_pity 必出。
    """

    pool: str = "限定池"
    base_rate: float = 0.006
    hard_pity: int | None = 90
    soft_pity: int | None = 74
    soft_step: float = 0.06
    win_rate: float = 1.0
    guarantee: bool = False


class Profession(BaseModel):
    """职业：同一框架内的属性倾向差异（系数）。

    stat_scale 形如 {"hp": 1.25, "atk": 0.85}，
    表示该职业的生命是基准的 1.25 倍、攻击是 0.85 倍。
    """

    name: str
    stat_scale: dict[str, float] = Field(default_factory=dict)


class Breakthrough(BaseModel):
    """突破节点：卡在该等级，消耗资源后解锁更高等级上限。"""

    level: int
    cost_resource: str = ""
    cost_amount: float = 0.0
    unlock_level: int = 0


class Rebirth(BaseModel):
    """转生：满级后重置等级，换取永久属性加成。"""

    enabled: bool = False
    stat_bonus: float = 0.05
    max_rebirths: int = 5


class Talent(BaseModel):
    """天赋：每级获得天赋点，点数按比例提升属性。"""

    enabled: bool = False
    points_per_level: float = 0.5
    bonus_per_point: float = 0.01


class Progression(BaseModel):
    """角色进阶：突破 + 转生 + 天赋。"""

    breakthroughs: list[Breakthrough] = Field(default_factory=list)
    rebirth: Rebirth = Field(default_factory=Rebirth)
    talent: Talent = Field(default_factory=Talent)


class SourceTicket(BaseModel):
    """单一投放渠道：某资源每天给多少（主线/日常/活动/打怪等）。"""

    name: str
    resource: str
    amount_per_day: float = 0.0


class LevelBandPlan(BaseModel):
    """等级段的投放规划。"""

    level_start: int
    level_end: int
    sources: list[SourceTicket] = Field(default_factory=list)


class InvestmentPlan(BaseModel):
    """投放规划：按等级段配置各渠道的每日投放量。"""

    bands: list[LevelBandPlan] = Field(default_factory=list)

    def band_of(self, level: int) -> LevelBandPlan | None:
        for band in self.bands:
            if band.level_start <= level <= band.level_end:
                return band
        return None


class Economy(BaseModel):
    """经济循环（文字描述 + 量化资源流）。"""

    currencies: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    sinks: list[str] = Field(default_factory=list)
    flows: list[ResourceFlow] = Field(default_factory=list)


class ValueFramework(BaseModel):
    """游戏数值框架。"""

    game_type: str
    title: str
    level_cap: int
    attributes: list[Attribute] = Field(default_factory=list)
    exp_curve: GrowthCurve
    combat: CombatFormula
    economy: Economy = Field(default_factory=Economy)
    drop_tables: list[DropTable] = Field(default_factory=list)
    power: PowerFormula = Field(default_factory=PowerFormula)
    equipment: Equipment = Field(default_factory=Equipment)
    gacha: list[GachaRule] = Field(default_factory=list)
    investment: InvestmentPlan = Field(default_factory=InvestmentPlan)
    progression: Progression = Field(default_factory=Progression)
    professions: list[Profession] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    def to_json(self, indent: int = 2) -> str:
        return self.model_dump_json(indent=indent)
