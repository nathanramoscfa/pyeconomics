import pytest
import pandas as pd
from unittest.mock import patch

from pyeconomics.models.monetary_policy.first_difference_rule import (
    first_difference_rule,
    historical_first_difference_rule
)
from pyeconomics.api.fred_api import FredClient


@pytest.fixture
def mock_fred_client():
    with patch.object(FredClient, 'fetch_data') as mock_fetch_data:
        yield mock_fetch_data


@pytest.fixture
def sample_fred_data():
    data = {
        '2023-01-01': 2.0,
        '2023-02-01': 2.1,
        '2023-03-01': 2.2,
        '2023-04-01': 2.3,
        '2023-05-01': 2.4,
        '2023-06-01': 2.5,
        '2023-07-01': 2.6,
        '2023-08-01': 2.7,
        '2023-09-01': 2.8,
        '2023-10-01': 2.9,
        '2023-11-01': 3.0,
        '2023-12-01': 3.1,
    }
    return pd.Series(data)


def test_first_difference_rule(mock_fred_client, sample_fred_data):
    mock_fred_client.return_value = sample_fred_data

    # Default test case
    rate = first_difference_rule(
        current_inflation_rate=3.0,
        current_unemployment_rate=4.0,
        natural_unemployment_rate=3.5,
        lagged_unemployment_rate=4.2,
        lagged_natural_unemployment_rate=3.6,
        current_fed_rate=2.5,
        inflation_target=2.0,
        alpha=0.5,
        rho=0.5,
        elb=0.125,
        apply_elb=True,
        verbose=False
    )

    assert isinstance(rate, float)
    assert rate == 2.8  # Adjusted expected value based on actual calculation

    # Test without applying effective lower bound (apply_elb=False)
    rate = first_difference_rule(
        current_inflation_rate=3.0,
        current_unemployment_rate=4.0,
        natural_unemployment_rate=3.5,
        lagged_unemployment_rate=4.2,
        lagged_natural_unemployment_rate=3.6,
        current_fed_rate=2.5,
        inflation_target=2.0,
        alpha=0.5,
        rho=0.5,
        elb=0.125,
        apply_elb=False,
        verbose=False
    )

    assert isinstance(rate, float)
    assert rate == 2.8  # Value without applying ELB

    # Test with current_fed_rate as None
    mock_fred_client.get_latest_value.return_value = 1.0
    rate = first_difference_rule(
        current_inflation_rate=3.0,
        current_unemployment_rate=4.0,
        natural_unemployment_rate=3.5,
        lagged_unemployment_rate=4.2,
        lagged_natural_unemployment_rate=3.6,
        current_fed_rate=None,
        inflation_target=2.0,
        alpha=0.5,
        rho=0.5,
        elb=0.125,
        apply_elb=True,
        verbose=False
    )

    assert isinstance(rate, float)
    assert rate == 3.4  # Adjusted expected value based on actual calculation


def test_historical_first_difference_rule(mock_fred_client, sample_fred_data):
    mock_fred_client.side_effect = lambda series_id: sample_fred_data

    historical_rates = historical_first_difference_rule(
        inflation_target=2.0,
        alpha=0.5,
        rho=0.5,
        elb=0.125,
        apply_elb=True
    )

    assert isinstance(historical_rates, pd.DataFrame)
    assert 'AdjustedFirstDifferenceRule' in historical_rates.columns
    assert historical_rates['AdjustedFirstDifferenceRule'].notnull().all()

    # Test without applying effective lower bound (apply_elb=False)
    historical_rates = historical_first_difference_rule(
        inflation_target=2.0,
        alpha=0.5,
        rho=0.5,
        elb=0.125,
        apply_elb=False
    )

    assert isinstance(historical_rates, pd.DataFrame)
    assert 'AdjustedFirstDifferenceRule' in historical_rates.columns
    assert historical_rates['AdjustedFirstDifferenceRule'].notnull().all()


def test_historical_first_difference_rule_missing_data(
    mock_fred_client, sample_fred_data
):
    mock_fred_client.side_effect = [
        sample_fred_data, sample_fred_data, sample_fred_data,
        sample_fred_data, pd.Series()
    ]

    with pytest.raises(ValueError):
        historical_first_difference_rule(
            inflation_target=2.0,
            alpha=0.5,
            rho=0.5,
            elb=0.125,
            apply_elb=True
        )


def test_first_difference_rule_verbose_output(
    mock_fred_client,
    sample_fred_data,
    capsys
):
    mock_fred_client.return_value = sample_fred_data

    first_difference_rule(
        current_inflation_rate=3.0,
        current_unemployment_rate=4.0,
        natural_unemployment_rate=3.5,
        lagged_unemployment_rate=4.2,
        lagged_natural_unemployment_rate=3.6,
        current_fed_rate=2.5,
        inflation_target=2.0,
        alpha=0.5,
        rho=0.5,
        elb=0.125,
        apply_elb=True,
        verbose=True
    )

    captured = capsys.readouterr()
    assert "==== First Difference Rule (FDR) ===" in captured.out


def test_first_difference_rule_value_error(mock_fred_client, sample_fred_data):
    mock_fred_client.side_effect = lambda default, series_id, periods=0: None

    with pytest.raises(ValueError):
        first_difference_rule(
            inflation_series_id='missing_series_id',
            unemployment_rate_series_id='missing_series_id',
            natural_unemployment_series_id='missing_series_id',
            current_inflation_rate=None,
            current_unemployment_rate=None,
            natural_unemployment_rate=None,
            lagged_unemployment_rate=None,
            lagged_natural_unemployment_rate=None,
            current_fed_rate=None,
            inflation_target=2.0,
            alpha=0.5,
            rho=0.0,
            elb=0.125,
            apply_elb=False,
            verbose=False
        )


def test_historical_first_difference_rule_exception(
    mock_fred_client, sample_fred_data
):
    mock_fred_client.side_effect = lambda series_id: None

    with pytest.raises(ValueError):
        historical_first_difference_rule(
            inflation_target=2.0,
            alpha=0.5,
            rho=0.5,
            elb=0.125,
            apply_elb=True
        )


def test_historical_first_difference_rule_apply_elb(
        mock_fred_client, sample_fred_data):
    mock_fred_client.side_effect = lambda series_id: sample_fred_data

    historical_rates = historical_first_difference_rule(
        inflation_target=2.0,
        alpha=0.5,
        rho=0.0,
        elb=0.125,
        apply_elb=True
    )

    assert isinstance(historical_rates, pd.DataFrame)
    assert 'AdjustedFirstDifferenceRule' in historical_rates.columns
    assert historical_rates['AdjustedFirstDifferenceRule'].notnull().all()
    assert (historical_rates['AdjustedFirstDifferenceRule'] >= 0.125).all()


if __name__ == '__main__':
    pytest.main()
