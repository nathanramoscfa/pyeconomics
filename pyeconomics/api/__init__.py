# pyeconomics/api/__init__.py
from .cache_manager import save_to_cache, load_from_cache
from .fred_api import FredClient, fred_client
from .fred_data import fetch_historical_fed_funds_rate

__all__ = ['FredClient', 'fred_client', 'fetch_historical_fed_funds_rate',
           'save_to_cache', 'load_from_cache']
