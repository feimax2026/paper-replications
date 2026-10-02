#!/usr/bin/env python3
"""Diagnose temporal changes in the FY2020–FY2024 JEPX extension period."""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "data" / "processed" / "extension_period_panel.csv"
REPORT = ROOT / "report" / "extension"


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def pearson(x_values: list[float], y_values: list[float]) -> float:
    x_mean, y_mean = mean(x_values), mean(y_values)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
    x_scale = math.sqrt(sum((x - x_mean) ** 2 for x in x_values))
    y_scale = math.sqrt(sum((y - y_mean) ** 2 for y in y_values))
    return numerator / (x_scale * y_scale) if x_scale and y_scale else 0.0


def solve_3x3(matrix: list[list[float]], vector: list[float]) -> list[float]:
    augmented = [row[:] + [target] for row, target in zip(matrix, vector)]
    for pivot in range(3):
        best = max(range(pivot, 3), key=lambda row: abs(augmented[row][pivot]))
        if abs(augmented[best][pivot]) < 1e-12:
            raise ValueError("Singular normal-equation matrix")
        augmented[pivot], augmented[best] = augmented[best], augmented[pivot]
        divisor = augmented[pivot][pivot]
        augmented[pivot] = [value / divisor for value in augmented[pivot]]
        for row in range(3):
            if row == pivot:
                continue
            factor = augmented[row][pivot]
            augmented[row] = [value - factor * pivot_value for value, pivot_value in zip(augmented[row], augmented[pivot])]
    return [augmented[row][3] for row in range(3)]


def fit_v_shape(rows: list[dict[str, float | str]]) -> dict[str, float]:
    temperatures = [float(row["temperature"]) for row in rows]
    tightness = [float(row["tightness"]) for row in rows]
    best: dict[str, float] | None = None
    lower_tick = math.ceil((min(temperatures) + 0.25) * 4)
    upper_tick = math.floor((max(temperatures) - 0.25) * 4)
    for tick in range(lower_tick, upper_tick + 1):
        turning_point = tick / 4
        normal = [[0.0] * 3 for _ in range(3)]
        target = [0.0] * 3
        for temperature, value in zip(temperatures, tightness):
            features = [1.0, temperature, max(temperature - turning_point, 0.0)]
            for row in range(3):
                target[row] += features[row] * value
                for column in range(3):
                    normal[row][column] += features[row] * features[column]
        intercept, cold_slope, hinge = solve_3x3(normal, target)
        residual_sum = sum(
            (value - (intercept + cold_slope * temperature + hinge * max(temperature - turning_point, 0.0))) ** 2
            for temperature, value in zip(temperatures, tightness)
        )
        if best is None or residual_sum < best["residual_sum"]:
            best = {
                "turning_point": turning_point,
                "intercept": intercept,
                "cold_slope": cold_slope,
                "warm_slope": cold_slope + hinge,
                "residual_sum": residual_sum,
            }
    assert best is not None
    total_sum = sum((value - mean(tightness)) ** 2 for value in tightness)
    best["r_squared"] = 1 - best["residual_sum"] / total_sum if total_sum else 0.0
    return best


def main() -> None:
    rows: list[dict[str, float | str]] = []
    daily: dict[str, list[dict[str, float | str]]] = defaultdict(list)
    with PANEL.open(encoding="utf-8", newline="") as handle:
        for source in csv.DictReader(handle):
            row = {
                "date": source["date"],
                "fiscal_year": source["fiscal_year"],
                "price": float(source["system_price_yen_per_kwh"]),
                "tightness": float(source["buy_minus_sell_kwh"]) / 1_000_000,
                "temperature": float(source["tokyo_temperature_proxy_c"]),
            }
            rows.append(row)
            daily[str(row["date"])].append(row)

    by_year: dict[str, list[dict[str, float | str]]] = defaultdict(list)
    for row in rows:
        by_year[str(row["fiscal_year"])].append(row)

    REPORT.mkdir(parents=True, exist_ok=True)
    fiscal_rows: list[dict[str, float | str]] = []
    for fiscal_year in sorted(by_year):
        group = by_year[fiscal_year]
        prices = [float(row["price"]) for row in group]
        tightness = [float(row["tightness"]) for row in group]
        temperatures = [float(row["temperature"]) for row in group]
        model = fit_v_shape(group)
        fiscal_rows.append(
            {
                "fiscal_year": fiscal_year,
                "mean_price": mean(prices),
                "p95_price": quantile(prices, 0.95),
                "p99_price": quantile(prices, 0.99),
                "max_price": max(prices),
                "half_hours_ge_50": sum(price >= 50 for price in prices),
                "mean_tightness": mean(tightness),
                "price_tightness_correlation": pearson(prices, tightness),
                "temperature_tightness_correlation": pearson(temperatures, tightness),
                **model,
            }
        )

    daily_events = []
    for delivery_date, group in daily.items():
        prices = [float(row["price"]) for row in group]
        daily_events.append(
            {
                "date": delivery_date,
                "fiscal_year": str(group[0]["fiscal_year"]),
                "mean_price": mean(prices),
                "max_price": max(prices),
                "mean_tightness": mean([float(row["tightness"]) for row in group]),
                "temperature": float(group[0]["temperature"]),
            }
        )
    daily_events.sort(key=lambda row: float(row["mean_price"]), reverse=True)

    fiscal_path = REPORT / "structural_diagnostics_by_fiscal_year.csv"
    with fiscal_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fiscal_rows[0]))
        writer.writeheader()
        writer.writerows(fiscal_rows)
    event_path = REPORT / "top_daily_price_events.csv"
    with event_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(daily_events[0]))
        writer.writeheader()
        writer.writerows(daily_events[:15])

    diagnostics = {str(row["fiscal_year"]): row for row in fiscal_rows}
    report = [
        "# FY2020–FY2024 extension findings",
        "",
        "## Findings",
        "",
        f"- **Tail risk is concentrated in FY2020–FY2022.** FY2020 has {diagnostics['FY2020']['half_hours_ge_50']} half-hours at or above 50 JPY/kWh and a daily-price peak that appears in the event table. FY2022 has the highest mean price ({diagnostics['FY2022']['mean_price']:.2f} JPY/kWh).",
        f"- **Bid tightness did not remain near the FY2019 balance.** Mean tightness is close to zero in FY2020–FY2021, then falls to {diagnostics['FY2023']['mean_tightness']:.2f} million kWh in FY2023 and {diagnostics['FY2024']['mean_tightness']:.2f} million kWh in FY2024.",
        f"- **The temperature relationship is not temporally stable.** The V-shape fit falls from R²={diagnostics['FY2020']['r_squared']:.3f} in FY2020 to R²={diagnostics['FY2024']['r_squared']:.3f} in FY2024, while the estimated turning point shifts from {diagnostics['FY2020']['turning_point']:.2f}°C to {diagnostics['FY2024']['turning_point']:.2f}°C.",
        f"- **Price and bid tightness are related but not interchangeable.** Their correlation rises from {diagnostics['FY2020']['price_tightness_correlation']:.3f} in FY2020 to {diagnostics['FY2024']['price_tightness_correlation']:.3f} in FY2024, even while the mean tightness becomes more negative. A bid imbalance alone therefore cannot explain the extension-period price distribution.",
        "",
        "## Interpretation boundary",
        "",
        "These are descriptive and reduced-form diagnostics. They do not identify the cause of any change, isolate market-design effects, or reproduce the paper's full state-switching model. The temperature series remains a daily max/min midpoint proxy. The next defensible step is to estimate the same V-shape specification on the two pooled periods and test whether its parameters differ.",
        "",
        "## Artifacts",
        "",
        "- `structural_diagnostics_by_fiscal_year.csv`",
        "- `top_daily_price_events.csv`",
    ]
    (REPORT / "extension_findings.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Wrote {fiscal_path.relative_to(ROOT)}")
    print(f"Wrote {event_path.relative_to(ROOT)}")
    print("Wrote report/extension/extension_findings.md")


if __name__ == "__main__":
    main()
