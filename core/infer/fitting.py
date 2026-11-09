"""把拟合结果应用回数值框架（拟合 → 建模的闭环）。"""

from pydantic import BaseModel, Field

from core.infer.curve_fit import (
    fit_exponential,
    fit_linear,
    fit_power_curve,
    predict_exponential,
    predict_linear,
    predict_power,
    r2,
)
from core.modeling.framework import ValueFramework


class FitOutcome(BaseModel):
    target: str
    params: dict[str, float]
    r2: float
    warnings: list[str] = Field(default_factory=list)


def parse_points(text: str) -> list[tuple[float, float]]:
    """解析 '10:100; 30:1000; 60:10000' 形式的目标点。"""
    points: list[tuple[float, float]] = []
    normalized = text.replace("；", ";").replace("：", ":")
    for chunk in normalized.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = chunk.replace(",", ":").split(":")
        if len(parts) != 2:
            raise ValueError(f"无法解析目标点：{chunk}")
        points.append((float(parts[0]), float(parts[1])))
    if len(points) < 2:
        raise ValueError("至少需要 2 个目标点")
    return points


def fit_exp(framework: ValueFramework, points: list[tuple[float, float]]) -> FitOutcome:
    """拟合经验曲线并写回框架。"""
    params = fit_power_curve(points)
    framework.exp_curve.params = {"base": params["a"], "exponent": params["b"]}
    score = r2(points, lambda x: predict_power(points, x))

    warnings: list[str] = []
    if params["a"] < 1:
        warnings.append(
            f"拟合出的 1 级经验仅 {params['a']:.2f}，低等级会过易，建议上调 base"
        )
    if score < 0.9:
        warnings.append(f"拟合优度 R²={score:.3f} 偏低，目标点可能不符合幂曲线")
    return FitOutcome(target="exp", params=params, r2=score, warnings=warnings)


def fit_attribute(
    framework: ValueFramework, key: str, points: list[tuple[float, float]]
) -> FitOutcome:
    """拟合某个属性的成长曲线并写回框架。"""
    attr = next((a for a in framework.attributes if a.key == key), None)
    if attr is None:
        raise ValueError(f"未找到属性：{key}")

    if attr.growth_type == "exponential":
        params = fit_exponential(points)
        score = r2(points, lambda x: predict_exponential(points, x))
    else:
        params = fit_linear(points)
        score = r2(points, lambda x: predict_linear(points, x))

    attr.base = round(params["base"], 4)
    attr.growth = round(params["growth"], 6)

    warnings: list[str] = []
    if score < 0.9:
        warnings.append(f"拟合优度 R²={score:.3f} 偏低，目标点与当前成长类型不匹配")
    if attr.growth_type == "exponential" and params["growth"] <= 1:
        warnings.append("指数成长的 growth 应大于 1，否则数值会随等级下降")
    return FitOutcome(target=key, params=params, r2=score, warnings=warnings)
