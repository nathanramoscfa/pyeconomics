# pyeconomics/api/openai_api.py

import openai
import os
import keyring
from typing import Optional


def get_openai_api_key() -> Optional[str]:
    """
    Retrieves the OpenAI API key from keyring or environment variables.

    Returns:
        Optional[str]: The API key if found, otherwise None.
    """
    api_key = keyring.get_password("openai", "api_key")

    if not api_key:
        api_key = os.getenv('OPENAI_API_KEY')

    if not api_key:
        return None

    return api_key


def initialize_openai_client(api_key: Optional[str] = None) -> None:
    """
    Initializes the OpenAI client with the provided API key.

    Args:
        api_key (Optional[str]): The OpenAI API key. If not provided, it tries
            to retrieve one.

    Raises:
        ValueError: If no API key is provided or found.
    """
    if not api_key:
        api_key = get_openai_api_key()

    if not api_key:
        raise ValueError("API Key for OpenAI must be provided either in "
                         "keyring or as an environment variable.")

    openai.api_key = api_key


def load_prompt(file_path: str) -> str:
    """
    Load the prompt template from a text file.

    Args:
        file_path (str): Path to the text file containing the prompt template.

    Returns:
        str: The prompt template as a string.
    """
    with open(file_path, 'r') as file:
        prompt_template = file.read()
    return prompt_template
