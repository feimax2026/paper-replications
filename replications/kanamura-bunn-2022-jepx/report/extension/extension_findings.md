# FY2020–FY2024 extension findings

## Findings

- **Tail risk is concentrated in FY2020–FY2022.** FY2020 has 823 half-hours at or above 50 JPY/kWh and a daily-price peak that appears in the event table. FY2022 has the highest mean price (20.41 JPY/kWh).
- **Bid tightness did not remain near the FY2019 balance.** Mean tightness is close to zero in FY2020–FY2021, then falls to -4.42 million kWh in FY2023 and -4.98 million kWh in FY2024.
- **The temperature relationship is not temporally stable.** The V-shape fit falls from R²=0.262 in FY2020 to R²=0.045 in FY2024, while the estimated turning point shifts from 20.25°C to 8.25°C.
- **Price and bid tightness are related but not interchangeable.** Their correlation rises from 0.460 in FY2020 to 0.837 in FY2024, even while the mean tightness becomes more negative. A bid imbalance alone therefore cannot explain the extension-period price distribution.

## Interpretation boundary

These are descriptive and reduced-form diagnostics. They do not identify the cause of any change, isolate market-design effects, or reproduce the paper's full state-switching model. The temperature series remains a daily max/min midpoint proxy. The next defensible step is to estimate the same V-shape specification on the two pooled periods and test whether its parameters differ.

## Artifacts

- `structural_diagnostics_by_fiscal_year.csv`
- `top_daily_price_events.csv`
