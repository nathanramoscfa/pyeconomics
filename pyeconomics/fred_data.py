import pandas as pd

from .api import fred_client


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
    return df
