# pyeconomics/diagnostics/residual_plots.py

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.stats as stats
from scipy.stats import norm
from statsmodels.genmod.generalized_linear_model import GLMResultsWrapper
import statsmodels.regression.linear_model as sm
from typing import Any


def plot_residuals(exog: pd.DataFrame, model: sm.RegressionResults) -> None:
    """
    Plot the residuals of the model against all predictor variables in the
    DataFrame.

    Args:
        exog (pd.DataFrame): DataFrame containing the exogenous variables.
        model (sm.RegressionResults): The fitted statsmodels model.
    """
    if not isinstance(exog, pd.DataFrame) or exog.empty:
        raise ValueError("Input 'df_exog' is not a valid non-empty DataFrame.")

    residuals = model.resid_deviance if (
        isinstance(model, GLMResultsWrapper)
    ) else model.resid
    num_plots = exog.shape[1]

    if num_plots == 0:
        raise ValueError("The DataFrame does not contain any columns.")

    fig, axs = plt.subplots(
        max(1, num_plots), 1, figsize=(5, 3 * max(1, num_plots))
    )
    axs = axs.flatten() if num_plots > 1 else [axs]

    for ax, column in zip(axs, exog.columns[1:]):
        ax.scatter(exog[column], residuals, alpha=0.5)
        ax.set_xlabel(f'Log Predictor: {column}')
        ax.set_ylabel('Residuals')
        ax.set_title(f'Residual Plot for {column}')
        ax.axhline(0, color='red', linestyle='--')
        ax.grid(True)

    plt.tight_layout()
    plt.show()


def plot_residuals_histogram(residuals: pd.Series) -> None:
    """
    Plot the histogram of the residuals with an overlaid normal distribution.

    Args:
        residuals (pd.Series): Residuals of the model.
    """
    plt.figure(figsize=(5, 3))

    # Plot histogram of residuals
    plt.hist(residuals, bins=30, density=True, edgecolor='black', alpha=0.6)

    # Fit a normal distribution to the data
    mu, std = norm.fit(residuals)

    # Plot the normal distribution
    xmin, xmax = plt.xlim()
    x = np.linspace(xmin, xmax, 100)
    p = norm.pdf(x, mu, std)

    plt.plot(x, p, 'k', linewidth=2)
    plt.xlabel('Residuals')
    plt.ylabel('Frequency')
    plt.title('Histogram of Residuals with Normal Distribution')

    plt.show()


def plot_qq_plot(residuals: pd.Series) -> None:
    """
    Plot the Q-Q plot of the residuals.

    Args:
        residuals (pd.Series): Residuals of the model.
    """
    plt.figure(figsize=(5, 3))
    stats.probplot(residuals, dist='norm', plot=plt)
    plt.title('Q-Q Plot of Residuals')
    plt.show()


def plot_residuals_vs_leverage(
    model: Any,
    residuals: pd.Series
) -> None:
    """
    Plot residuals vs leverage.

    Args:
        model (Any): The fitted statsmodels model.
        residuals (pd.Series): Residuals of the model.
    """
    influence = model.get_influence()
    leverage = influence.hat_matrix_diag

    plt.figure(figsize=(5, 3))
    plt.scatter(leverage, residuals, alpha=0.5)
    plt.title('Residuals vs Leverage')
    plt.xlabel('Leverage')
    plt.ylabel('Residuals')
    plt.axhline(0, linestyle='--', color='red')
    plt.xticks(rotation=45)
    plt.show()


def plot_residuals_vs_cooks_distance(model: Any) -> None:
    """
    Plot residuals vs Cook's distance.

    Args:
        model (Any): The fitted statsmodels model.
    """
    influence = model.get_influence()
    cooks_d2 = influence.cooks_distance[0]

    plt.figure(figsize=(5, 3))
    plt.scatter(range(len(cooks_d2)), cooks_d2, alpha=0.5)
    plt.title("Cook's Distance")
    plt.xlabel('Observation')
    plt.ylabel("Cook's Distance")
    plt.axhline(4 / len(cooks_d2), linestyle='--', color='red')
    plt.show()
