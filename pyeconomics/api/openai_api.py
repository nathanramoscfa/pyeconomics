# pyeconomics/api/openai_api.py

import openai
import os
import keyring
from typing import Optional


def get_openai_api_key(api_key: Optional[str] = None) -> str:
    """
    Retrieve the OpenAI API key from keyring, environment variables, or a
    manually passed key.

    Args:
        api_key (Optional[str]): The OpenAI API key to use. If None, it falls
            back to keyring or environment variable.

    Returns:
        str: The API key for OpenAI.

    Raises:
        ValueError: If no API key is found.
    """
    if api_key:
        return api_key

    # Attempt to retrieve the API key from keyring
    api_key = keyring.get_password("openai", "api_key")

    # If the API key is not found in keyring, try to get it from environment
    # variables
    if not api_key:
        api_key = os.getenv('OPENAI_API_KEY')

    # Raise an error if the API key is still not found
    if not api_key:
        raise ValueError("API Key for OpenAI must be provided either in "
                         "keyring or as an environment variable.")
    return api_key


def initialize_openai_client(api_key: Optional[str] = None):
    """
    Initialize the OpenAI client with the API key.

    Args:
        api_key (Optional[str]): The OpenAI API key to use. If None, it falls
            back to keyring or environment variable.
    """
    openai.api_key = get_openai_api_key(api_key)


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
