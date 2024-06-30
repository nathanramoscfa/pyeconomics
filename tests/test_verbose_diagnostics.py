# tests/test_verbose_diagnostics.py

import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch
from statsmodels.genmod.generalized_linear_model import GLMResultsWrapper
from statsmodels.regression.linear_model import RegressionResultsWrapper, OLS

from pyeconomics.diagnostics.verbose_diagnostics import (
    verbose_model_diagnostics, get_residuals, run_breusch_pagan_test,
    run_durbin_watson_test, run_vif_test, run_ramsey_reset_test,
    run_jarque_bera_test
)


@pytest.fixture
def mock_model():
    model = MagicMock(spec=RegressionResultsWrapper)
    model.resid = pd.Series(np.random.normal(0, 1, 100))
    model.nobs = 100
    model.params = MagicMock()
    model.params.index = ['const', 'predictor']

    # Mock the model's internal model representation
    internal_model = MagicMock(spec=OLS)

    # Mock the data attribute within the internal model
    data_mock = MagicMock()
    data_mock.endog = np.random.normal(0, 1, 100)
    internal_model.data = data_mock

    # Continue setting other necessary attributes
    internal_model.exog = np.random.normal(0, 1, (100, 2))
    internal_model.k_constant = 1

    # Create a new mock for the fit method's return value
    fit_result = MagicMock(spec=RegressionResultsWrapper)
    fit_result.resid = model.resid

    # Mock the fit method on the internal model to return the fit_result mock
    internal_model.fit = MagicMock(return_value=fit_result)

    model.model = internal_model
    model.fittedvalues = np.random.normal(0, 1, 100)
    model.fit = MagicMock(return_value=fit_result)
    model.get_influence = MagicMock()  # Add a mock get_influence method

    return model


@pytest.fixture
def mock_glm_model():
    model = MagicMock(spec=GLMResultsWrapper)
    model.resid_deviance = pd.Series(np.random.normal(0, 1, 100))
    model.nobs = 100
    model.params = MagicMock()
    model.params.index = ['const', 'predictor']
    return model


@pytest.fixture
def mock_exog():
    return pd.DataFrame({
        'const': np.ones(100),
        'x1': np.random.normal(0, 1, 100),
        'x2': np.random.normal(0, 1, 100)
    })


@patch('pyeconomics.diagnostics.verbose_diagnostics.breusch_pagan_test')
def test_run_breusch_pagan_test(mock_breusch_pagan_test, mock_model, mock_exog):
    run_breusch_pagan_test(mock_model, mock_exog)
    mock_breusch_pagan_test.assert_called_once()


@patch('pyeconomics.diagnostics.verbose_diagnostics.durbin_watson_test')
def test_run_durbin_watson_test(mock_durbin_watson_test, mock_model):
    run_durbin_watson_test(mock_model)
    mock_durbin_watson_test.assert_called_once()


@patch('pyeconomics.diagnostics.verbose_diagnostics.'
       'variance_inflation_factor_test')
def test_run_vif_test(mock_vif_test, mock_exog):
    run_vif_test(mock_exog)
    mock_vif_test.assert_called_once()


@patch('pyeconomics.diagnostics.verbose_diagnostics.ramsey_reset_test')
def test_run_ramsey_reset_test(mock_ramsey_reset_test, mock_model):
    run_ramsey_reset_test(mock_model)
    mock_ramsey_reset_test.assert_called_once()


@patch('pyeconomics.diagnostics.verbose_diagnostics.jarque_bera_test')
def test_run_jarque_bera_test(mock_jarque_bera_test, mock_model):
    run_jarque_bera_test(mock_model)
    mock_jarque_bera_test.assert_called_once()


def test_get_residuals(mock_model, mock_glm_model):
    assert get_residuals(mock_model) is mock_model.resid
    assert get_residuals(mock_glm_model) is mock_glm_model.resid_deviance


@patch('pyeconomics.diagnostics.verbose_diagnostics.print_model_summary')
@patch('pyeconomics.diagnostics.verbose_diagnostics.hypothesis_test_slope')
@patch('pyeconomics.diagnostics.verbose_diagnostics.normality_tests')
@patch('pyeconomics.diagnostics.verbose_diagnostics.plot_residuals')
@patch('pyeconomics.diagnostics.verbose_diagnostics.plot_qq_plot')
@patch('pyeconomics.diagnostics.verbose_diagnostics.plot_residuals_histogram')
@patch('pyeconomics.diagnostics.verbose_diagnostics.plot_residuals_vs_leverage')
@patch('pyeconomics.diagnostics.verbose_diagnostics.'
       'plot_residuals_vs_cooks_distance')
def test_verbose_model_diagnostics(
    mock_plot_residuals_vs_cooks_distance,
    mock_plot_residuals_vs_leverage,
    mock_plot_residuals_histogram,
    mock_plot_qq_plot,
    mock_plot_residuals,
    mock_normality_tests,
    mock_hypothesis_test_slope,
    mock_print_model_summary,
    mock_model,
    mock_exog
):
    verbose_model_diagnostics(mock_model, mock_exog, show_plots=True)

    mock_print_model_summary.assert_called_once_with(mock_model)
    mock_hypothesis_test_slope.assert_called_once_with(
        mock_model, 'predictor', 100
    )
    mock_normality_tests.assert_called_once()
    mock_plot_residuals.assert_called_once()
    mock_plot_qq_plot.assert_called_once()
    mock_plot_residuals_histogram.assert_called_once()
    mock_plot_residuals_vs_leverage.assert_called_once()
    mock_plot_residuals_vs_cooks_distance.assert_called_once()


if __name__ == '__main__':
    pytest.main()
