# tests/test_durbin_watson.py

import pytest
import pandas as pd
from unittest.mock import patch

from pyeconomics.diagnostics.durbin_watson import durbin_watson_test


@pytest.fixture
def mock_durbin_watson():
    with patch('pyeconomics.diagnostics.durbin_watson.durbin_watson') as mock:
        yield mock


def test_durbin_watson_test_positive_autocorrelation(
    mock_durbin_watson, capsys
):
    mock_durbin_watson.return_value = 1.0

    residuals = pd.Series([1, -1, 2, -2, 3, -3])

    durbin_watson_test(residuals)

    captured = capsys.readouterr()
    assert "Durbin-Watson Test for Autocorrelation:" in captured.out
    assert "Durbin-Watson test statistic: 1.000000" in captured.out
    assert ("Interpretation: Positive autocorrelation is likely present" in
            captured.out)


def test_durbin_watson_test_no_autocorrelation(mock_durbin_watson, capsys):
    mock_durbin_watson.return_value = 2.0

    residuals = pd.Series([1, -1, 2, -2, 3, -3])

    durbin_watson_test(residuals)

    captured = capsys.readouterr()
    assert "Durbin-Watson Test for Autocorrelation:" in captured.out
    assert "Durbin-Watson test statistic: 2.000000" in captured.out
    assert ("Interpretation: There is no significant autocorrelation in the "
            "residuals.") in captured.out


def test_durbin_watson_test_negative_autocorrelation(
    mock_durbin_watson, capsys
):
    mock_durbin_watson.return_value = 3.0

    residuals = pd.Series([1, -1, 2, -2, 3, -3])

    durbin_watson_test(residuals)

    captured = capsys.readouterr()
    assert "Durbin-Watson Test for Autocorrelation:" in captured.out
    assert "Durbin-Watson test statistic: 3.000000" in captured.out
    assert ("Interpretation: Negative autocorrelation is likely present" in
            captured.out)


if __name__ == '__main__':
    pytest.main()
