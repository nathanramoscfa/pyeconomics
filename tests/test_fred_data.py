# pyeconomics/api/fred_data.py
from unittest.mock import patch

import pandas as pd
import pytest

from pyeconomics.api.fred_data import fetch_historical_fed_funds_rate


@pytest.fixture
def mock_fred_data():
    """Fixture for mock FRED data."""
    dfedtar_data = {
        'DATE': pd.date_range(start='2000-01-01', end='2008-12-15', freq='M'),
        'VALUE': [1.5] * 108
    }
    dfedtaru_data = {
        'DATE': pd.date_range(start='2008-12-16', end='2020-01-01', freq='M'),
        'VALUE': [0.25] * 133
    }
    # Fix the lengths to ensure they match
    dfedtar_data['VALUE'] = dfedtar_data['VALUE'][:len(dfedtar_data['DATE'])]
    dfedtaru_data['VALUE'] = dfedtaru_data['VALUE'][:len(dfedtaru_data['DATE'])]

    dfedtar = pd.DataFrame(dfedtar_data).set_index('DATE')
    dfedtaru = pd.DataFrame(dfedtaru_data).set_index('DATE')
    return dfedtar, dfedtaru


@patch('pyeconomics.api.fred_data.fred_client')
def test_fetch_historical_fed_funds_rate(mock_fred_client, mock_fred_data):
    dfedtar, dfedtaru = mock_fred_data
    mock_fred_client.fetch_data.side_effect = [dfedtar, dfedtaru]

    result = fetch_historical_fed_funds_rate()

    expected = pd.concat([
        dfedtar[dfedtar.index <= '2008-12-15'],
        dfedtaru[dfedtaru.index > '2008-12-15']
    ])
    expected.index.name = 'FedRate'
    expected.name = 'FedRate'

    pd.testing.assert_frame_equal(result, expected)


if __name__ == '__main__':
    pytest.main()
