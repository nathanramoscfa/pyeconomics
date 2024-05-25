from unittest.mock import patch

import pandas as pd
import pytest

from pyeconomics.models.monetary_policy.balanced_approach_rule import (
    balanced_approach_rule, historical_balanced_approach_rule
)


@pytest.fixture
def mock_fred_data():
    """Fixture for mock FRED data."""
    return {
        'inflation_rate': 2.5,
        'unemployment_rate': 4.0,
        'natural_unemployment_rate': 4.5,
        'real_interest_rate': 1.0,
        'current_fed_rate': 0.5
    }


@patch('pyeconomics.models.monetary_policy.balanced_approach_rule.fred_client')
def test_balanced_approach_rule(mock_fred_client, mock_fred_data):
    mock_fred_client.get_data_or_fetch.side_effect = (
        lambda default, series_id, periods=0: mock_fred_data.get(series_id)
    )
    mock_fred_client.get_latest_value.return_value = (
        mock_fred_data['current_fed_rate']
    )

    # Default test case
    result = balanced_approach_rule(
        inflation_series_id='inflation_rate',
        unemployment_rate_series_id='unemployment_rate',
        natural_unemployment_series_id='natural_unemployment_rate',
        real_interest_rate_series_id='real_interest_rate',
        inflation_target=2.0, alpha=0.5, beta=2.0,
        rho=0.0, apply_elb=False,
        use_shortfalls_rule=False)
    expected_result = 4.75  # Computed based on the mock data and parameters
    assert result == expected_result

    # Test with apply_elb = True
    result = balanced_approach_rule(
        inflation_series_id='inflation_rate',
        unemployment_rate_series_id='unemployment_rate',
        natural_unemployment_series_id='natural_unemployment_rate',
        real_interest_rate_series_id='real_interest_rate',
        inflation_target=2.0, alpha=0.5, beta=2.0,
        rho=0.0, apply_elb=True,
        use_shortfalls_rule=False)
    expected_result = max(4.75, 0.125)
    assert result == expected_result

    # Test with use_shortfalls_rule = True
    result = balanced_approach_rule(
        inflation_series_id='inflation_rate',
        unemployment_rate_series_id='unemployment_rate',
        natural_unemployment_series_id='natural_unemployment_rate',
        real_interest_rate_series_id='real_interest_rate',
        inflation_target=2.0, alpha=0.5, beta=2.0,
        rho=0.0, apply_elb=False,
        use_shortfalls_rule=True)
    expected_result = 3.75  # Change as the gap is negative (shortfall)
    assert result == expected_result

    # Test with verbose output
    with patch('pyeconomics.models.monetary_policy.balanced_approach_rule.'
               'verbose_balanced_approach_rule') as mock_verbose:
        balanced_approach_rule(
            inflation_series_id='inflation_rate',
            unemployment_rate_series_id='unemployment_rate',
            natural_unemployment_series_id='natural_unemployment_rate',
            real_interest_rate_series_id='real_interest_rate',
            inflation_target=2.0, alpha=0.5, beta=2.0,
            rho=0.0, apply_elb=False,
            use_shortfalls_rule=False,
            verbose=True)
        assert mock_verbose.called

    # Test ValueError raise condition
    with pytest.raises(ValueError):
        balanced_approach_rule(
            inflation_series_id='missing_series_id',
            unemployment_rate_series_id='missing_series_id',
            natural_unemployment_series_id='missing_series_id',
            real_interest_rate_series_id='missing_series_id',
            inflation_target=2.0, alpha=0.5, beta=2.0,
            rho=0.0, apply_elb=False,
            use_shortfalls_rule=False)

    # Test with current_fed_rate as None
    mock_fred_client.get_latest_value.return_value = 1.0
    result = balanced_approach_rule(
        inflation_series_id='inflation_rate',
        unemployment_rate_series_id='unemployment_rate',
        natural_unemployment_series_id='natural_unemployment_rate',
        real_interest_rate_series_id='real_interest_rate',
        inflation_target=2.0, alpha=0.5, beta=2.0,
        rho=0.0, apply_elb=False,
        current_fed_rate=None
    )
    expected_result = 4.75  # Computed based on the mock data and parameters
    assert result == expected_result


@patch('pyeconomics.models.monetary_policy.balanced_approach_rule.fred_client')
@patch(
    'pyeconomics.models.monetary_policy.'
    'balanced_approach_rule.fetch_historical_fed_funds_rate'
)
def test_historical_balanced_approach_rule(
    mock_fetch_historical_fed_funds_rate,
    mock_fred_client,
    mock_fred_data
):
    mock_fred_client.fetch_data.side_effect = (
        lambda series_id: pd.Series([mock_fred_data[series_id]] * 10)
    )
    mock_fetch_historical_fed_funds_rate.return_value = (
        pd.Series([mock_fred_data['current_fed_rate']] * 10)
    )

    # Default test case
    result = historical_balanced_approach_rule(
        inflation_series_id='inflation_rate',
        unemployment_rate_series_id='unemployment_rate',
        natural_unemployment_series_id='natural_unemployment_rate',
        real_interest_rate_series_id='real_interest_rate',
        inflation_target=2.0,
        alpha=0.5,
        beta=2.0,
        rho=0.0,
        apply_elb=False,
        use_shortfalls_rule=False
    )

    # Verify the shape and content of the result DataFrame
    assert not result.empty
    assert all(result['BalancedApproachRule'] == 4.75)  # Based on mock data

    # Test with apply_elb = True
    result = historical_balanced_approach_rule(
        inflation_series_id='inflation_rate',
        unemployment_rate_series_id='unemployment_rate',
        natural_unemployment_series_id='natural_unemployment_rate',
        real_interest_rate_series_id='real_interest_rate',
        inflation_target=2.0,
        alpha=0.5,
        beta=2.0,
        rho=0.0,
        apply_elb=True,
        use_shortfalls_rule=False
    )

    assert not result.empty
    assert all(result['AdjustedBalancedApproachRule'] == max(4.75, 0.125))

    # Test with use_shortfalls_rule = True
    result = historical_balanced_approach_rule(
        inflation_series_id='inflation_rate',
        unemployment_rate_series_id='unemployment_rate',
        natural_unemployment_series_id='natural_unemployment_rate',
        real_interest_rate_series_id='real_interest_rate',
        inflation_target=2.0,
        alpha=0.5,
        beta=2.0,
        rho=0.0,
        apply_elb=False,
        use_shortfalls_rule=True
    )

    assert not result.empty
    assert all(
        result['BalancedApproachShortfallsRule'] == 3.75)  # Based on mock data


if __name__ == '__main__':
    pytest.main()
