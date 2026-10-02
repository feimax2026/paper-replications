#!/usr/bin/env python3
"""Create descriptive results for the Kanamura and Bunn (2022) replication."""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "data" / "processed" / "kanamura_bunn_2022_panel.csv"
FIGURES = ROOT / "figures"
REPORT = ROOT / "report"

WIDTH, HEIGHT = 1400, 940
LEFT, RIGHT, TOP, BOTTOM = 95, 45, 65, 60


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def quantile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * p
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def svg_start(title: str, width: int = WIDTH, height: int = HEIGHT) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<style>text { font-family: Arial, sans-serif; fill: #202124; } .axis { stroke: #9aa0a6; stroke-width: 1; } .grid { stroke: #e8eaed; stroke-width: 1; } .title { font-size: 22px; font-weight: 700; } .subtitle { font-size: 13px; fill: #5f6368; } .label { font-size: 12px; fill: #5f6368; } .panel-title { font-size: 15px; font-weight: 700; }</style>',
        f'<text x="{LEFT}" y="32" class="title">{title}</text>',
    ]


def write_svg(path: Path, elements: list[str]) -> None:
    path.write_text("\n".join(elements + ["</svg>"]), encoding="utf-8")


def scale(value: float, low: float, high: float, target_low: float, target_high: float) -> float:
    if high == low:
        return (target_low + target_high) / 2
    return target_low + (value - low) / (high - low) * (target_high - target_low)


def line_panel(
    elements: list[str],
    x: float,
    y: float,
    width: float,
    height: float,
    title: str,
    dates: list[date],
    values: list[float],
    color: str,
) -> None:
    low, high = min(values), max(values)
    padding = (high - low) * 0.05 or 1
    low, high = low - padding, high + padding
    start, end = dates[0].toordinal(), dates[-1].toordinal()

    elements.append(f'<text x="{x}" y="{y - 10}" class="panel-title">{title}</text>')
    for fraction in (0, 0.5, 1):
        grid_y = y + height - fraction * height
        value = low + fraction * (high - low)
        elements.append(f'<line x1="{x}" y1="{grid_y:.1f}" x2="{x + width}" y2="{grid_y:.1f}" class="grid"/>')
        elements.append(f'<text x="{x - 8}" y="{grid_y + 4:.1f}" text-anchor="end" class="label">{value:.1f}</text>')
    elements.append(f'<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="none" class="axis"/>')
    points = " ".join(
        f'{scale(day.toordinal(), start, end, x, x + width):.2f},{scale(value, low, high, y + height, y):.2f}'
        for day, value in zip(dates, values)
    )
    elements.append(f'<polyline fill="none" stroke="{color}" stroke-width="1.25" points="{points}"/>')
    for year in range(2015, 2021):
        tick = date(year, 4, 1)
        if dates[0] <= tick <= dates[-1]:
            tick_x = scale(tick.toordinal(), start, end, x, x + width)
            elements.append(f'<line x1="{tick_x:.1f}" y1="{y + height}" x2="{tick_x:.1f}" y2="{y + height + 5}" class="axis"/>')
            elements.append(f'<text x="{tick_x:.1f}" y="{y + height + 20}" text-anchor="middle" class="label">FY{year}</text>')


def build_time_series(daily: dict[date, dict[str, list[float]]]) -> None:
    dates = sorted(daily)
    average = {metric: [mean(daily[day][metric]) for day in dates] for metric in daily[dates[0]]}
    FIGURES.mkdir(exist_ok=True)
    elements = svg_start("JEPX descriptive replication: FY2015–FY2019")
    elements.append('<text x="95" y="52" class="subtitle">Daily means from the public-data panel. Dashed policy marker: gross bidding begins in FY2017.</text>')
    positions = [(95, 105), (760, 105), (95, 515), (760, 515)]
    panels = [
        ("System price (JPY/kWh)", "price", "#d93025"),
        ("Buy bid volume (million kWh)", "buy_million", "#1a73e8"),
        ("Sell bid volume (million kWh)", "sell_million", "#188038"),
        ("Tokyo temperature proxy (C)", "temperature", "#f9ab00"),
    ]
    for (title, metric, color), (x, y) in zip(panels, positions):
        line_panel(elements, x, y, 555, 300, title, dates, average[metric], color)
        marker = date(2017, 4, 1)
        marker_x = scale(marker.toordinal(), dates[0].toordinal(), dates[-1].toordinal(), x, x + 555)
        elements.append(f'<line x1="{marker_x:.1f}" y1="{y}" x2="{marker_x:.1f}" y2="{y + 300}" stroke="#5f6368" stroke-width="1" stroke-dasharray="5,4"/>')
    write_svg(FIGURES / "figure_01_descriptive_time_series.svg", elements)


def build_scatter(rows: list[dict[str, float | str]]) -> None:
    selected = [row for row in rows if row["fiscal_year"] in ("FY2015", "FY2019")]
    x_values = [float(row["temperature"]) for row in selected]
    y_values = [float(row["scarcity"]) / 1_000_000 for row in selected]
    x_low, x_high = math.floor(min(x_values)) - 1, math.ceil(max(x_values)) + 1
    y_low, y_high = math.floor(min(y_values)) - 1, math.ceil(max(y_values)) + 1
    elements = svg_start("Temperature and JEPX market tightness", width=1400, height=650)
    elements.append('<text x="95" y="52" class="subtitle">Each dot is a half-hour observation. Tightness = buy bid volume minus sell bid volume.</text>')
    panels = [("FY2015", 95, "#1a73e8"), ("FY2019", 760, "#d93025")]
    for fiscal_year, x, color in panels:
        y, width, height = 105, 555, 430
        elements.append(f'<text x="{x}" y="90" class="panel-title">{fiscal_year}</text>')
        for fraction in (0, 0.5, 1):
            grid_x = x + fraction * width
            grid_y = y + height - fraction * height
            x_tick = x_low + fraction * (x_high - x_low)
            y_tick = y_low + fraction * (y_high - y_low)
            elements.append(f'<line x1="{grid_x:.1f}" y1="{y}" x2="{grid_x:.1f}" y2="{y + height}" class="grid"/>')
            elements.append(f'<line x1="{x}" y1="{grid_y:.1f}" x2="{x + width}" y2="{grid_y:.1f}" class="grid"/>')
            elements.append(f'<text x="{grid_x:.1f}" y="{y + height + 20}" text-anchor="middle" class="label">{x_tick:.0f}</text>')
            elements.append(f'<text x="{x - 8}" y="{grid_y + 4:.1f}" text-anchor="end" class="label">{y_tick:.0f}</text>')
        elements.append(f'<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="none" class="axis"/>')
        year_rows = [row for row in selected if row["fiscal_year"] == fiscal_year]
        for row in year_rows[::6]:
            px = scale(float(row["temperature"]), x_low, x_high, x, x + width)
            py = scale(float(row["scarcity"]) / 1_000_000, y_low, y_high, y + height, y)
            elements.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="1.2" fill="{color}" fill-opacity="0.18"/>')
        elements.append(f'<text x="{x + width / 2}" y="{y + height + 45}" text-anchor="middle" class="label">Tokyo temperature proxy (C)</text>')
    elements.append('<text x="45" y="330" transform="rotate(-90 45 330)" text-anchor="middle" class="label">Buy minus sell bid volume (million kWh)</text>')
    write_svg(FIGURES / "figure_02_temperature_scarcity.svg", elements)


def main() -> None:
    rows: list[dict[str, float | str]] = []
    daily: dict[date, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    with PANEL.open(encoding="utf-8", newline="") as handle:
        for source in csv.DictReader(handle):
            delivery_date = date.fromisoformat(source["date"])
            row = {
                "fiscal_year": source["fiscal_year"],
                "price": float(source["system_price_yen_per_kwh"]),
                "buy": float(source["buy_bid_volume_kwh"]),
                "sell": float(source["sell_bid_volume_kwh"]),
                "scarcity": float(source["buy_minus_sell_kwh"]),
                "temperature": float(source["tokyo_temperature_proxy_c"]),
            }
            rows.append(row)
            daily[delivery_date]["price"].append(row["price"])
            daily[delivery_date]["buy_million"].append(row["buy"] / 1_000_000)
            daily[delivery_date]["sell_million"].append(row["sell"] / 1_000_000)
            daily[delivery_date]["temperature"].append(row["temperature"])

    REPORT.mkdir(exist_ok=True)
    summary_path = REPORT / "descriptive_statistics.csv"
    with summary_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["fiscal_year", "observations", "mean_price", "p95_price", "mean_buy_million_kwh", "mean_sell_million_kwh", "mean_tightness_million_kwh", "mean_temperature_c"])
        for fiscal_year in sorted({str(row["fiscal_year"]) for row in rows}):
            group = [row for row in rows if row["fiscal_year"] == fiscal_year]
            writer.writerow([
                fiscal_year,
                len(group),
                f"{mean([float(row['price']) for row in group]):.3f}",
                f"{quantile([float(row['price']) for row in group], 0.95):.3f}",
                f"{mean([float(row['buy']) for row in group]) / 1_000_000:.3f}",
                f"{mean([float(row['sell']) for row in group]) / 1_000_000:.3f}",
                f"{mean([float(row['scarcity']) for row in group]) / 1_000_000:.3f}",
                f"{mean([float(row['temperature']) for row in group]):.3f}",
            ])
    by_year = {year: [row for row in rows if row["fiscal_year"] == year] for year in sorted({str(row["fiscal_year"]) for row in rows})}
    first, last = by_year["FY2015"], by_year["FY2019"]
    first_tightness = mean([float(row["scarcity"]) for row in first]) / 1_000_000
    last_tightness = mean([float(row["scarcity"]) for row in last]) / 1_000_000
    first_buy = mean([float(row["buy"]) for row in first]) / 1_000_000
    last_buy = mean([float(row["buy"]) for row in last]) / 1_000_000
    first_sell = mean([float(row["sell"]) for row in first]) / 1_000_000
    last_sell = mean([float(row["sell"]) for row in last]) / 1_000_000
    (REPORT / "first_stage_results.md").write_text(
        "# First-stage descriptive results\n\n"
        "This is a descriptive checkpoint, not yet an estimate of the paper's state-switching model.\n\n"
        "## What the public-data panel shows\n\n"
        f"- Mean buy bid volume increased from {first_buy:.3f} million kWh in FY2015 to {last_buy:.3f} million kWh in FY2019.\n"
        f"- Mean sell bid volume increased from {first_sell:.3f} million kWh to {last_sell:.3f} million kWh over the same period.\n"
        f"- Mean buy-minus-sell tightness moved from {first_tightness:.3f} million kWh to {last_tightness:.3f} million kWh.\n"
        "- Mean prices do not move monotonically across fiscal years. That is consistent with the paper's motivation for a nonlinear, regime-dependent model rather than a before/after mean comparison.\n\n"
        "## Interpretation boundary\n\n"
        "These figures provide a qualitative check of the paper's descriptive premise: market activity rose after the 2017 gross-bidding intervention and buy and sell volumes became more balanced. They do not establish causality or reproduce the paper's parameter estimates. The temperature column is a public daily max/min midpoint proxy, so it must be replaced or stress-tested before making an exact model-level claim.\n\n"
        "## Generated artifacts\n\n"
        "- `descriptive_statistics.csv`\n"
        "- `../figures/figure_01_descriptive_time_series.svg`\n"
        "- `../figures/figure_02_temperature_scarcity.svg`\n",
        encoding="utf-8",
    )
    build_time_series(daily)
    build_scatter(rows)
    print(f"Wrote {summary_path.relative_to(ROOT)}")
    print("Wrote report/first_stage_results.md")
    print("Wrote figures/figure_01_descriptive_time_series.svg")
    print("Wrote figures/figure_02_temperature_scarcity.svg")


if __name__ == "__main__":
    main()
