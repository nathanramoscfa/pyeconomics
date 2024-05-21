# pyeconomics/api/fred_api.py
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from pyeconomics.api.fred_api import FredClient


@pytest.fixture
def mock_fred_series():
    """Fixture for mock FRED series data."""
    date_range = pd.date_range(start='2020-01-01', periods=5, freq='D')
    data = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0], index=date_range)
    return data


@patch('pyeconomics.api.fred_api.Fred')
@patch('pyeconomics.api.fred_api.load_from_cache')
@patch('pyeconomics.api.fred_api.save_to_cache')
def test_fetch_data(mock_save_to_cache, mock_load_from_cache, mock_fred_class,
                    mock_fred_series):
    series_id = 'TEST_SERIES'
    cache_key = f"fred_series_{series_id}"

    # Mock cache miss
    mock_load_from_cache.return_value = None

    # Create a mock instance of Fred and set return value for get_series
    mock_fred_instance = MagicMock()
    mock_fred_instance.get_series.return_value = mock_fred_series
    mock_fred_class.return_value = mock_fred_instance

    client = FredClient(api_key='dummy_api_key')

    # Ensure the client's internal Fred instance is the mock
    client.client = mock_fred_instance

    data = client.fetch_data(series_id)

    # Verify data is fetched and saved to cache
    mock_fred_instance.get_series.assert_called_once_with(series_id)
    mock_save_to_cache.assert_called_once_with(cache_key, mock_fred_series)
    pd.testing.assert_series_equal(data, mock_fred_series)


@patch('pyeconomics.api.fred_api.Fred')
@patch('pyeconomics.api.fred_api.load_from_cache')
def test_fetch_data_cache_hit(mock_load_from_cache, mock_fred,
                              mock_fred_series):
    series_id = 'TEST_SERIES'
    cache_key = f"fred_series_{series_id}"

    # Mock cache hit
    mock_load_from_cache.return_value = mock_fred_series

    client = FredClient(api_key='dummy_api_key')
    data = client.fetch_data(series_id)

    # Verify data is fetched from cache
    mock_load_from_cache.assert_called_once_with(cache_key)
    mock_fred.return_value.get_series.assert_not_called()
    pd.testing.assert_series_equal(data, mock_fred_series)


@patch('pyeconomics.api.fred_api.Fred')
def test_get_latest_value(mock_fred, mock_fred_series):
    series_id = 'TEST_SERIES'
    mock_fred_instance = mock_fred.return_value
    mock_fred_instance.get_series.return_value = mock_fred_series

    client = FredClient(api_key='dummy_api_key')
    latest_value = client.get_latest_value(series_id)

    # Verify the latest value is returned
    assert latest_value == mock_fred_series.iloc[-1]


@patch('pyeconomics.api.fred_api.Fred')
def test_get_historical_value(mock_fred, mock_fred_series):
    series_id = 'TEST_SERIES'
    mock_fred_instance = mock_fred.return_value
    mock_fred_instance.get_series.return_value = mock_fred_series

    client = FredClient(api_key='dummy_api_key')
    historical_value = client.get_historical_value(series_id, periods=-2)

    # Verify the historical value is returned
    assert historical_value == mock_fred_series.iloc[-2]


@patch('pyeconomics.api.fred_api.Fred')
def test_get_series_name(mock_fred):
    series_id = 'TEST_SERIES'
    series_info = {"title": "Test Series Name"}

    # Mock the Fred instance and its get_series_info method
    mock_fred_instance = mock_fred.return_value
    mock_fred_instance.get_series_info.return_value = series_info

    client = FredClient(api_key='dummy_api_key')

    # Assign the mock_fred_instance to the client's Fred instance
    client.client = mock_fred_instance

    series_name = client.get_series_name(series_id)

    # Verify the series name is returned
    assert series_name == series_info["title"]


if __name__ == '__main__':
    pytest.main()
