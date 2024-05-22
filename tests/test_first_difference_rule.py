from unittest.mock import patch
import pandas as pd
import pytest
from pyeconomics.models.monetary_policy.first_difference_rule import (
    first_difference_rule,
    historical_first_difference_rule
)


@pytest.fixture
def mock_fred_data():
    """Fixture for mock FRED data."""
    return {
        'PCETRIM12M159SFRBDAL': 2.5,
        'UNRATE': 4.0,
        'NROU': 4.5,
        'lagged_unemployment_rate': 4.2,
        'lagged_natural_unemployment_rate': 4.6,
        'DFEDTARU': 0.5
    }


@patch('pyeconomics.api.fred_api.FredClient.get_data_or_fetch')
@patch('pyeconomics.api.fred_api.FredClient.get_latest_value')
def test_first_difference_rule(mock_get_latest_value, mock_get_data_or_fetch,
                               mock_fred_data):
    mock_get_data_or_fetch.side_effect = lambda default, series, periods=0: (
        mock_fred_data.get(series, default))
    mock_get_latest_value.return_value = mock_fred_data['DFEDTARU']

    result = first_difference_rule(
        inflation_series_id='PCETRIM12M159SFRBDAL',
        unemployment_rate_series_id='UNRATE',
        natural_unemployment_series_id='NROU',
        current_inflation_rate=None,
        current_unemployment_rate=None,
        natural_unemployment_rate=None,
        lagged_unemployment_rate=None,
        lagged_natural_unemployment_rate=None,
        current_fed_rate=None,
        inflation_target=2.0,
        alpha=0.5,
        rho=0.0,
        apply_elb=False
    )

    # Adjust expected result based on the mock data provided
    expected_result = 0.75  # Adjust this value based on the correct calculation
    assert result == expected_result


@patch('pyeconomics.models.monetary_policy.balanced_approach_rule.fred_client')
@patch('pyeconomics.models.monetary_policy.first_difference_rule'
       '.fetch_historical_fed_funds_rate')
def test_historical_first_difference_rule(
        mock_fetch_historical_fed_funds_rate, mock_fetch_data, mock_fred_data):
    mock_fetch_data.side_effect = lambda series: pd.Series(
        [mock_fred_data.get(series, None)] * 12,
        index=pd.date_range('2019-01-01', periods=12, freq='M')
    )
    mock_fetch_historical_fed_funds_rate.return_value = pd.Series(
        [mock_fred_data['DFEDTARU']] * 12,
        index=pd.date_range('2019-01-01', periods=12, freq='M')
    )

    result = historical_first_difference_rule(
        inflation_series_id='PCETRIM12M159SFRBDAL',
        unemployment_rate_series_id='UNRATE',
        natural_unemployment_series_id='NROU',
        inflation_target=2.0,
        alpha=0.5,
        rho=0.0,
        apply_elb=False
    )

    # Verify the shape and content of the result DataFrame
    assert not result.empty
    assert all(result['FirstDifferenceRule'].notna())  # Ensure no NaN values

    # The expected result needs to be based on the mock data provided
    expected_values = [
        0.69, 0.91, 0.72, 0.74, 0.74, 0.8, 0.8, 0.85, 0.85, 0.84, 0.84, 0.46,
        0.46, 0.56, 0.56, 0.64, 0.64, 0.75, 0.75, 0.7, 0.7, 0.7, 0.7
    ]
    assert result['FirstDifferenceRule'].round(2).tolist() == expected_values


if __name__ == '__main__':
    pytest.main()
