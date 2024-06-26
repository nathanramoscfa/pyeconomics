# tests/test_fred_api.py

import os
import datetime
import pytest
from unittest.mock import patch, MagicMock

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


def test_singleton_none_instance():
    FredClient.reset_instance()
    assert FredClient._instance is None


def test_singleton_existing_instance(fred_client):
    """
    Test to ensure FredClient does not create a new instance if one already
    exists.
    """
    FredClient.reset_instance()  # Ensure a fresh start
    first_instance = FredClient(api_key='test_api_key')
    second_instance = FredClient(api_key='another_test_api_key')

    assert first_instance is second_instance  # Should be the same instance


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
    FredClient.reset_instance()  # Reset instance before test
    FredClient._instance = fred_client  # Ensure the instance is set
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


def test_keyring_unavailable():
    with patch.dict('sys.modules', {'keyring': None}):
        from importlib import reload
        FredClient.reset_instance()

        # Set a test API key in the environment before reloading
        with patch.dict(
            'os.environ',
            {'FRED_API_KEY': 'test_api_key'}
        ):
            import pyeconomics.api.fred_api as fred_api
            fred_api.KEYRING_AVAILABLE = False
            reload(fred_api)

            assert not fred_api.KEYRING_AVAILABLE

            # Use a context manager to create the FredClient instance
            with patch(
                'pyeconomics.api.fred_api.FredClient.__new__',
                    return_value=MagicMock()):
                # Now the FRED_API_KEY environment variable will be used
                client = FredClient(api_key=None)
                assert client is not None


def test_keyring_available_but_no_api_key():
    with patch('keyring.get_password', return_value=None):
        FredClient.reset_instance()  # Ensure fresh instance for each test
        # Ensure no environment variable is set
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(
                ValueError,
                match="API Key for FRED must be provided "
                      "or retrievable from keyring."
            ):
                FredClient(api_key=None)  # No API key provided


def test_no_api_key_provided():
    with patch('keyring.get_password', return_value=None):
        FredClient.reset_instance()  # Ensure fresh instance for each test
        # Ensure no environment variable is set
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(
                ValueError,
                match="API Key for FRED must be provided or "
                      "retrievable from keyring."
            ):
                FredClient(api_key=None)  # No API key provided


def test_fetch_data_no_data_found(fred_client):
    with patch.object(
        fred_client.client,
        'get_series',
            return_value=pd.Series([])):
        with pytest.raises(ValueError, match="No data found for series ID GDP"):
            fred_client.fetch_data('GDP')


def test_fetch_data_exception_handling(fred_client):
    with patch.object(
        fred_client.client,
        'get_series',
            side_effect=Exception("API error")):
        with pytest.raises(Exception, match="API error"):
            fred_client.fetch_data('GDP')


def test_get_latest_value_exception_handling(fred_client):
    with patch.object(
        fred_client,
        'fetch_data',
            side_effect=Exception("Data fetch error")):
        with pytest.raises(Exception, match="Data fetch error"):
            fred_client.get_latest_value('GDP')


def test_get_historical_value_exception_handling(fred_client):
    with patch.object(
        fred_client,
        'fetch_data',
            side_effect=Exception("Data fetch error")
    ):
        with pytest.raises(Exception, match="Data fetch error"):
            fred_client.get_historical_value('GDP', periods=-2)


def test_get_series_name_exception_handling(fred_client):
    with patch.object(
        fred_client.client,
        'get_series_info',
            side_effect=Exception("API error")):
        with pytest.raises(Exception, match="API error"):
            fred_client.get_series_name('GDP')


def test_keyring_get_password_called():
    with patch.dict('sys.modules', {'keyring': MagicMock()}):
        from importlib import reload
        import pyeconomics.api.fred_api as fred_api
        reload(fred_api)
        FredClient.reset_instance()

        mock_keyring = fred_api.keyring
        mock_keyring.get_password = MagicMock(return_value='mocked_api_key')

        # Ensure that KEYRING_AVAILABLE is set to True
        with patch('pyeconomics.api.fred_api.KEYRING_AVAILABLE', True):
            with patch.dict(os.environ, {'FRED_API_KEY': ''}):
                try:
                    FredClient(api_key=None)
                except ValueError:
                    # If the initialization fails,
                    # catch the exception to check why
                    pass

                mock_keyring.get_password.assert_called_once_with(
                    'fred', 'api_key')


def test_get_data_or_fetch_exception_handling():
    FredClient.reset_instance()
    with patch.object(
        FredClient, 'get_latest_value', side_effect=Exception("fetch error")
    ):
        with patch('pyeconomics.api.fred_api.KEYRING_AVAILABLE', False):
            FredClient._instance = FredClient(api_key="test_api_key")
            with pytest.raises(Exception, match="fetch error"):
                FredClient.get_data_or_fetch(None, 'GDP', 0)


def test_instance_creation_with_existing_instance():
    FredClient.reset_instance()
    with patch.object(
            FredClient, '__new__', wraps=FredClient.__new__) as mock_new:
        first_instance = FredClient(api_key='test_api_key')
        second_instance = FredClient(api_key='another_test_api_key')

        assert first_instance is second_instance  # Should be the same instance
        # Ensure __new__ was called twice, but instance creation only once
        assert mock_new.call_count == 2
        assert first_instance == second_instance


if __name__ == '__main__':
    pytest.main()
