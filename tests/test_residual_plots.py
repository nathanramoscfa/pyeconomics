# tests/test_residual_plots.py

import pytest
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from unittest.mock import MagicMock
import statsmodels.regression.linear_model as sm
from statsmodels.genmod.generalized_linear_model import GLMResultsWrapper
from pyeconomics.diagnostics.residual_plots import (
    plot_residuals, plot_residuals_histogram, plot_qq_plot,
    plot_residuals_vs_leverage, plot_residuals_vs_cooks_distance
)

# Use the Agg backend for testing plots
plt.switch_backend('Agg')


@pytest.fixture
def mock_model():
    model = MagicMock(spec=sm.RegressionResults)
    model.resid = pd.Series(np.random.normal(0, 1, 100))
    model.get_influence = MagicMock()
    return model


@pytest.fixture
def mock_glm_model():
    model = MagicMock(spec=GLMResultsWrapper)
    model.resid_deviance = pd.Series(np.random.normal(0, 1, 100))
    model.get_influence = MagicMock()
    return model


@pytest.fixture
def mock_exog():
    return pd.DataFrame({
        'const': np.ones(100),
        'x1': np.random.normal(0, 1, 100),
        'x2': np.random.normal(0, 1, 100)
    })


def test_plot_residuals(mock_model, mock_exog):
    plot_residuals(mock_exog, mock_model)


def test_plot_residuals_glm(mock_glm_model, mock_exog):
    plot_residuals(mock_exog, mock_glm_model)


def test_plot_residuals_empty_df(mock_model):
    with pytest.raises(ValueError):
        plot_residuals(pd.DataFrame(), mock_model)


def test_plot_residuals_histogram(mock_model):
    plot_residuals_histogram(mock_model.resid)


def test_plot_qq_plot(mock_model):
    plot_qq_plot(mock_model.resid)


def test_plot_residuals_vs_leverage(mock_model):
    influence = MagicMock()
    influence.hat_matrix_diag = np.random.normal(0, 1, 100)
    mock_model.get_influence.return_value = influence

    plot_residuals_vs_leverage(mock_model, mock_model.resid)


def test_plot_residuals_vs_cooks_distance(mock_model):
    influence = MagicMock()
    influence.cooks_distance = (np.random.normal(0, 1, 100), None)
    mock_model.get_influence.return_value = influence

    plot_residuals_vs_cooks_distance(mock_model)


if __name__ == '__main__':
    pytest.main()
