# tests/test_ramsey_reset.py

import pytest
from unittest.mock import MagicMock, patch
import statsmodels.regression.linear_model as sm

from pyeconomics.diagnostics.ramsey_reset import ramsey_reset_test


@pytest.fixture
def mock_model():
    model = MagicMock(spec=sm.RegressionResults)
    return model


@pytest.fixture
def mock_linear_reset():
    with patch('pyeconomics.diagnostics.ramsey_reset.linear_reset') as mock:
        yield mock


def test_ramsey_reset_test_significant(mock_model, mock_linear_reset, capsys):
    mock_result = MagicMock()
    mock_result.fvalue = 10.0
    mock_result.pvalue = 0.01
    mock_linear_reset.return_value = mock_result

    ramsey_reset_test(mock_model)

    captured = capsys.readouterr()
    assert "Ramsey RESET Test for Model Specification:" in captured.out
    assert "Ramsey RESET test F-statistic: 10.00" in captured.out
    assert "p-value: 0.0100" in captured.out
    assert ("Interpretation: There might be omitted variables or incorrect "
            "functional form in the model.") in captured.out


def test_ramsey_reset_test_not_significant(
    mock_model, mock_linear_reset, capsys
):
    mock_result = MagicMock()
    mock_result.fvalue = 1.0
    mock_result.pvalue = 0.5
    mock_linear_reset.return_value = mock_result

    ramsey_reset_test(mock_model)

    captured = capsys.readouterr()
    assert "Ramsey RESET Test for Model Specification:" in captured.out
    assert "Ramsey RESET test F-statistic: 1.00" in captured.out
    assert "p-value: 0.5000" in captured.out
    assert ("Interpretation: No evidence of omitted variables or incorrect "
            "functional form in the model.") in captured.out


if __name__ == '__main__':
    pytest.main()
