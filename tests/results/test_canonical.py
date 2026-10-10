# tests/results/test_canonical.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""Canonical JSON (RFC 8785): the RFC's vectors, an independent oracle, round trips."""

from __future__ import annotations

import datetime as dt
import json
import math
import struct
from typing import Any

import pytest
import rfc8785
from hypothesis import given
from hypothesis import strategies as st

from pyeconomics.core.canonical import (
    MAX_DEPTH,
    MAX_EXACT_INTEGER,
    canonical_json,
    canonical_sha256,
)

# RFC 8785 Appendix B, Table 1: an IEEE 754 double (hex) and its serialization.
APPENDIX_B = [
    ("0000000000000000", "0"),
    ("8000000000000000", "0"),
    ("0000000000000001", "5e-324"),
    ("8000000000000001", "-5e-324"),
    ("7fefffffffffffff", "1.7976931348623157e+308"),
    ("ffefffffffffffff", "-1.7976931348623157e+308"),
    ("4340000000000000", "9007199254740992"),
    ("c340000000000000", "-9007199254740992"),
    ("4430000000000000", "295147905179352830000"),
    ("44b52d02c7e14af5", "9.999999999999997e+22"),
    ("44b52d02c7e14af6", "1e+23"),
    ("44b52d02c7e14af7", "1.0000000000000001e+23"),
    ("444b1ae4d6e2ef4e", "999999999999999700000"),
    ("444b1ae4d6e2ef4f", "999999999999999900000"),
    ("444b1ae4d6e2ef50", "1e+21"),
    ("3eb0c6f7a0b5ed8c", "9.999999999999997e-7"),
    ("3eb0c6f7a0b5ed8d", "0.000001"),
    ("41b3de4355555553", "333333333.3333332"),
    ("41b3de4355555554", "333333333.33333325"),
    ("41b3de4355555555", "333333333.3333333"),
    ("41b3de4355555556", "333333333.3333334"),
    ("41b3de4355555557", "333333333.33333343"),
    ("becbf647612f3696", "-0.0000033333333333333333"),
    ("43143ff3c1cb0959", "1424953923781206.2"),
]


def double(hex_bits: str) -> float:
    return struct.unpack(">d", bytes.fromhex(hex_bits))[0]  # type: ignore[no-any-return]


@pytest.mark.parametrize(("bits", "expected"), APPENDIX_B)
def test_appendix_b_number_samples(bits: str, expected: str) -> None:
    assert canonical_json(double(bits)) == expected.encode()


@pytest.mark.parametrize("bits", ["7fffffffffffffff", "7ff0000000000000"])
def test_appendix_b_nan_and_infinity_are_errors(bits: str) -> None:
    with pytest.raises(ValueError, match="no representation"):
        canonical_json(double(bits))
    with pytest.raises(ValueError, match="no representation"):
        canonical_json({"nested": [double(bits)]})


def test_the_rfc_key_sorting_example() -> None:
    """Section 3.2.3: keys sort by UTF-16 code unit, so the emoji precedes U+FB33."""
    unsorted = {
        "€": "Euro Sign",
        "\r": "Carriage Return",
        "דּ": "Hebrew Letter Dalet With Dagesh",
        "1": "One",
        "\U0001f600": "Emoji: Grinning Face",
        "\u0080": "Control",
        "ö": "Latin Small Letter O With Diaeresis",
    }
    text = canonical_json(unsorted).decode("utf-8")
    keys = list(json.loads(text))
    assert keys == ["\r", "1", "\u0080", "ö", "€", "\U0001f600", "דּ"]
    assert text.startswith('{"\\r":"Carriage Return","1":"One","\u0080":"Control"')


def test_the_rfc_section_3_2_4_example() -> None:
    parsed = json.loads(
        r"""{"numbers": [333333333.33333329, 1E30, 4.50, 2e-3,
                         0.000000000000000000000000001],
             "string": "\u20ac$\u000F\u000aA'\u0042\u0022\u005c\\\"/",
             "literals": [null, true, false]}"""
    )
    expected = (
        r"""{"literals":[null,true,false],"numbers":[333333333.3333333,1e+30,4.5,"""
        r"""0.002,1e-27],"string":"€$\u000f\nA'B\"\\\\\"/"}"""
    )
    assert canonical_json(parsed) == expected.encode("utf-8")


def test_the_rfc_sample_is_the_independent_packages_output_too() -> None:
    sample = {"b": [1e30, 4.5, 0.002, 1e-27], "a": "€\x0f\n'\"\\/", "c": None}
    assert canonical_json(sample) == rfc8785.dumps(sample)


def test_scalars() -> None:
    assert canonical_json(None) == b"null"
    assert canonical_json(True) == b"true"  # noqa: FBT003
    assert canonical_json(False) == b"false"  # noqa: FBT003
    assert canonical_json(0) == b"0"
    assert canonical_json(-7) == b"-7"
    assert canonical_json(1.0) == b"1"
    assert canonical_json(-1.5e-7) == b"-1.5e-7"
    assert canonical_json("") == b'""'


def test_a_bool_is_not_a_number() -> None:
    assert canonical_json([True, 1, 1.0]) == b"[true,1,1]"


def test_integers_are_exact_within_two_to_the_53() -> None:
    assert canonical_json(MAX_EXACT_INTEGER) == b"9007199254740992"
    assert canonical_json(-MAX_EXACT_INTEGER) == b"-9007199254740992"
    for beyond in (MAX_EXACT_INTEGER + 1, -MAX_EXACT_INTEGER - 1, 10**30):
        with pytest.raises(ValueError, match="not exact in a double"):
            canonical_json(beyond)


def test_control_characters_and_quotes_are_escaped_as_json_stringify_does() -> None:
    text = "".join(chr(code) for code in range(0x20)) + '"\\\x7f'
    expected = (
        '"\\u0000\\u0001\\u0002\\u0003\\u0004\\u0005\\u0006\\u0007\\b\\t\\n'
        "\\u000b\\f\\r\\u000e\\u000f\\u0010\\u0011\\u0012\\u0013\\u0014\\u0015"
        "\\u0016\\u0017\\u0018\\u0019\\u001a\\u001b\\u001c\\u001d\\u001e\\u001f"
        '\\"\\\\\x7f"'
    )
    assert canonical_json(text) == expected.encode()
    assert json.loads(canonical_json(text)) == text


def test_non_ascii_text_is_written_as_utf8_not_escaped() -> None:
    assert canonical_json("é€😀") == '"é€😀"'.encode()


def test_dates_are_iso_8601_strings() -> None:
    assert canonical_json(dt.date(2026, 10, 9)) == b'"2026-10-09"'
    stamp = dt.datetime(2026, 10, 9, 12, 30, tzinfo=dt.UTC)
    assert canonical_json(stamp) == b'"2026-10-09T12:30:00+00:00"'


def test_tuples_are_arrays_and_mappings_are_objects() -> None:
    assert canonical_json({"a": (1, 2), "b": {}}) == b'{"a":[1,2],"b":{}}'
    assert canonical_json([]) == b"[]"


@pytest.mark.parametrize("value", [{1, 2}, b"bytes", object(), 1 + 2j, {"a": {1}}])
def test_an_unsupported_type_is_refused(value: object) -> None:
    with pytest.raises(TypeError, match="cannot represent"):
        canonical_json(value)


def test_object_keys_must_be_strings() -> None:
    with pytest.raises(TypeError, match="keys are strings"):
        canonical_json({1: "one"})


def test_lone_surrogates_are_refused() -> None:
    with pytest.raises(ValueError, match="lone surrogates"):
        canonical_json("\ud800")
    with pytest.raises(ValueError, match="lone surrogates"):
        canonical_json({"\ud800": 1})


def test_nesting_is_bounded() -> None:
    value: object = 1
    for _ in range(MAX_DEPTH):
        value = [value]
    assert canonical_json(value).startswith(b"[[[")
    with pytest.raises(ValueError, match="nest at most"):
        canonical_json([value])


def test_the_hash_is_the_sha256_of_the_canonical_bytes() -> None:
    assert (
        canonical_sha256({"a": 1})
        == "015abd7f5cc57a2dd94b7590f04ad8084273905ee33ec5cebeae62276a97f862"
    )
    assert canonical_sha256({"a": 1, "b": 2}) == canonical_sha256({"b": 2, "a": 1})


# --- property tests ------------------------------------------------------------

finite_floats = st.floats(allow_nan=False, allow_infinity=False)
exact_integers = st.integers(-MAX_EXACT_INTEGER, MAX_EXACT_INTEGER)
text = st.text()  # hypothesis draws no lone surrogates by default
json_values = st.recursive(
    st.none() | st.booleans() | exact_integers | finite_floats | text,
    lambda children: (
        st.lists(children, max_size=4) | st.dictionaries(text, children, max_size=4)
    ),
    max_leaves=12,
)


@given(json_values)
def test_it_agrees_with_the_independent_rfc8785_package(value: Any) -> None:  # noqa: ANN401
    assert canonical_json(value) == rfc8785.dumps(value)


@given(finite_floats)
def test_every_finite_float_round_trips_exactly(value: float) -> None:
    # ECMAScript prints 5.780414299433543e16 as 57804142994335430, which Python's
    # json reads as an exact int; the double it names is the original.
    loaded = json.loads(canonical_json(value))
    assert isinstance(loaded, int | float)
    assert float(loaded) == value
    if value != 0:
        assert math.copysign(1.0, float(loaded)) == math.copysign(1.0, value)


@given(json_values)
def test_json_loads_of_the_canonical_bytes_is_lossless(value: object) -> None:
    # parse_int=float because every JSON number is a double (RFC 8785 section 3.2.2.3).
    loaded = json.loads(canonical_json(value), parse_int=float)
    assert canonical_json(loaded) == canonical_json(value)


@given(st.dictionaries(text, exact_integers, max_size=6))
def test_key_order_does_not_change_the_bytes(mapping: dict[str, int]) -> None:
    reversed_mapping = dict(reversed(list(mapping.items())))
    assert canonical_json(mapping) == canonical_json(reversed_mapping)
