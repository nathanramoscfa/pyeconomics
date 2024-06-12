# pyeconomics/tests/test_openai_api.py

import pytest
from unittest.mock import patch, mock_open

from pyeconomics.api.openai_api import load_prompt


# Mock the keyring and os.getenv functions
@patch('keyring.get_password', return_value=None)
@patch('os.getenv', return_value=None)
def test_no_api_key(mock_getenv, mock_get_password):
    with pytest.raises(ValueError,
                       match="API Key for OpenAI must be provided either in "
                             "keyring or as an environment variable."):
        # Reload the module to trigger the api_key assignment
        import pyeconomics.api.openai_api
        from importlib import reload
        reload(pyeconomics.api.openai_api)


@patch('keyring.get_password', return_value="fake_key_from_keyring")
@patch('os.getenv', return_value=None)
def test_api_key_from_keyring(mock_getenv, mock_get_password):
    import pyeconomics.api.openai_api
    from importlib import reload
    reload(pyeconomics.api.openai_api)
    assert pyeconomics.api.openai_api.openai.api_key == "fake_key_from_keyring"


@patch('keyring.get_password', return_value=None)
@patch('os.getenv', return_value="fake_key_from_env")
def test_api_key_from_env(mock_getenv, mock_get_password):
    import pyeconomics.api.openai_api
    from importlib import reload
    reload(pyeconomics.api.openai_api)
    assert pyeconomics.api.openai_api.openai.api_key == "fake_key_from_env"


@patch('keyring.get_password', return_value="fake_key_from_keyring")
@patch('os.getenv', return_value="fake_key_from_env")
def test_prefer_keyring_over_env(mock_getenv, mock_get_password):
    import pyeconomics.api.openai_api
    from importlib import reload
    reload(pyeconomics.api.openai_api)
    assert pyeconomics.api.openai_api.openai.api_key == "fake_key_from_keyring"


@patch('builtins.open', new_callable=mock_open,
       read_data="This is a test prompt.")
def test_load_prompt(mock_file):
    prompt = load_prompt("dummy_path.txt")
    assert prompt == "This is a test prompt."
    mock_file.assert_called_once_with("dummy_path.txt", 'r')


if __name__ == '__main__':
    pytest.main()
