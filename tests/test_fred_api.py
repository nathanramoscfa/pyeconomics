# tests/test_fred_api.py
import datetime
import pytest
from unittest.mock import patch

import pandas as pd

from pyeconomics.api.fred_api import FredClient


@pytest.fixture(scope='module')
def fred_client():
    FredClient.reset_instance()
    api_key = 'test_api_key'
    return FredClient(api_key)


def test_singleton_pattern(fred_client):
    """
    Test to ensure FredClient follows the singleton pattern.
    """
    with patch.object(FredClient, '__new__', return_value=fred_client):
        another_instance = FredClient()
        assert fred_client is another_instance


def test_fetch_data_from_cache(fred_client):
    with patch('pyeconomics.api.fred_api.load_from_cache') as mock_load_cache:
        series_id = 'GDP'
        expected_data = pd.Series([1, 2, 3], name=series_id)
        mock_load_cache.return_value = expected_data

        data = fred_client.fetch_data(series_id)
        assert data.equals(expected_data)
        mock_load_cache.assert_called_once_with(f'fred_series_{series_id}')


def test_fetch_data_from_api(fred_client):
    with patch('pyeconomics.api.fred_api.load_from_cache') as mock_load_cache, \
        patch('pyeconomics.api.fred_api.save_to_cache') as mock_save_cache, \
            patch.object(fred_client.client, 'get_series') as mock_get_series:
        mock_load_cache.return_value = None
        series_id = 'GDP'
        expected_data = pd.Series([1, 2, 3], name=series_id)
        mock_get_series.return_value = expected_data

        data = fred_client.fetch_data(series_id)
        assert data.equals(expected_data)
        mock_get_series.assert_called_once_with(series_id)
        mock_save_cache.assert_called_once_with(f'fred_series_{series_id}',
                                                expected_data)


def test_get_latest_value(fred_client):
    with patch.object(fred_client, 'fetch_data') as mock_fetch_data:
        series_id = 'GDP'
        today = datetime.date.today()
        data = pd.Series(
            [1, 2, 3],
            index=pd.date_range(end=today, periods=3, freq='D'),
            name=series_id
        )
        mock_fetch_data.return_value = data

        latest_value = fred_client.get_latest_value(series_id)
        assert latest_value == 3


def test_get_historical_value(fred_client):
    with patch.object(fred_client, 'fetch_data') as mock_fetch_data:
        series_id = 'GDP'
        data = pd.Series([1, 2, 3], name=series_id)
        mock_fetch_data.return_value = data

        historical_value = fred_client.get_historical_value(
            series_id, periods=-2)
        assert historical_value == 2


def test_get_series_name(fred_client):
    with patch.object(
            fred_client.client, 'get_series_info'
    ) as mock_get_series_info:
        series_id = 'GDP'
        series_info = {"title": "Gross Domestic Product"}
        mock_get_series_info.return_value = series_info

        series_name = fred_client.get_series_name(series_id)
        assert series_name == "Gross Domestic Product"


def test_get_data_or_fetch(fred_client):
    with (patch.object(
        FredClient, 'get_latest_value'
    ) as mock_get_latest_value, patch.object(
        FredClient, 'get_historical_value'
    ) as mock_get_historical_value):
        series_id = 'GDP'
        default = None
        periods = 0
        expected_value = 3

        mock_get_latest_value.return_value = expected_value
        value = FredClient.get_data_or_fetch(default, series_id, periods)
        assert value == expected_value

        periods = -2
        mock_get_historical_value.return_value = 2
        value = FredClient.get_data_or_fetch(default, series_id, periods)
        assert value == 2


if __name__ == '__main__':
    pytest.main()
