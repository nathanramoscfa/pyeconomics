# tests/test_vif.py

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch
from pyeconomics.diagnostics.vif import variance_inflation_factor_test


@pytest.fixture
def mock_data():
    np.random.seed(0)
    data = pd.DataFrame({
        'const': np.ones(100),
        'x1': np.random.normal(0, 1, 100),
        'x2': np.random.normal(0, 1, 100),
    })
    return data


@patch('builtins.print')
def test_variance_inflation_factor_test(mock_print, mock_data):
    variance_inflation_factor_test(mock_data)
    assert mock_print.call_count == 5
    # Verify the calls to print the VIFs and interpretation
    mock_print.assert_any_call(
        "\nVariance Inflation Factor (VIF) for Multicollinearity:")

    calls = [call[0][0] for call in mock_print.call_args_list]
    const_vif = [call for call in calls if call.startswith("  const:")][0]
    x1_vif = [call for call in calls if call.startswith("  x1:")][0]
    x2_vif = [call for call in calls if call.startswith("  x2:")][0]

    assert const_vif.startswith("  const:")
    assert x1_vif.startswith("  x1:")
    assert x2_vif.startswith("  x2:")

    const_vif_value = float(const_vif.split(": ")[1])
    x1_vif_value = float(x1_vif.split(": ")[1])
    x2_vif_value = float(x2_vif.split(": ")[1])

    assert const_vif_value == pytest.approx(1.009, rel=1e-2)
    assert x1_vif_value == pytest.approx(1.009, rel=1e-2)
    assert x2_vif_value == pytest.approx(1.009, rel=1e-2)

    mock_print.assert_any_call(
        "  Interpretation: No significant multicollinearity detected "
        "among the predictor variables.")


if __name__ == '__main__':
    pytest.main()
