# pyeconomics/diagnostics/summary.py

import statsmodels.regression.linear_model as sm


def print_model_summary(model: sm.RegressionResults) -> None:
    """
    Print the summary of the fitted ai_model.

    Args:
        model (sm.RegressionResults): The fitted statsmodels ai_model.
    """
    print(model.summary())
