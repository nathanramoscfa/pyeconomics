# tests/test_fred_data.py

from unittest.mock import patch

import pandas as pd
import pytest

from pyeconomics.utils.fred import fetch_historical_fed_funds_rate


@pytest.fixture
def mock_fred_data():
    """Fixture for mock FRED data."""
    dfedtar_data = {
        'DATE': pd.date_range(start='2000-01-01', end='2008-12-15', freq='D'),
        'VALUE': [1.5] * len(
            pd.date_range(start='2000-01-01', end='2008-12-15', freq='D'))
    }
    dfedtaru_data = {
        'DATE': pd.date_range(start='2008-12-16', end='2020-01-01', freq='D'),
        'VALUE': [0.25] * len(
            pd.date_range(start='2008-12-16', end='2020-01-01', freq='D'))
    }
    dfedtar = pd.DataFrame(dfedtar_data).set_index('DATE')
    dfedtaru = pd.DataFrame(dfedtaru_data).set_index('DATE')
    return dfedtar, dfedtaru


@patch('pyeconomics.api.fred_api.fred_client')
def test_fetch_historical_fed_funds_rate(mock_fred_client, mock_fred_data):
    dfedtar, dfedtaru = mock_fred_data
    mock_fred_client.fetch_data.side_effect = [dfedtar['VALUE'],
                                               dfedtaru['VALUE']]

    result = fetch_historical_fed_funds_rate()

    # Check the column name
    assert list(result.columns) == ['FedRate'], \
        f"Column names do not match: {list(result.columns)} != ['FedRate']"

    # Check the index name
    assert result.index.name == 'DATE', \
        f"Index name does not match: {result.index.name} != 'DATE'"

    # Check the data type is DataFrame
    assert isinstance(result, pd.DataFrame), \
        f"Result is not a DataFrame: {type(result)}"


if __name__ == '__main__':
    pytest.main()
