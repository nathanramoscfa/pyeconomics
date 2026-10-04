# pyeconomics/utils/utils.py

import base64
import textwrap

from datetime import datetime
from typing import Tuple


def wrap_text(text: str, width: int, indent: int = 2):
    """
    Wrap text to a specified width with an optional indent.

    Args:
        text (str): The text to wrap.
        width (int): The width to wrap the text to.
        indent (int): The number of spaces to indent each line.

    Returns:
        str: The wrapped and indented text.
    """
    wrapped_lines = textwrap.wrap(text, width=width - indent)
    indented_text = '\n'.join((' ' * indent) + line for line in wrapped_lines)
    return indented_text


def encode_image(image_path):
    """
    Encode the image to base64 format.

    Args:
        image_path (str): Path to the image file.

    Returns:
        str: Base64 encoded image.
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def halving_dates_list() -> list[datetime]:
    """
    Return the Bitcoin halving dates.

    Returns:
        list[datetime]: List of Bitcoin halving dates.
    """
    return [
        datetime(2012, 11, 28),
        datetime(2016, 7, 9),
        datetime(2020, 5, 11),
        datetime(2024, 4, 19),
        datetime(2028, 3, 27),
        datetime(2032, 2, 29),
    ]


def months_until_next_halving(date: datetime, halving_dates: list[datetime]):
    for halving_date in halving_dates:
        if date < halving_date:
            delta = halving_date - date
            return delta.days // 30  # Approximate months
    return 0


def get_forecast_tickers(quarters_ahead: int = 2) -> Tuple[str, str, str]:
    """
    Generate the Bloomberg tickers for the consensus Core PCE (yoy%) forecast
    and unemployment forecast for the specified number of quarters ahead,
    as well as for the current quarter.

    Args:
        quarters_ahead (int): The number of quarters ahead to use for forecast.
            Default is 2 quarters.

    Returns:
        Tuple[str, str, str]: The tickers for Core PCE forecast for the
            specified number of quarters ahead, unemployment forecast for the
            specified quarters ahead, and the current quarter unemployment
            forecast.
    """
    # Get current period
    current_year = datetime.now().year
    current_quarter = (datetime.now().month - 1) // 3 + 1

    # Calculate the future quarter and year based on quarters_ahead
    future_quarter = (current_quarter + quarters_ahead - 1) % 4 + 1
    future_year = current_year + (current_quarter + quarters_ahead - 1) // 4

    # Construct the Bloomberg tickers for the specified quarters ahead
    core_pce_future_ticker = \
        f"ECCCUS Q{future_quarter}{future_year % 100:02d} INDEX"
    unemployment_future_ticker = \
        f"ECUPUS Q{future_quarter}{future_year % 100:02d} INDEX"

    # Construct the Bloomberg ticker for the current quarter
    unemployment_current_ticker = \
        f"ECUPUS Q{current_quarter}{current_year % 100:02d} INDEX"

    return (core_pce_future_ticker, unemployment_future_ticker,
            unemployment_current_ticker)
