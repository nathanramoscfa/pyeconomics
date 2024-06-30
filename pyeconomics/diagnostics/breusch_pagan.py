# pyeconomics/diagnostics/breusch_pagan.py

import pandas as pd
from statsmodels.stats.diagnostic import het_breuschpagan
from typing import Dict


def breusch_pagan_test(residuals: pd.Series, exog: pd.DataFrame) -> None:
    """
    Perform Breusch-Pagan test for heteroskedasticity.

    Args:
        residuals (pd.Series): Residuals of the model.
        exog (pd.DataFrame): Exogenous variables used in the model.
    """
    lm_stat, lm_pvalue, f_stat, f_pvalue = het_breuschpagan(residuals, exog)
    bp_test_results: Dict[str, float] = {
        'Lagrange multiplier statistic': lm_stat,
        'p-value': lm_pvalue,
        'f-value': f_stat,
        'f p-value': f_pvalue
    }
    print("\nBreusch-Pagan Test for Heteroskedasticity:")
    for k, v in bp_test_results.items():
        print(f"  {k}: {v:.3e}")
    if bp_test_results['p-value'] < 0.05:
        print("  Interpretation: There is evidence of heteroskedasticity "
              "(non-constant variance) in the residuals.")
    else:
        print("  Interpretation: No evidence of heteroskedasticity "
              "(constant variance) in the residuals.")
