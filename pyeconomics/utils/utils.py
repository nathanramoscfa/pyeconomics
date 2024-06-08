import base64
import textwrap

from ..api import fred_client


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
    # Print the series names and their IDs
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
