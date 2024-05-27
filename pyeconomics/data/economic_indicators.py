# pyeconomics/data/economic_indicators.py

from dataclasses import dataclass

from typing import Optional


@dataclass
class EconomicIndicators:
    """
    Data class for storing economic indicators.

    Attributes:
        current_fed_rate (float, optional): Current Federal Funds Target Rate.
            Defaults to None.
        current_inflation_rate (float, optional): Current inflation rate.
            Defaults to None.
        current_unemployment_rate (float, optional): Current unemployment rate.
            Defaults to None.
        inflation_series_id (str): FRED Series ID for inflation data.
        lagged_natural_unemployment_rate (float, optional): The natural
            unemployment rate from a previous period. Defaults to None.
        lagged_unemployment_rate (float, optional): The unemployment rate from a
            previous period. Defaults to None.
        long_term_real_interest_rate (float, optional): Long-term real interest
            rate. Defaults to None.
        natural_unemployment_rate (float, optional): Natural unemployment rate.
            Defaults to None.
        natural_unemployment_series_id (str): FRED Series ID for natural
            unemployment rate.
        real_interest_rate_series_id (str): FRED Series ID for long-term real
            interest rate.
        unemployment_rate_series_id (str): FRED Series ID for unemployment rate.
    """
    current_fed_rate: Optional[float] = None
    current_inflation_rate: Optional[float] = None
    current_unemployment_rate: Optional[float] = None
    inflation_series_id: str = 'PCETRIM12M159SFRBDAL'
    lagged_natural_unemployment_rate: Optional[float] = None
    lagged_unemployment_rate: Optional[float] = None
    long_term_real_interest_rate: Optional[float] = None
    natural_unemployment_rate: Optional[float] = None
    natural_unemployment_series_id: str = 'NROU'
    real_interest_rate_series_id: str = 'DFII10'
    unemployment_rate_series_id: str = 'UNRATE'
