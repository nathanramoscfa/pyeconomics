# src/pyeconomics/core/canonical.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
r"""Canonical JSON: RFC 8785, the JSON Canonicalization Scheme (ADR-0008 decision 12).

Two equal values serialize to the same bytes on every surface, which is what a
manifest hash and the cross-surface parity tests compare. The scheme:

- UTF-8, with no insignificant whitespace;
- object keys sorted by their UTF-16 code units (not by code point, so an emoji
  sorts before U+FB33);
- strings escaped as ``JSON.stringify`` escapes them: ``\"``, ``\\``, the
  five short control escapes and ``\u00xx`` in lowercase for the rest, with
  every other character, DEL and non-ASCII included, written as itself;
- numbers in ECMAScript's shortest round-trip form (RFC 8785 section 3.2.2.3),
  derived here from the shortest ``repr`` of a ``float``;
- no NaN or infinity, and an integer only when it is exact in a double
  (within ±2\ :sup:`53`);
- dates as ISO 8601 strings.

The writer accepts ``None``, ``bool``, ``int``, ``float``, ``str``, ``date`` and
``datetime``, mappings with string keys, and lists and tuples. Anything else
raises, so a value a surface cannot reproduce never gets a hash. It uses no
library beyond the standard one; the test suite checks it against the RFC's
vectors and against the independent ``rfc8785`` package.

ECMAScript prints a large whole-number double such as ``5.78e16`` without an
exponent, so Python's ``json.loads`` reads it back as an exact ``int``. The
double it names is the original (``float(loaded)``), and a model's float field
accepts it. To canonicalize parsed data again, load it with
``json.loads(text, parse_int=float)``: an ``int`` beyond 2\ :sup:`53` is refused.

Examples
--------
>>> from pyeconomics.core.canonical import canonical_json
>>> canonical_json({"b": [1.0, 2e-7, None], "a": True})
b'{"a":true,"b":[1,2e-7,null]}'
>>> canonical_json(333333333.33333329)
b'333333333.3333333'

"""

from __future__ import annotations

import datetime as dt
import hashlib
import math
import re
from collections.abc import Mapping
from decimal import Decimal
from typing import Final

__all__ = [
    "MAX_DEPTH",
    "MAX_EXACT_INTEGER",
    "canonical_json",
    "canonical_sha256",
]

#: The largest integer a double holds exactly: 2**53 (RFC 8785 section 3.2.2.3).
MAX_EXACT_INTEGER: Final = 2**53
#: The deepest nesting accepted, so a hostile value cannot exhaust the stack.
MAX_DEPTH: Final = 100

#: ECMAScript prints a number without an exponent while its decimal point sits
#: no more than 21 digits from the first digit.
_DIGITS_BEFORE_EXPONENT: Final = 21
#: ...and prints small numbers as 0.000001 but 1e-7.
_ZEROS_BEFORE_EXPONENT: Final = -6

_NEEDS_ESCAPE = re.compile(r'["\\\x00-\x1f]')
_SHORT_ESCAPES: Final = {
    '"': '\\"',
    "\\": "\\\\",
    "\b": "\\b",
    "\t": "\\t",
    "\n": "\\n",
    "\f": "\\f",
    "\r": "\\r",
}


def _escape(match: re.Match[str]) -> str:
    character = match.group()
    return _SHORT_ESCAPES.get(character) or f"\\u{ord(character):04x}"


def _string(value: str) -> str:
    return f'"{_NEEDS_ESCAPE.sub(_escape, str.__str__(value))}"'


def _integer(value: int) -> str:
    if abs(value) > MAX_EXACT_INTEGER:
        msg = (
            f"the integer {value} is not exact in a double; canonical JSON carries "
            f"integers only within ±{MAX_EXACT_INTEGER}"
        )
        raise ValueError(msg)
    return str(int(value))


def _float(value: float) -> str:
    """Format a float as ECMAScript's ``Number::toString`` does."""
    if not math.isfinite(value):
        msg = f"canonical JSON has no representation for {value!r}"
        raise ValueError(msg)
    if value == 0:
        return "0"  # also -0.0
    sign = "-" if value < 0 else ""
    _, decimal_digits, raw_exponent = Decimal(repr(abs(value))).as_tuple()
    exponent = int(raw_exponent)  # a finite Decimal's exponent is an int
    digits = list(decimal_digits)
    while digits[-1] == 0:
        digits.pop()
        exponent += 1
    text = "".join(map(str, digits))
    count = len(text)
    point = count + exponent  # value = 0.<digits> x 10**point
    if count <= point <= _DIGITS_BEFORE_EXPONENT:
        body = text + "0" * (point - count)
    elif 0 < point <= _DIGITS_BEFORE_EXPONENT:
        body = f"{text[:point]}.{text[point:]}"
    elif _ZEROS_BEFORE_EXPONENT < point <= 0:
        body = f"0.{'0' * -point}{text}"
    else:
        power = point - 1
        mantissa = text if count == 1 else f"{text[0]}.{text[1:]}"
        body = f"{mantissa}e{'+' if power >= 0 else '-'}{abs(power)}"
    return sign + body


def _utf16_key(key: str) -> bytes:
    # Big-endian UTF-16 bytes compare as UTF-16 code units do.
    return key.encode("utf-16-be")


def _scalar(value: object) -> str | None:
    """Write a scalar, or return ``None`` for anything else."""
    if value is None or isinstance(value, bool):
        return "null" if value is None else str(value).lower()
    if isinstance(value, int):
        return _integer(value)
    if isinstance(value, float):
        return _float(value)
    if isinstance(value, str):
        return _string(value)
    if isinstance(value, dt.datetime | dt.date):
        return _string(value.isoformat())
    return None


def _write(value: object, out: list[str], depth: int) -> None:
    if depth > MAX_DEPTH:
        msg = f"canonical JSON values may nest at most {MAX_DEPTH} levels deep"
        raise ValueError(msg)
    scalar = _scalar(value)
    if scalar is not None:
        out.append(scalar)
    elif isinstance(value, Mapping):
        _write_object(value, out, depth)
    elif isinstance(value, list | tuple):
        out.append("[")
        for index, item in enumerate(value):
            if index:
                out.append(",")
            _write(item, out, depth + 1)
        out.append("]")
    else:
        msg = f"canonical JSON cannot represent a {type(value).__name__}"
        raise TypeError(msg)


def _write_object(value: Mapping[object, object], out: list[str], depth: int) -> None:
    keys: list[str] = []
    for key in value:
        if not isinstance(key, str):
            msg = f"canonical JSON object keys are strings, not {type(key).__name__}"
            raise TypeError(msg)
        keys.append(key)
    keys.sort(key=_utf16_key)
    out.append("{")
    for index, key in enumerate(keys):
        if index:
            out.append(",")
        out.append(_string(key))
        out.append(":")
        _write(value[key], out, depth + 1)
    out.append("}")


def canonical_json(value: object) -> bytes:
    r"""Serialize ``value`` as RFC 8785 canonical JSON, in UTF-8.

    Parameters
    ----------
    value
        ``None``, a ``bool``, ``int``, ``float``, ``str``, ``date`` or
        ``datetime``, a mapping with string keys, or a list or tuple of these.

    Returns
    -------
    bytes
        The canonical form: the same bytes for equal values, on every platform.

    Raises
    ------
    ValueError
        For NaN or infinity, an integer beyond ±2\ :sup:`53`, a string with a
        lone surrogate, or nesting deeper than :data:`MAX_DEPTH`.
    TypeError
        For a value of any other type, or an object key that is not a string.

    Examples
    --------
    >>> canonical_json({"\u20ac": 1, "\r": 2, "1": 3})
    b'{"\\r":2,"1":3,"\xe2\x82\xac":1}'
    >>> canonical_json(1e21), canonical_json(1e-6), canonical_json(-0.0)
    (b'1e+21', b'0.000001', b'0')
    """
    out: list[str] = []
    try:
        _write(value, out, 0)
        return "".join(out).encode("utf-8")
    except UnicodeEncodeError as error:
        msg = "canonical JSON strings must not contain lone surrogates"
        raise ValueError(msg) from error


def canonical_sha256(value: object) -> str:
    """Return the SHA-256, in lowercase hex, of ``value``'s canonical JSON.

    Examples
    --------
    >>> canonical_sha256({"a": 1})
    '015abd7f5cc57a2dd94b7590f04ad8084273905ee33ec5cebeae62276a97f862'
    """
    return hashlib.sha256(canonical_json(value)).hexdigest()
