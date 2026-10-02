#!/usr/bin/env python3
"""Build the first replication panel for Kanamura and Bunn (2022).

This dependency-free script combines JEPX half-hourly system-price data with a
Tokyo temperature proxy. The paper uses Tokyo temperature as a first-order
approximation for the JEPX system price. The public weather mirror currently
contains daily maximum and minimum temperatures, so their midpoint is retained
explicitly as a proxy rather than presented as the paper's exact input series.
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed" / "kanamura_bunn_2022_panel.csv"

START = date(2015, 4, 1)
END = date(2020, 3, 8)


def as_float(value: str) -> float | None:
    return float(value) if value not in ("", "NA", "N/A") else None


def load_temperature_proxy() -> dict[str, float | None]:
    temperatures: dict[str, float | None] = {}
    with (RAW / "japan_weather.csv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            high = as_float(row["Tokyo_47662_TMax"])
            low = as_float(row["Tokyo_47662_TMin"])
            temperatures[row["DateTime"]] = (high + low) / 2 if high is not None and low is not None else None
    return temperatures


def main() -> None:
    temperatures = load_temperature_proxy()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "datetime",
        "date",
        "period_id",
        "fiscal_year",
        "system_price_yen_per_kwh",
        "buy_bid_volume_kwh",
        "sell_bid_volume_kwh",
        "buy_minus_sell_kwh",
        "contracted_total_volume_kwh",
        "tokyo_temperature_proxy_c",
    ]

    written = 0
    with (RAW / "jepx_spot.csv").open(encoding="utf-8", newline="") as source, OUT.open(
        "w", encoding="utf-8", newline=""
    ) as target:
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        for row in csv.DictReader(source):
            delivery_date = date.fromisoformat(row["Date"])
            if not START <= delivery_date <= END:
                continue

            buy = as_float(row["Buy Bid Volume kWh"])
            sell = as_float(row["Sell Bid Volume kWh"])
            writer.writerow(
                {
                    "datetime": row["datetime"],
                    "date": row["Date"],
                    "period_id": row["PeriodID"],
                    "fiscal_year": f"FY{delivery_date.year if delivery_date.month >= 4 else delivery_date.year - 1}",
                    "system_price_yen_per_kwh": row["System Price Yen/kWh"],
                    "buy_bid_volume_kwh": row["Buy Bid Volume kWh"],
                    "sell_bid_volume_kwh": row["Sell Bid Volume kWh"],
                    "buy_minus_sell_kwh": buy - sell if buy is not None and sell is not None else "",
                    "contracted_total_volume_kwh": row["Contracted Total Volume kWh"],
                    "tokyo_temperature_proxy_c": temperatures.get(row["Date"], ""),
                }
            )
            written += 1
    print(f"Wrote {written:,} half-hourly observations to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
