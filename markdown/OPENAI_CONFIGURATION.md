# Configuring Your OpenAI API Key

This notebook provides detailed instructions on how to obtain and securely 
store your API key for accessing the OpenAI API. Proper setup will enable you 
to use OpenAI services seamlessly for your analyses.

## Step 1: Obtain an API Key

To access the OpenAI API, you first need to obtain an API key:

1. Visit the [OpenAI API website](https://platform.openai.com/).
2. Register for an account if you do not already have one.
3. Once registered, navigate to the 'API Keys' section and generate a new API key.

## Step 2: Install Keyring Library

The `keyring` library is used to securely manage credentials in Python. To 
install this library, run the following command in your notebook:

```sh
pip install keyring
```

## Step 3: Store Your API Key Securely
With the keyring library installed, you can now securely store your API key 
using the following commands:

```python
import keyring

# Replace 'your_api_key_here' with the actual API key you obtained from OpenAI
keyring.set_password('openai', 'api_key', 'your_api_key_here')
```

## Step 4: Retrieve Your API Key
Whenever you need to access the FRED API, you can securely retrieve your API 
key with:

```python
import keyring

# Retrieve the API key
api_key = keyring.get_password('openai', 'api_key')

print(f"API key: {api_key}")
```

## Note: Setting the API Key as an Environment Variable

Alternatively, you can also set the API key as an environment variable, using
the os package:

```python
import os

# Set the API key as an environment variable
os.environ['OPENAI_API_KEY'] = 'your_api_key_here'

# Now you can access the API key from the environment variable
print(os.getenv('OPENAI_API_KEY'))
```

## Conclusion
You have now set up your API key securely. This setup will ensure that your 
scripts can access services from OpenAI without hardcoding sensitive 
information.
