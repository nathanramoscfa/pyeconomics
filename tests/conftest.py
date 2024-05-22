import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture(autouse=True)
def mock_keyring():
    with patch('keyring.get_password') as mock_get_password:
        mock_get_password.return_value = 'dummy_fred_api_key'
        yield


@pytest.fixture(autouse=True)
def mock_fred_client():
    with patch('pyeconomics.api.fred_api.FredClient.__new__') as mock_new:
        mock_instance = MagicMock()
        mock_instance.client = MagicMock()
        mock_new.return_value = mock_instance
        yield mock_instance
