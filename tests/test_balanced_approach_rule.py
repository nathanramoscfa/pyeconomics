# tests/test_balanced_approach_rule.py

from unittest.mock import patch
import pandas as pd
import pytest

from pyeconomics.data.economic_indicators import EconomicIndicators
from pyeconomics.data.model_parameters import BalancedApproachRuleParameters

from pyeconomics.models.monetary_policy.balanced_approach_rule import (
    balanced_approach_rule,
    historical_balanced_approach_rule,
    plot_historical_bar_basr_rule
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

    indicators = EconomicIndicators(
        inflation_series_id='inflation_rate',
        unemployment_rate_series_id='unemployment_rate',
        natural_unemployment_series_id='natural_unemployment_rate',
        real_interest_rate_series_id='real_interest_rate'
    )

    params = BalancedApproachRuleParameters(
        inflation_target=2.0, alpha=0.5, beta=2.0,
        rho=0.0, elb=0.125, apply_elb=False,
        use_shortfalls_rule=False, verbose=False
    )

    # Default test case
    result = balanced_approach_rule(indicators, params)
    expected_result = 4.75  # Computed based on the mock data and parameters
    assert result == expected_result

    # Test with apply_elb = True
    params.apply_elb = True
    result = balanced_approach_rule(indicators, params)
    expected_result = max(4.75, 0.125)
    assert result == expected_result

    # Test with use_shortfalls_rule = True
    params.use_shortfalls_rule = True
    params.apply_elb = False
    result = balanced_approach_rule(indicators, params)
    expected_result = 3.75  # Change as the gap is negative (shortfall)
    assert result == expected_result

    # Test with verbose output
    with patch('pyeconomics.models.monetary_policy.balanced_approach_rule.'
               'verbose_balanced_approach_rule') as mock_verbose:
        params.verbose = True
        balanced_approach_rule(indicators, params)
        assert mock_verbose.called

    # Test ValueError raise condition
    with pytest.raises(ValueError):
        invalid_indicators = EconomicIndicators(
            inflation_series_id='missing_series_id',
            unemployment_rate_series_id='missing_series_id',
            natural_unemployment_series_id='missing_series_id',
            real_interest_rate_series_id='missing_series_id'
        )
        balanced_approach_rule(invalid_indicators, params)

    # Test with current_fed_rate as None
    mock_fred_client.get_latest_value.return_value = 1.0
    indicators.current_fed_rate = None
    params.verbose = False
    result = balanced_approach_rule(indicators, params)
    expected_result = 3.75  # Computed based on the mock data and parameters
    assert result == expected_result

    # Test with current_fed_rate provided
    indicators.current_fed_rate = 2.0
    result = balanced_approach_rule(indicators, params)
    expected_result = 3.75  # Computed based on the mock data and parameters
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

    indicators = EconomicIndicators(
        inflation_series_id='inflation_rate',
        unemployment_rate_series_id='unemployment_rate',
        natural_unemployment_series_id='natural_unemployment_rate',
        real_interest_rate_series_id='real_interest_rate'
    )

    params = BalancedApproachRuleParameters(
        inflation_target=2.0, alpha=0.5, beta=2.0,
        rho=0.0, elb=0.125, apply_elb=False,
        use_shortfalls_rule=False, verbose=False
    )

    # Default test case
    result = historical_balanced_approach_rule(indicators, params)

    # Verify the shape and content of the result DataFrame
    assert not result.empty
    assert all(result['BalancedApproachRule'] == 4.75)  # Based on mock data

    # Test with apply_elb = True
    params.apply_elb = True
    result = historical_balanced_approach_rule(indicators, params)
    assert not result.empty
    assert all(result['AdjustedBalancedApproachRule'] == max(4.75, 0.125))

    # Test with use_shortfalls_rule = True
    params.apply_elb = False
    params.use_shortfalls_rule = True
    result = historical_balanced_approach_rule(indicators, params)
    assert not result.empty
    assert all(
        result['BalancedApproachShortfallsRule'] == 3.75)  # Based on mock data


@patch('pyeconomics.models.monetary_policy.balanced_approach_rule.plt.show')
def test_plot_historical_bar_basr_rule(mock_show):
    historical_rates = pd.DataFrame({
        'BalancedApproachRule': [3.0, 3.1],
        'BalancedApproachShortfallsRule': [2.7, 2.8],
        'AdjustedBalancedApproachRule': [3.2, 3.3],
        'AdjustedBalancedApproachShortfallsRule': [2.9, 3.0],
        'FedRate': [2.0, 2.1]
    }, index=pd.to_datetime(['2020-01-01', '2020-02-01']))

    # Test unadjusted plot
    plot_historical_bar_basr_rule(historical_rates, adjusted=False)
    assert mock_show.called

    # Test adjusted plot
    plot_historical_bar_basr_rule(historical_rates, adjusted=True)
    assert mock_show.called


if __name__ == '__main__':
    pytest.main()
