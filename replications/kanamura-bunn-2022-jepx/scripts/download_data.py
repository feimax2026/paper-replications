#!/usr/bin/env python3
"""Download the public convenience copies used by the first replication stage."""

from __future__ import annotations

from pathlib import Path
from urllib.request import urlretrieve


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
SOURCES = {
    "jepx_spot.csv": "https://japanesepower.org/jepxSpot.csv",
    "japan_weather.csv": "https://japanesepower.org/weatherData.csv",
}


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    for filename, url in SOURCES.items():
        target = RAW / filename
        print(f"Downloading {filename}...")
        urlretrieve(url, target)
        print(f"Saved {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
