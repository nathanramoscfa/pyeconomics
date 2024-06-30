# pyeconomics/utils/fred.py

import pandas as pd

from pyeconomics.api.fred_api import fred_client


def print_fred_series_names(
    inflation_series_id: str = 'PCETRIM12M159SFRBDAL',
    unemployment_rate_series_id: str = 'UNRATE',
    natural_unemployment_series_id: str = 'NROU',
    real_interest_rate_series_id: str = 'DFII10'
) -> None:
    """
    Print the FRED series IDs and their corresponding names for various
    economic indicators.

    Args:
        inflation_series_id (str): FRED Series ID for inflation data.
        unemployment_rate_series_id (str): FRED Series ID for unemployment rate.
        natural_unemployment_series_id (str): FRED Series ID for natural
            unemployment rate.
        real_interest_rate_series_id (str): FRED Series ID for long-term real
            interest rate.

    Returns:
        None
    """
    from ..api import fred_client
    print(
        f"Inflation Series ID:               "
        f"{fred_client.get_series_name(inflation_series_id)}")
    print(
        f"Unemployment Rate Series ID:       "
        f"{fred_client.get_series_name(unemployment_rate_series_id)}")
    print(
        f"Natural Unemployment Series ID:    "
        f"{fred_client.get_series_name(natural_unemployment_series_id)}")
    print(
        f"Real Interest Rate Series ID:      "
        f"{fred_client.get_series_name(real_interest_rate_series_id)}")


def fetch_historical_fed_funds_rate() -> pd.DataFrame:
    """
    Fetches and combines Federal Funds Target Rate historical data.

    Returns:
        pandas.DataFrame: DataFrame containing the Federal Funds Target Rate
            historical data.

    Notes:
        - Prior to 2008-12-15, the Federal Funds Target Rate was a single value.
        - Post 2008-12-15, the Federal Funds Target Rate is a range.
        - This function uses the single value up to 2008-12-15, and the upper
          limit of the range post 2008-12-15.
    """
    dfedtar = fred_client.fetch_data('DFEDTAR')
    dfedtaru = fred_client.fetch_data('DFEDTARU')

    # Use only the upper limit post 2008-12-15
    df = pd.concat([
        dfedtar[dfedtar.index <= '2008-12-15'],
        dfedtaru[dfedtaru.index > '2008-12-15']
    ])
    df.index.name = 'FedRate'
    df.name = 'FedRate'
    return df
