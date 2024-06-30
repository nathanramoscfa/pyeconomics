# tests/test_coinmetrics_api.py

import pytest
import pandas as pd
from unittest.mock import patch
from datetime import datetime

from pyeconomics.api.coinmetrics_api import load_bitcoin_data, bitcoin_s2f_data
from pyeconomics.utils.utils import months_until_next_halving, \
    halving_dates_list

# Mock data for testing
mock_data = pd.DataFrame({
    'time': pd.date_range(start='2020-01-01', periods=10, freq='D'),
    'CapMrktCurUSD': [1000 + i for i in range(10)],
    'PriceUSD': [10 + i for i in range(10)],
    'BlkCnt': [1 for _ in range(10)],
    'SplyCur': [100 + i for i in range(10)],
})


@pytest.fixture
def mock_load_from_cache():
    with patch('pyeconomics.api.coinmetrics_api.load_from_cache') as mock:
        yield mock


@pytest.fixture
def mock_save_to_cache():
    with patch('pyeconomics.api.coinmetrics_api.save_to_cache') as mock:
        yield mock


@pytest.fixture
def mock_pd_read_csv():
    with patch('pandas.read_csv') as mock:
        yield mock


def test_load_bitcoin_data_cache_hit(mock_load_from_cache):
    mock_load_from_cache.return_value = mock_data

    result = load_bitcoin_data()
    pd.testing.assert_frame_equal(result, mock_data)
    mock_load_from_cache.assert_called_once()


def test_load_bitcoin_data_cache_miss(mock_load_from_cache, mock_save_to_cache,
                                      mock_pd_read_csv):
    mock_load_from_cache.return_value = None
    mock_pd_read_csv.return_value = mock_data

    result = load_bitcoin_data()
    pd.testing.assert_frame_equal(result, mock_data)
    mock_load_from_cache.assert_called_once()
    mock_pd_read_csv.assert_called_once()
    mock_save_to_cache.assert_called_once()


@patch('pyeconomics.api.coinmetrics_api.load_bitcoin_data')
def test_bitcoin_s2f_data(mock_load_bitcoin_data):
    mock_load_bitcoin_data.return_value = mock_data.set_index('time')

    result = bitcoin_s2f_data()

    assert 'TotalBlks' in result.columns
    assert 'Flow' in result.columns
    assert 'StocktoFlow' in result.columns
    assert 'AnnInflationRate%' in result.columns
    assert 'MaxDrawdown%' in result.columns
    assert 'BlkCntMonthly' in result.columns
    assert 'MonthsUntilHalving' in result.columns


def test_months_until_next_halving():
    halving_dates = halving_dates_list()
    test_date = datetime(2023, 1, 1)
    expected_months = (halving_dates[3] - test_date).days // 30
    assert months_until_next_halving(test_date,
                                     halving_dates) == expected_months


def test_halving_dates_list():
    halving_dates = halving_dates_list()
    assert isinstance(halving_dates, list)
    assert all(isinstance(date, datetime) for date in halving_dates)


if __name__ == '__main__':
    pytest.main()
