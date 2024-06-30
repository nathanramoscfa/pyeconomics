# pyeconomics/api/coinmetrics_api.py

import numpy as np
import pandas as pd
from datetime import timedelta

from pyeconomics.api.cache_manager import save_to_cache, load_from_cache
from pyeconomics.utils.utils import months_until_next_halving, \
    halving_dates_list


def load_bitcoin_data(
    url: str = 'https://raw.githubusercontent.com/coinmetrics/data/master/csv/'
               'btc.csv'
) -> pd.DataFrame:
    # Define a unique key for the cache based on the URL
    cache_key = f"bitcoin_data_{url}"

    # Try to load the data from cache
    cached_data = load_from_cache(cache_key, expiry=timedelta(hours=6))

    if cached_data is not None:
        return cached_data

    # If cache is empty or expired, fetch the data
    dtype = {'principal_market_usd': 'str'}
    raw_data = pd.read_csv(url, index_col='time', dtype=dtype)

    # Save the fetched data to cache
    save_to_cache(cache_key, raw_data)

    return raw_data


def bitcoin_s2f_data() -> pd.DataFrame:
    data = load_bitcoin_data()[[
        'CapMrktCurUSD', 'PriceUSD', 'BlkCnt', 'SplyCur'
    ]].copy()

    data.insert(3, 'TotalBlks', data.BlkCnt.cumsum().values)
    data['Flow'] = data['SplyCur'] - data['SplyCur'].shift(1)
    data['StocktoFlow'] = data['SplyCur'] / (
        data['SplyCur'] - data['SplyCur'].shift(365))
    data['AnnInflationRate%'] = (data['SplyCur'] / data['SplyCur'].shift(
        365) - 1) * 100
    data = data.dropna()

    drawdown = data.CapMrktCurUSD.ffill()
    drawdown[np.isnan(drawdown)] = -np.Inf
    roll_max = np.maximum.accumulate(drawdown)
    drawdown = (drawdown / roll_max - 1.) * 100
    data['MaxDrawdown%'] = drawdown.round(4)

    data.insert(2, 'BlkCntMonthly',
                data['TotalBlks'] - data['TotalBlks'].shift(30))

    data.index = pd.to_datetime(data.index)
    halving_dates = halving_dates_list()
    data['MonthsUntilHalving'] = data.index.map(
        lambda x: months_until_next_halving(x, halving_dates))
    return data
