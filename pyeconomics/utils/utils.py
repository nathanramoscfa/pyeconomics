# pyeconomics/utils/utils.py

import base64
import textwrap

from datetime import datetime


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
