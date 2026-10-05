# tests/test_credential_logging.py

"""
Regression tests: the FRED API key never reaches a log record.

Versions up to 0.2.5 logged the key at DEBUG in FredClient.__new__. These
tests build the client through each of its three key sources with the root
logger capturing DEBUG, and fail if the key appears in any record's message,
arguments or formatted output. The key is a sentinel that is not shaped like
a FRED key, and fredapi.Fred is mocked, so no request is made.
"""

import logging
from unittest.mock import MagicMock, patch

import pytest

from pyeconomics.api import fred_api

SENTINEL = 'sentinel-not-a-fred-key'


class _RecordCapture(logging.Handler):
    """Keeps every record that reaches the root logger."""

    def __init__(self):
        super().__init__(level=logging.DEBUG)
        self.setFormatter(logging.Formatter(
            '%(asctime)s %(name)s %(levelname)s %(pathname)s:%(lineno)d '
            '%(message)s'))
        self.records = []

    def emit(self, record):
        self.records.append(record)


# These two override the autouse fixtures of the same name in conftest.py,
# which replace keyring.get_password and FredClient.__new__ with mocks. Here
# the real __new__ must run, and each test controls its own key source.
@pytest.fixture(autouse=True)
def mock_keyring():
    yield


@pytest.fixture(autouse=True)
def mock_fred_client():
    yield


@pytest.fixture
def capture():
    root = logging.getLogger()
    handler = _RecordCapture()
    previous_level = root.level
    root.addHandler(handler)
    root.setLevel(logging.DEBUG)
    yield handler
    root.removeHandler(handler)
    root.setLevel(previous_level)


@pytest.fixture
def fred():
    """
    A fresh FredClient singleton built on a mocked fredapi.Fred. The
    import-time instance is restored afterwards: other tests rely on it.
    """
    original = fred_api.FredClient._instance
    fred_api.FredClient.reset_instance()
    with patch.object(fred_api, 'Fred') as mock_fred:
        yield mock_fred
    fred_api.FredClient._instance = original


def _check_no_leak(handler):
    if not handler.records:
        pytest.fail('No log record was captured; the check proves nothing.')
    for record in handler.records:
        surfaces = {
            'message': str(record.msg),
            'args': repr(record.args),
            'formatted message': record.getMessage(),
            'formatted output': handler.format(record),
        }
        for surface, text in surfaces.items():
            if SENTINEL in text:
                pytest.fail(
                    f'The FRED API key reached the {surface} of a '
                    f'{record.levelname} record from {record.pathname}:'
                    f'{record.lineno}.')


def test_key_from_argument_is_not_logged(capture, fred):
    with patch.dict('os.environ', {}, clear=True):
        fred_api.FredClient(api_key=SENTINEL)

    fred.assert_called_once_with(api_key=SENTINEL)
    _check_no_leak(capture)


def test_key_from_environment_is_not_logged(capture, fred):
    with patch.dict('os.environ', {'FRED_API_KEY': SENTINEL}, clear=True):
        fred_api.FredClient()

    fred.assert_called_once_with(api_key=SENTINEL)
    _check_no_leak(capture)


def test_key_from_keyring_is_not_logged(capture, fred):
    mock_keyring = MagicMock()
    mock_keyring.get_password.return_value = SENTINEL
    with patch.dict('os.environ', {}, clear=True), \
            patch.object(fred_api, 'keyring', mock_keyring), \
            patch.object(fred_api, 'KEYRING_AVAILABLE', True):
        fred_api.FredClient()

    mock_keyring.get_password.assert_called_once_with('fred', 'api_key')
    fred.assert_called_once_with(api_key=SENTINEL)
    _check_no_leak(capture)
