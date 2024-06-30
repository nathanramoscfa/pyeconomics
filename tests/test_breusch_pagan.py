# tests/test_breusch_pagan.py

import pytest
import pandas as pd
from unittest.mock import patch

from pyeconomics.diagnostics.breusch_pagan import breusch_pagan_test


@pytest.fixture
def mock_het_breuschpagan():
    with (patch('pyeconomics.diagnostics.breusch_pagan.het_breuschpagan') as
          mock):
        yield mock


def test_breusch_pagan_test_positive(mock_het_breuschpagan, capsys):
    mock_het_breuschpagan.return_value = (10.5, 0.002, 9.3, 0.003)

    residuals = pd.Series([1, -1, 2, -2, 3, -3])
    exog = pd.DataFrame({
        'const': [1, 1, 1, 1, 1, 1],
        'x1': [10, 20, 30, 40, 50, 60]
    })

    breusch_pagan_test(residuals, exog)

    captured = capsys.readouterr()
    assert "Breusch-Pagan Test for Heteroskedasticity:" in captured.out
    assert "Lagrange multiplier statistic: 1.050e+01" in captured.out
    assert "p-value: 2.000e-03" in captured.out
    assert "f-value: 9.300e+00" in captured.out
    assert "f p-value: 3.000e-03" in captured.out
    assert ("Interpretation: There is evidence of heteroskedasticity" in
            captured.out)


def test_breusch_pagan_test_negative(mock_het_breuschpagan, capsys):
    mock_het_breuschpagan.return_value = (2.5, 0.12, 1.8, 0.15)

    residuals = pd.Series([1, -1, 2, -2, 3, -3])
    exog = pd.DataFrame({
        'const': [1, 1, 1, 1, 1, 1],
        'x1': [10, 20, 30, 40, 50, 60]
    })

    breusch_pagan_test(residuals, exog)

    captured = capsys.readouterr()
    assert "Breusch-Pagan Test for Heteroskedasticity:" in captured.out
    assert "Lagrange multiplier statistic: 2.500e+00" in captured.out
    assert "p-value: 1.200e-01" in captured.out
    assert "f-value: 1.800e+00" in captured.out
    assert "f p-value: 1.500e-01" in captured.out
    assert "Interpretation: No evidence of heteroskedasticity" in captured.out


if __name__ == '__main__':
    pytest.main()
