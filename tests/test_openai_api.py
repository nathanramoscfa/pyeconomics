# pyeconomics/tests/test_openai_api.py

from unittest.mock import patch, mock_open

import openai
import pytest

from pyeconomics.api.openai_api import load_prompt, initialize_openai_client


# Mock the keyring and os.getenv functions
@patch('keyring.get_password', return_value=None)
@patch('os.getenv', return_value=None)
def test_no_api_key(_mock_getenv, _mock_get_password):
    with pytest.raises(ValueError, match="API Key for OpenAI must be provided "
                                         "either in keyring or as an "
                                         "environment variable."):
        initialize_openai_client()  # Explicitly call initialize_openai_client


@patch('keyring.get_password', return_value="fake_key_from_keyring")
@patch('os.getenv', return_value=None)
def test_api_key_from_keyring(_mock_getenv, _mock_get_password):
    initialize_openai_client()  # Explicitly call initialize_openai_client
    assert openai.api_key == "fake_key_from_keyring"


@patch('keyring.get_password', return_value=None)
@patch('os.getenv', return_value="fake_key_from_env")
def test_api_key_from_env(_mock_getenv, _mock_get_password):
    initialize_openai_client()  # Explicitly call initialize_openai_client
    assert openai.api_key == "fake_key_from_env"


@patch('keyring.get_password', return_value="fake_key_from_keyring")
@patch('os.getenv', return_value="fake_key_from_env")
def test_prefer_keyring_over_env(_mock_getenv, _mock_get_password):
    initialize_openai_client()  # Explicitly call initialize_openai_client
    assert openai.api_key == "fake_key_from_keyring"


@patch(
    'builtins.open',
    new_callable=mock_open,
    read_data="This is a test prompt."
)
def test_load_prompt(mock_file):
    prompt = load_prompt("dummy_path.txt")
    assert prompt == "This is a test prompt."
    mock_file.assert_called_once_with("dummy_path.txt", 'r')


if __name__ == '__main__':
    pytest.main()
