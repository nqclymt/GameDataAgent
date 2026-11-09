"""曲线拟合：用目标点反推成长曲线参数（统计方法，不训练模型）。"""

import numpy as np


def fit_power_curve(points: list[tuple[float, float]]) -> dict[str, float]:
    """拟合 y = a * x^b（经验曲线形态），返回 {a, b}。"""
    xs, ys = _arrays(points)
    b, log_a = np.polyfit(np.log(xs), np.log(ys), 1)
    return {"a": float(np.exp(log_a)), "b": float(b)}


def fit_exponential(points: list[tuple[float, float]]) -> dict[str, float]:
    """拟合 y = base * growth^(x-1)（属性指数成长），返回 {base, growth}。"""
    xs, ys = _arrays(points)
    slope, intercept = np.polyfit(xs - 1, np.log(ys), 1)
    return {"base": float(np.exp(intercept)), "growth": float(np.exp(slope))}


def fit_linear(points: list[tuple[float, float]]) -> dict[str, float]:
    """拟合 y = base + growth*(x-1)（属性线性成长），返回 {base, growth}。"""
    xs, ys = _arrays(points)
    slope, intercept = np.polyfit(xs - 1, ys, 1)
    return {"base": float(intercept), "growth": float(slope)}


def predict_power(points: list[tuple[float, float]], x: float) -> float:
    params = fit_power_curve(points)
    return float(params["a"] * (x ** params["b"]))


def predict_exponential(points: list[tuple[float, float]], x: float) -> float:
    params = fit_exponential(points)
    return float(params["base"] * (params["growth"] ** (x - 1)))


def predict_linear(points: list[tuple[float, float]], x: float) -> float:
    params = fit_linear(points)
    return float(params["base"] + params["growth"] * (x - 1))


def r2(points: list[tuple[float, float]], predict_fn) -> float:
    """拟合优度 R²，越接近 1 越贴合。"""
    xs, ys = _arrays(points)
    predicted = np.array([predict_fn(float(x)) for x in xs])
    ss_res = float(np.sum((ys - predicted) ** 2))
    ss_tot = float(np.sum((ys - np.mean(ys)) ** 2))
    return 1 - ss_res / ss_tot if ss_tot else 1.0


def _arrays(points: list[tuple[float, float]]):
    if len(points) < 2:
        raise ValueError("至少需要 2 个目标点")
    xs = np.array([p[0] for p in points], dtype=float)
    ys = np.array([p[1] for p in points], dtype=float)
    if (xs <= 0).any() or (ys <= 0).any():
        raise ValueError("目标点必须为正数")
    return xs, ys
