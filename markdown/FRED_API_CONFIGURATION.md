## FRED API Key Configuration Guide

Feel free to use this [Jupyter Notebook](../examples/api_configuration/fred_api_configuration.ipynb)
to configure your API key as instructed below. Some features of PyEconomics
require access to the FRED API. To use these features, you need to obtain an
API key from the Federal Reserve Economic Data (FRED) website.

1. Go to the [FRED API page](https://fred.stlouisfed.org/docs/api/fred/) and 
   sign
   up for an API key.
2. Once you have your API key, you can securely store it using the `keyring`
   library.

### Storing the API Key

If you don't have `keyring` installed, you can install it using `pip`:

```sh
pip install keyring
```

Open a Python interpreter and run the following commands to store your API key:

```python
import keyring

# Replace 'your_api_key_here' with your actual FRED API key
keyring.set_password('fred', 'api_key', 'your_api_key_here')
```

### Retrieving the API Key

To use the stored API key in your code, retrieve it using `keyring`:

```python
import keyring

# Retrieve the API key
fred_api_key = keyring.get_password('fred', 'api_key')

print(fred_api_key)  # Print the API key
```

### Setting the API Key as an Environment Variable

If you prefer to set the API key as an environment variable, you can do so using
the os package:

```python
import os

# Set the API key as an environment variable
os.environ['FRED_API_KEY'] = 'your_api_key_here'

# Now you can access the API key from the environment variable
print(os.getenv('FRED_API_KEY'))
```