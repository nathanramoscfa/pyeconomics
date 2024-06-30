# test_import.py

import pyeconomics as pyecon

print(dir(pyecon))

try:
    pyecon.load_bitcoin_data()
    print("load_bitcoin_data() is accessible")
except AttributeError as e:
    print(e)
