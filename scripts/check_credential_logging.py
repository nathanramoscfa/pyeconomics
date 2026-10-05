# scripts/check_credential_logging.py

"""
Check that an INSTALLED pyeconomics never logs the FRED API key.

The release workflow's smoke job runs this against the version it just
published. It makes the same assertion as tests/test_credential_logging.py:
with the root logger capturing DEBUG, it builds FredClient from a sentinel
key through the import-time client, the argument, FRED_API_KEY and a mocked
keyring, and fails if the sentinel appears in any record's message,
arguments or formatted output. fredapi.Fred is mocked, so no request is
made.

It refuses to run against the source checkout (an editable install or the
working directory on sys.path), because that would test the repository
rather than the artifact.

Usage:
    python scripts/check_credential_logging.py

Exit status: 0 when no record carries the key, 1 on a leak, 2 when it
refuses to run.
"""

import importlib.util
import logging
import os
import sys
from importlib.metadata import version
from pathlib import Path
from unittest import mock

SENTINEL = 'sentinel-not-a-fred-key'
CHECKOUT = Path(__file__).resolve().parent.parent


class _RecordCapture(logging.Handler):
    """Keeps every record that reaches the root logger."""

    def __init__(self):
        super().__init__(level=logging.DEBUG)
        self.setFormatter(logging.Formatter(
            '%(asctime)s %(name)s %(levelname)s %(pathname)s:%(lineno)d '
            '%(message)s'))
        self.records = []

    def emit(self, record):
        self.records.append(record)


def _inside_checkout(path):
    return Path(path).resolve().is_relative_to(CHECKOUT)


def _leaks(handler):
    found = []
    for record in handler.records:
        surfaces = {
            'message': str(record.msg),
            'args': repr(record.args),
            'formatted message': record.getMessage(),
            'formatted output': handler.format(record),
        }
        for surface, text in surfaces.items():
            if SENTINEL in text:
                found.append(f'{surface} of a {record.levelname} record '
                             f'from {record.pathname}:{record.lineno}')
    return found


def _expect_key(fred, case, failures):
    if fred.call_args != mock.call(api_key=SENTINEL):
        failures.append(f'{case}: fredapi.Fred was not built from the '
                        f'sentinel, so the case proves nothing')
    fred.reset_mock()


def main():
    # Locate the package without importing it: importing builds the
    # import-time client, which must happen under capture.
    spec = importlib.util.find_spec('pyeconomics')
    if spec is None or spec.origin is None:
        print('pyeconomics is not installed in this environment.',
              file=sys.stderr)
        return 2
    if _inside_checkout(spec.origin):
        print(f'Refusing to run: pyeconomics resolves to {spec.origin}, '
              f'inside the checkout {CHECKOUT}. Install the built artifact '
              f'into a virtual environment outside the checkout.',
              file=sys.stderr)
        return 2

    root = logging.getLogger()
    capture = _RecordCapture()
    root.addHandler(capture)
    root.setLevel(logging.DEBUG)

    failures = []
    os.environ['FRED_API_KEY'] = SENTINEL
    # fred_api binds `from fredapi import Fred` at import, so patching the
    # source before the first import puts the mock under every client.
    with mock.patch('fredapi.Fred') as fred:
        import pyeconomics
        from pyeconomics.api import fred_api

        if _inside_checkout(pyeconomics.__file__):
            print(f'Refusing to run: pyeconomics was imported from '
                  f'{pyeconomics.__file__}, inside the checkout.',
                  file=sys.stderr)
            return 2
        _expect_key(fred, 'import-time client', failures)

        fred_api.FredClient.reset_instance()
        del os.environ['FRED_API_KEY']
        fred_api.FredClient(api_key=SENTINEL)
        _expect_key(fred, 'argument', failures)

        fred_api.FredClient.reset_instance()
        os.environ['FRED_API_KEY'] = SENTINEL
        fred_api.FredClient()
        _expect_key(fred, 'FRED_API_KEY', failures)

        fred_api.FredClient.reset_instance()
        del os.environ['FRED_API_KEY']
        keyring = mock.MagicMock()
        keyring.get_password.return_value = SENTINEL
        with mock.patch.object(fred_api, 'keyring', keyring), \
                mock.patch.object(fred_api, 'KEYRING_AVAILABLE', True):
            fred_api.FredClient()
        _expect_key(fred, 'keyring', failures)

        fred_api.FredClient.reset_instance()

    root.removeHandler(capture)

    if not capture.records:
        failures.append('no log record was captured, so the check proves '
                        'nothing')
    leaks = _leaks(capture)
    for leak in leaks:
        print(f'LEAK: the FRED API key reached the {leak}', file=sys.stderr)
    for failure in failures:
        print(f'FAILED: {failure}', file=sys.stderr)
    if leaks or failures:
        return 1

    print(f'OK: pyeconomics {version("pyeconomics")} from '
          f'{Path(pyeconomics.__file__).parent}; {len(capture.records)} log '
          f'records checked across 4 key sources, none carries the key.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
