import os
from datetime import datetime, timedelta
from hashlib import sha256

import pytest

from pyeconomics.api.cache_manager import (
    CACHE_DIR, cache_filename, save_to_cache, load_from_cache
)


@pytest.fixture(scope='function', autouse=True)
def setup_and_teardown():
    """Setup and teardown for tests."""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    yield
    # Cleanup after test
    for filename in os.listdir(CACHE_DIR):
        file_path = os.path.join(CACHE_DIR, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)


def test_cache_filename():
    key = 'test_key'
    filename = cache_filename(key)
    hashed_key = sha256(key.encode('utf-8')).hexdigest()
    expected_filename = os.path.join(CACHE_DIR, f"{hashed_key}.pkl")
    assert filename == expected_filename


def test_save_to_cache():
    key = 'test_key'
    data = {'value': 42}
    save_to_cache(key, data)
    filename = cache_filename(key)
    assert os.path.exists(filename)


def test_load_from_cache():
    key = 'test_key'
    data = {'value': 42}
    save_to_cache(key, data)
    loaded_data = load_from_cache(key)
    assert loaded_data == data


def test_load_from_cache_expired():
    key = 'test_key'
    data = {'value': 42}
    save_to_cache(key, data)
    # Manually set the file's modified time to simulate expiry
    filename = cache_filename(key)
    old_time = datetime.now() - timedelta(days=2)
    old_timestamp = old_time.timestamp()
    os.utime(filename, (old_timestamp, old_timestamp))
    loaded_data = load_from_cache(key, expiry=timedelta(days=1))
    assert loaded_data is None


def test_load_from_cache_nonexistent_key():
    key = 'nonexistent_key'
    loaded_data = load_from_cache(key)
    assert loaded_data is None


def test_cache_directory_creation():
    assert os.path.exists(CACHE_DIR)


if __name__ == '__main__':
    pytest.main()
