# pyeconomics/diagnostics/ramsey_reset.py

import statsmodels.regression.linear_model as sm
from statsmodels.stats.diagnostic import linear_reset


def ramsey_reset_test(model: sm.RegressionResults) -> None:
    """
    Perform Ramsey RESET test for model specification.

    Args:
        model (model: sm.RegressionResults): The fitted statsmodels model.
    """
    reset_test = linear_reset(model, power=2, use_f=True)
    print("\nRamsey RESET Test for Model Specification:")
    print(f"  Ramsey RESET test F-statistic: {reset_test.fvalue:.2f}")
    print(f"  p-value: {reset_test.pvalue:.4f}")
    if reset_test.pvalue < 0.05:
        print("  Interpretation: There might be omitted variables or "
              "incorrect functional form in the model.")
    else:
        print("  Interpretation: No evidence of omitted variables or "
              "incorrect functional form in the model.")
