import os
import pickle
from datetime import datetime, timedelta
from hashlib import sha256

# Define the cache directory relative to the location of this script
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cache')

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)


def cache_filename(key):
    """Generate a filename for the cache based on a hashed key."""
    hashed_key = sha256(key.encode('utf-8')).hexdigest()
    return os.path.join(CACHE_DIR, f"{hashed_key}.pkl")


def save_to_cache(key, data):
    """Save data to the cache."""
    filename = cache_filename(key)
    with open(filename, 'wb') as f:
        pickle.dump(data, f)


def load_from_cache(key, expiry=timedelta(days=1)):
    """Load data from the cache if available and not expired."""
    filename = cache_filename(key)
    if os.path.exists(filename):
        file_mtime = datetime.fromtimestamp(os.path.getmtime(filename))
        if datetime.now() - file_mtime < expiry:
            with open(filename, 'rb') as f:
                return pickle.load(f)
    return None
