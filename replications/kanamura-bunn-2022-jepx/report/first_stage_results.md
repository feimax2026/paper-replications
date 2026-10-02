# First-stage descriptive results

This is a descriptive checkpoint, not yet an estimate of the paper's state-switching model.

## What the public-data panel shows

- Mean buy bid volume increased from 2.110 million kWh in FY2015 to 20.065 million kWh in FY2019.
- Mean sell bid volume increased from 5.063 million kWh to 19.885 million kWh over the same period.
- Mean buy-minus-sell tightness moved from -2.953 million kWh to 0.181 million kWh.
- Mean prices do not move monotonically across fiscal years. That is consistent with the paper's motivation for a nonlinear, regime-dependent model rather than a before/after mean comparison.

## Interpretation boundary

These figures provide a qualitative check of the paper's descriptive premise: market activity rose after the 2017 gross-bidding intervention and buy and sell volumes became more balanced. They do not establish causality or reproduce the paper's parameter estimates. The temperature column is a public daily max/min midpoint proxy, so it must be replaced or stress-tested before making an exact model-level claim.

## Generated artifacts

- `descriptive_statistics.csv`
- `../figures/figure_01_descriptive_time_series.svg`
- `../figures/figure_02_temperature_scarcity.svg`
