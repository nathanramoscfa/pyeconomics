# pyeconomics/diagnostics/verbose_diagnostics.py

from typing import Any
from statsmodels.genmod.generalized_linear_model import GLMResultsWrapper
from .breusch_pagan import breusch_pagan_test
from .durbin_watson import durbin_watson_test
from .hypothesis_test import hypothesis_test_slope
from .normality_tests import jarque_bera_test, normality_tests
from .ramsey_reset import ramsey_reset_test
from .residual_plots import (plot_residuals, plot_qq_plot,
                             plot_residuals_histogram,
                             plot_residuals_vs_leverage,
                             plot_residuals_vs_cooks_distance)
from .summary import print_model_summary
from .vif import variance_inflation_factor_test


def run_breusch_pagan_test(model: Any, exog: Any) -> None:
    """
    Run Breusch-Pagan test for heteroskedasticity.

    Args:
        model (Any): The fitted statsmodels model.
        exog (Any): Exogenous variables used in the model.
    """
    residuals = get_residuals(model)
    breusch_pagan_test(residuals, exog)


def run_durbin_watson_test(model: Any) -> None:
    """
    Run Durbin-Watson test for autocorrelation.

    Args:
        model (Any): The fitted statsmodels model.
    """
    residuals = get_residuals(model)
    durbin_watson_test(residuals)


def run_vif_test(exog: Any) -> None:
    """
    Run Variance Inflation Factor (VIF) test for multicollinearity.

    Args:
        exog (Any): Exogenous variables used in the model.
    """
    variance_inflation_factor_test(exog)


def run_ramsey_reset_test(model: Any) -> None:
    """
    Run Ramsey RESET test for model specification.

    Args:
        model (Any): The fitted statsmodels model.
    """
    ramsey_reset_test(model)


def run_jarque_bera_test(model: Any) -> None:
    """
    Run Jarque-Bera test for normality of residuals.

    Args:
        model (Any): The fitted statsmodels model.
    """
    residuals = get_residuals(model)
    jarque_bera_test(residuals)


def get_residuals(model: Any) -> Any:
    """
    Get residuals from the model.

    Args:
        model (Any): The fitted statsmodels model.

    Returns:
        Any: Residuals of the model.
    """
    if isinstance(model, GLMResultsWrapper):
        return model.resid_deviance
    return model.resid


def verbose_model_diagnostics(
    model: Any,
    exog: Any,
    show_plots: bool = False
) -> None:
    """
    Print verbose output for the model diagnostics.

    Args:
        model (Any): The fitted statsmodels model.
        exog (Any): Exogenous variables used in the model.
        show_plots (bool): Whether to display diagnostic plots.
    """
    print("\n==== Model Diagnostics ==========================================="
          "============")

    # Print model summary
    print_model_summary(model)

    # Perform and print diagnostics
    n = model.nobs
    param = model.params.index[1]
    hypothesis_test_slope(model, param, n)

    # Perform diagnostic tests
    run_breusch_pagan_test(model, exog)
    run_durbin_watson_test(model)
    run_vif_test(exog)
    run_ramsey_reset_test(model)
    normality_tests(get_residuals(model))

    print()
    print('=' * 78)
    print()

    # Plot diagnostic plots
    if show_plots:
        plot_residuals(exog, model)
        plot_qq_plot(get_residuals(model))
        plot_residuals_histogram(get_residuals(model))

        # Check if the model has the get_influence method
        if hasattr(model, 'get_influence'):
            plot_residuals_vs_leverage(model, get_residuals(model))
            plot_residuals_vs_cooks_distance(model)
        else:
            print("Model does not support influence measures.")
