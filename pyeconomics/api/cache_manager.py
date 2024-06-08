# pyeconomics/api/cache_manager.py

import os
import pickle
from datetime import datetime, timedelta
from hashlib import sha256
from typing import Any

# Define the cache directory relative to the root of the project
CACHE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'cache')

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)


def cache_filename(key: str) -> str:
    """Generate a filename for the cache based on a hashed key.

    Args:
        key (str): The key to hash for generating the cache filename.

    Returns:
        str: The path to the cache file.
    """
    hashed_key = sha256(key.encode('utf-8')).hexdigest()
    return os.path.join(CACHE_DIR, f"{hashed_key}.pkl")


def save_to_cache(key: str, data: Any) -> None:
    """Save data to the cache.

    Args:
        key (str): The key for the cache entry.
        data: The data to be cached.

    Returns:
        None
    """
    filename = cache_filename(key)
    with open(filename, 'wb') as f:
        pickle.dump(data, f)


def load_from_cache(key: str, expiry: timedelta = timedelta(hours=6)):
    """Load data from the cache if available and not expired.

    Args:
        key (str): The key for the cache entry.
        expiry (timedelta): The expiration time for the cache entry.

    Returns:
        The cached data if available and not expired, otherwise None.
    """
    filename = cache_filename(key)
    if os.path.exists(filename):
        file_mtime = datetime.fromtimestamp(os.path.getmtime(filename))
        if datetime.now() - file_mtime < expiry:
            with open(filename, 'rb') as f:
                return pickle.load(f)
    return None
