# Numerical conventions

The model reference declares each input's unit and bounds. These conventions
follow [ADR-0008](https://github.com/pyeconomics-dev/pyeconomics/blob/main/docs/adr/0008-numerical-conventions.md).

- Rates, returns, yields and percentages are decimals. Use `0.05` for 5%,
  and `0.0001` for one basis point. Conversion helpers live in `pyeconomics.core`.
- Money uses a consistent currency chosen by the caller. Models do not perform
  currency conversion implicitly. Years, periods and frequency are distinct units.
- Declare compounding and frequency explicitly where a calculation supports
  them. A nominal periodic rate and an effective annual rate are different inputs.
- Day counts include ACT/360, ACT/365F, ACT/ACT ISDA, ACT/ACT ICMA,
  30/360 US and 30E/360. ICMA needs its reference coupon period. Calendars and
  business-day adjustments are explicit; dates have no implicit timezone.
- Outputs are finite. Undefined operations and numerical failures raise
  documented errors. Floating-point comparisons use the unit's `Tolerance`,
  with both absolute and relative thresholds; decimal rates use tighter
  thresholds than monetary amounts.
- Stochastic models require a seed and use NumPy's PCG64 generator. The manifest
  records the seed and generator. Repeating inputs in the same environment
  repeats results; no global random state or clock enters a model.
- Arrays have explicit maximum lengths. Inputs and outputs reject unknown fields.

Consult each card's assumptions and limitations before interpreting a result.
