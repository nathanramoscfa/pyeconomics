# pyeconomics/api/fred_api.py

import os
import logging
import datetime
from threading import Lock
from typing import Optional, Any

import pandas as pd
from fredapi import Fred

from pyeconomics.api.cache_manager import save_to_cache, load_from_cache

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    keyring = None
    KEYRING_AVAILABLE = False


class DataSource:
    """
    Abstract base class for all data source clients.

    Attributes:
        api_key (Optional[str]): API key for accessing the data source.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def fetch_data(self, series_id: str) -> pd.Series:
        """
        Abstract method to fetch data from a data source given a series ID.

        Args:
            series_id (str): The identifier for the data series.

        Returns:
            pandas.Series: Series containing the requested data.

        Raises:
            NotImplementedError: If method is not implemented.
        """
        raise NotImplementedError(
            "This method should be overridden by subclasses."
        )


class FredClient(DataSource):
    """
    A client for fetching data from the FRED API.

    Inherits from DataSource and implements methods to fetch data from FRED.
    """
    _instance: Optional['FredClient'] = None
    _lock: Lock = Lock()

    def __new__(cls, api_key: Optional[str] = None) -> 'FredClient':
        """
        Ensures a single instance of FredClient using a thread-safe singleton
        pattern.

        Args:
            api_key (Optional[str]): The FRED API key, retrieved from
                keyring or environment variable if None.

        Returns:
            FredClient: Singleton instance.
        """
        with cls._lock:
            if cls._instance is None:
                logging.debug("Creating new FredClient instance")
                cls._instance = object.__new__(cls)
                api_key_retrieved = api_key or os.getenv('FRED_API_KEY')
                logging.debug(f"API key from environment variable: "
                              f"{api_key_retrieved}")
                if not api_key_retrieved and KEYRING_AVAILABLE:
                    logging.debug("Attempting to retrieve API key from keyring")
                    try:
                        api_key_retrieved = keyring.get_password(
                            "fred", "api_key")
                        logging.debug(f"API key from keyring: "
                                      f"{api_key_retrieved}")
                    except Exception as e:
                        logging.debug(f"Keyring not available: {e}")
                if not api_key_retrieved:
                    logging.debug("API Key not found, raising ValueError.")
                    raise ValueError(
                        "API Key for FRED must be provided "
                        "or retrievable from keyring.")
                logging.debug(f"Using API Key: {api_key_retrieved}")
                cls._instance.client = Fred(api_key=api_key_retrieved)
            return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """
        Resets the singleton instance. Use this method only in tests.
        """
        with cls._lock:
            cls._instance = None
            logging.debug("FredClient instance reset")

    def fetch_data(self, series_id: str) -> pd.Series:
        """
        Fetches data for a given series ID from FRED with caching.

        Args:
            series_id (str): FRED series ID to fetch data for.

        Returns:
            pandas.Series: Series containing the requested data.

        Raises:
            ValueError: If no data is found for series ID.
            Exception: For fetch operation errors.
        """
        cache_key = f"fred_series_{series_id}"
        data = load_from_cache(cache_key)

        if data is not None:
            logging.info(f"Data for {series_id} loaded from cache.")
            return data

        try:
            data = self.client.get_series(series_id)
            if data.empty:
                raise ValueError(f"No data found for series ID {series_id}")
            save_to_cache(cache_key, data)
            logging.info(f"Data for {series_id} fetched and cached.")
            return data
        except Exception as e:
            logging.error(f"Fetching error for {series_id}: {e}")
            raise

    def get_latest_value(self, series_id: str) -> Optional[float]:
        """
        Fetches the latest value for a FRED series ID, considering only dates
        up to today.

        Args:
            series_id (str): Identifier for the FRED data series.

        Returns:
            Optional[float]: Most recent data point up to today, or None if no
                data.
        """
        try:
            data = self.fetch_data(series_id)
            today = datetime.date.today()
            filtered_data = data[:str(today)]
            return filtered_data.iloc[-1] if not filtered_data.empty else None
        except Exception as e:
            logging.error(f"Error in getting latest value for {series_id}: {e}")
            raise

    def get_historical_value(
        self,
        series_id: str,
        periods: int = -1
    ) -> Optional[float]:
        """
        Fetches a historical value for a FRED series ID.

        Args:
            series_id (str): Identifier for the FRED data series.
            periods (int): Index of period to retrieve (negative for
                historical).

        Returns:
            Optional[float]: Historical data point value, or None if
                unavailable.
        """
        try:
            series = self.fetch_data(series_id)
            return series.iloc[periods] \
                if not series.empty and len(series) > -periods else None
        except Exception as e:
            logging.error(
                f"Error in getting historical value for {series_id}: {e}")
            raise

    def get_series_name(self, series_id: str) -> str:
        """
        Fetches the name of a FRED series given its ID.

        Args:
            series_id (str): Identifier for the FRED data series.

        Returns:
            str: Name of the FRED series.
        """
        try:
            return self.client.get_series_info(series_id)["title"]
        except Exception as e:
            logging.error(f"Error in getting series name for {series_id}: {e}")
            raise

    @classmethod
    def get_data_or_fetch(
        cls,
        default: Any,
        series_id: str,
        periods: int = 0
    ) -> Any:
        """
        Fetches data if default is None using the given FRED series ID. Can
        fetch historical data based on periods.

        Args:
            default (Any): Default value to return if not None.
            series_id (str): FRED series ID for fetching data if default is
                None.
            periods (int): Number of periods back to fetch the data. Default is
                0 for current data.

        Returns:
            Any: Latest value or historical value or default value.
        """
        if default is not None:
            return default
        else:
            try:
                if periods == 0:
                    return cls._instance.get_latest_value(series_id)
                else:
                    return cls._instance.get_historical_value(
                        series_id, periods)
            except Exception as e:
                logging.error(
                    f"Error in get_data_or_fetch for {series_id}: {e}")
                raise


# Global instance of the FredClient
fred_client = FredClient()
