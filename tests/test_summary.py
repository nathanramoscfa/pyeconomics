# tests/test_summary.py

import pytest
from unittest.mock import MagicMock, patch
import statsmodels.regression.linear_model as sm

from pyeconomics.diagnostics.summary import print_model_summary


@pytest.fixture
def mock_model():
    model = MagicMock(spec=sm.RegressionResults)
    return model


def test_print_model_summary(mock_model, capsys):
    summary_text = "This is a mock summary."
    mock_model.summary.return_value = summary_text

    print_model_summary(mock_model)

    captured = capsys.readouterr()
    assert summary_text in captured.out


if __name__ == '__main__':
    pytest.main()
