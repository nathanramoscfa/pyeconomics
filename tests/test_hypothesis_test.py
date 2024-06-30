# tests/test_hypothesis_test.py

import pytest
from unittest.mock import MagicMock
import statsmodels.regression.linear_model as sm

from pyeconomics.diagnostics.hypothesis_test import hypothesis_test_slope


@pytest.fixture
def mock_model():
    model = MagicMock(spec=sm.RegressionResults)
    model.params = {'predictor': 0.5}
    model.bse = {'predictor': 0.1}
    return model


def test_hypothesis_test_slope_significant(mock_model, capsys):
    n = 100
    hypothesis_test_slope(mock_model, 'predictor', n)

    captured = capsys.readouterr()
    assert "Hypothesis Test for the Slope:" in captured.out
    assert "t-statistic: 5.000000" in captured.out
    assert "p-value: 2.513578e-06" in captured.out
    assert ("Decision: Reject the null hypothesis. The model is statistically "
            "significant.") in captured.out
    assert ("Interpretation: The relationship between the predictor and the "
            "response variable is statistically significant.") in captured.out


def test_hypothesis_test_slope_not_significant(mock_model, capsys):
    mock_model.params['predictor'] = 0.01
    mock_model.bse['predictor'] = 0.1
    n = 100
    hypothesis_test_slope(mock_model, 'predictor', n)

    captured = capsys.readouterr()
    assert "Hypothesis Test for the Slope:" in captured.out
    assert "t-statistic: 0.100000" in captured.out
    assert "p-value: 9.205486e-01" in captured.out
    assert ("Decision: Fail to reject the null hypothesis. The model is not "
            "statistically significant.") in captured.out
    assert (("Interpretation: There is no statistically significant "
            "relationship between the predictor and the response variable.") in
            captured.out)


if __name__ == '__main__':
    pytest.main()
