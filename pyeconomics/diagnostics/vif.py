# pyeconomics/diagnostics/vif.py

import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor


def variance_inflation_factor_test(x: pd.DataFrame) -> None:
    """
    Calculate Variance Inflation Factor (VIF) for multicollinearity.

    Args:
        x (pd.DataFrame): Design matrix including the constant term.
    """
    vif_data = pd.DataFrame()
    vif_data['Feature'] = x.columns
    vif_data['VIF'] = [variance_inflation_factor(x.values, i)
                       for i in range(x.shape[1])]
    print("\nVariance Inflation Factor (VIF) for Multicollinearity:")
    for i, row in vif_data.iterrows():
        print(f"  {row['Feature']}: {row['VIF']:.6f}")
    if vif_data['VIF'].max() > 10:
        print("  Interpretation: High multicollinearity detected among the "
              "predictor variables.")
    else:
        print("  Interpretation: No significant multicollinearity detected "
              "among the predictor variables.")
