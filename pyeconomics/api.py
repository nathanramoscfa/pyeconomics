import datetime
import logging
from typing import Optional

import keyring
import pandas as pd
from fredapi import Fred


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
    _instance = None

    def __new__(cls, api_key: Optional[str] = None):
        """
        Ensures a single instance of FredClient.

        Args:
            api_key (Optional[str]): The FRED API key, retrieved from
                keyring if None.

        Returns:
            FredClient: Singleton instance.
        """
        if not isinstance(cls._instance, cls):
            cls._instance = super(FredClient, cls).__new__(cls)
            api_key = api_key or keyring.get_password(
                "fred", "api_key")
            cls._instance.client = Fred(api_key=api_key)
        return cls._instance

    def fetch_data(self, series_id: str) -> pd.Series:
        """
        Fetches data for a given series ID from FRED.

        Args:
            series_id (str): FRED series ID to fetch data for.

        Returns:
            pandas.Series: Series containing the requested data.

        Raises:
            ValueError: If no data is found for series ID.
            Exception: For fetch operation errors.
        """
        try:
            data = self.client.get_series(series_id)
            if data.empty:
                raise ValueError(f"No data found for series ID {series_id}")
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
            float: Most recent data point up to today, or None if no data.
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
            float: Historical data point value, or None if unavailable.
        """
        series = self.fetch_data(series_id)
        return series.iloc[periods] \
            if not series.empty and len(series) > -periods else None

    @staticmethod
    def get_data_or_fetch(default, series_id):
        """Fetches data if default is None using the given FRED series ID."""
        return fred_client.get_latest_value(
            series_id) if default is None else default


# Global instance of the FredClient
fred_client = FredClient()
