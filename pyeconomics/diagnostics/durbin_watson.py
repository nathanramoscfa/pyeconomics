# pyeconomics/diagnostics/durbin_watson.py

import pandas as pd
from statsmodels.stats.stattools import durbin_watson


def durbin_watson_test(residuals: pd.Series) -> None:
    """
    Perform Durbin-Watson test for autocorrelation.

    Args:
        residuals (pd.Series): Residuals of the model.
    """
    dw_test = durbin_watson(residuals)
    print("\nDurbin-Watson Test for Autocorrelation:")
    print(f"  Durbin-Watson test statistic: {dw_test:.6f}")
    if dw_test < 1.5:
        print("  Interpretation: Positive autocorrelation is likely present "
              "in the residuals.")
    elif dw_test > 2.5:
        print("  Interpretation: Negative autocorrelation is likely present "
              "in the residuals.")
    else:
        print("  Interpretation: There is no significant autocorrelation in "
              "the residuals.")
