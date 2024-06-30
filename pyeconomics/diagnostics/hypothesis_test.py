# pyeconomics/diagnostics/hypothesis_test.py

import numpy as np
from scipy import stats
import statsmodels.regression.linear_model as sm


def hypothesis_test_slope(
    model: sm.RegressionResults,
    predictor: str, n: int
) -> None:
    """
    Perform hypothesis test for the slope of the model.

    Args:
        model (sm.RegressionResults): The fitted statsmodels model.
        predictor (str): The name of the predictor variable.
        n (int): Number of observations.
    """
    slope = model.params[predictor]
    std_err = model.bse[predictor]
    t_statistic = slope / std_err
    df = n - 2
    p_value = 2 * (1 - stats.t.cdf(np.abs(t_statistic), df))
    alpha = 0.05
    print("\nHypothesis Test for the Slope:")
    print(f"  t-statistic: {t_statistic:.6f}")
    print(f"  p-value: {p_value:.6e}")
    if p_value < alpha:
        print("  Decision: Reject the null hypothesis. The model is "
              "statistically significant.")
        print("  Interpretation: The relationship between the predictor and "
              "the response variable is statistically significant.")
    else:
        print("  Decision: Fail to reject the null hypothesis. The model is "
              "not statistically significant.")
        print("  Interpretation: There is no statistically significant "
              "relationship between the predictor and the response variable.")
