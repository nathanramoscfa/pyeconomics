# .semgrep/tests/unsafe-yaml.py
# Test cases for .semgrep/rules/unsafe-yaml.yaml (semgrep --test).
# Deliberately unsafe code: excluded from the bandit and semgrep hooks.
import yaml
from yaml import SafeLoader


def cases(stream):
    # ruleid: unsafe-yaml
    yaml.load(stream)
    # ruleid: unsafe-yaml
    yaml.load(stream, Loader=yaml.Loader)
    # ruleid: unsafe-yaml
    yaml.load(stream, Loader=yaml.FullLoader)
    # ruleid: unsafe-yaml
    yaml.load(stream, Loader=yaml.UnsafeLoader)
    # ruleid: unsafe-yaml
    yaml.load_all(stream)
    # ruleid: unsafe-yaml
    yaml.full_load(stream)
    # ruleid: unsafe-yaml
    yaml.unsafe_load(stream)

    # ok: unsafe-yaml
    yaml.safe_load(stream)
    # ok: unsafe-yaml
    yaml.safe_load_all(stream)
    # ok: unsafe-yaml
    yaml.load(stream, Loader=yaml.SafeLoader)
    # ok: unsafe-yaml
    yaml.load(stream, Loader=yaml.CSafeLoader)
    # ok: unsafe-yaml
    yaml.load(stream, Loader=SafeLoader)
    # ok: unsafe-yaml
    yaml.load_all(stream, Loader=yaml.SafeLoader)
