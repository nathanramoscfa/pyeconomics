# .semgrep/tests/unsafe-deserialization.py
# Test cases for .semgrep/rules/unsafe-deserialization.yaml (semgrep --test).
# Deliberately unsafe code: excluded from the bandit and semgrep hooks.
# ruleid: unsafe-deserialization
import pickle
# ruleid: unsafe-deserialization
import marshal
# ruleid: unsafe-deserialization
import shelve
# ruleid: unsafe-deserialization
from pickle import loads
# ruleid: unsafe-deserialization
import pickle as pkl
import json

import numpy
import pandas as pd


def cases(data, path, fh):
    # ruleid: unsafe-deserialization
    pickle.loads(data)
    # ruleid: unsafe-deserialization
    pickle.load(fh)
    # ruleid: unsafe-deserialization
    pickle.Unpickler(fh).load()
    # ruleid: unsafe-deserialization
    pkl.loads(data)
    # ruleid: unsafe-deserialization
    loads(data)
    # ruleid: unsafe-deserialization
    marshal.loads(data)
    # ruleid: unsafe-deserialization
    shelve.open(path)
    # ruleid: unsafe-deserialization
    pd.read_pickle(path)
    # ruleid: unsafe-deserialization
    numpy.load(path, allow_pickle=True)

    # ok: unsafe-deserialization
    json.loads(data)
    # ok: unsafe-deserialization
    numpy.load(path)
    # ok: unsafe-deserialization
    numpy.load(path, allow_pickle=False)
    # ok: unsafe-deserialization
    pd.read_parquet(path)
