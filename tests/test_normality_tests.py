# tests/test_normality_tests.py

import pytest
import pandas as pd

from pyeconomics.diagnostics.normality_tests import (
    shapiro_wilk_test, kolmogorov_smirnov_test, anderson_darling_test,
    jarque_bera_test, dagostino_k_squared_test, normality_tests
)


@pytest.fixture
def mock_residuals():
    return pd.Series([1, -1, 2, -2, 3, -3, 4, -4, 5, -5])


def test_shapiro_wilk_test(mock_residuals, capsys):
    shapiro_wilk_test(mock_residuals)

    captured = capsys.readouterr()
    assert "Shapiro-Wilk Test for Normality of Residuals:" in captured.out
    assert "Shapiro-Wilk test statistic:" in captured.out


def test_kolmogorov_smirnov_test(mock_residuals, capsys):
    kolmogorov_smirnov_test(mock_residuals)

    captured = capsys.readouterr()
    assert "Kolmogorov-Smirnov Test for Normality of Residuals:" in captured.out
    assert "Kolmogorov-Smirnov test statistic:" in captured.out


def test_anderson_darling_test(mock_residuals, capsys):
    anderson_darling_test(mock_residuals)

    captured = capsys.readouterr()
    assert "Anderson-Darling Test for Normality of Residuals:" in captured.out
    assert "Anderson-Darling test statistic:" in captured.out
    assert "Significance Level:" in captured.out
    assert "Critical Value:" in captured.out


def test_jarque_bera_test(mock_residuals, capsys):
    jarque_bera_test(mock_residuals)

    captured = capsys.readouterr()
    assert "Jarque-Bera Test for Normality of Residuals:" in captured.out
    assert "Jarque-Bera test statistic:" in captured.out


def test_dagostino_k_squared_test(mock_residuals, capsys):
    dagostino_k_squared_test(mock_residuals)

    captured = capsys.readouterr()
    assert ("D'Agostino's K-squared Test for Normality of Residuals:" in
            captured.out)
    assert "D'Agostino's K-squared test statistic:" in captured.out


def test_normality_tests(mock_residuals, capsys):
    normality_tests(mock_residuals)

    captured = capsys.readouterr()
    assert "Shapiro-Wilk Test for Normality of Residuals:" in captured.out
    assert "Kolmogorov-Smirnov Test for Normality of Residuals:" in captured.out
    assert "Anderson-Darling Test for Normality of Residuals:" in captured.out
    assert "Jarque-Bera Test for Normality of Residuals:" in captured.out
    assert ("D'Agostino's K-squared Test for Normality of Residuals:" in
            captured.out)


if __name__ == '__main__':
    pytest.main()
