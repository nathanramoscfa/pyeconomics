# tests/unit/core/test_random.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""Seeded generators: determinism, independence, bounds and provenance."""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from pyeconomics.core import (
    BIT_GENERATOR,
    DEFAULT_SEED,
    SEED_MAX,
    SEED_MIN,
    InputError,
    generator,
    provenance,
)


def test_one_seed_gives_identical_draws() -> None:
    first = generator(20261009)
    second = generator(20261009)
    np.testing.assert_array_equal(
        first.standard_normal(1_000), second.standard_normal(1_000)
    )
    assert first.integers(0, 1_000_000) == second.integers(0, 1_000_000)


def test_different_seeds_give_different_draws() -> None:
    draws = {seed: generator(seed).random(16) for seed in (0, 1, 2, SEED_MAX)}
    for seed, values in draws.items():
        for other, others in draws.items():
            if seed != other:
                assert not np.array_equal(values, others), (seed, other)


def test_generators_are_independent_objects() -> None:
    first = generator(DEFAULT_SEED)
    head = first.random(4)
    np.testing.assert_array_equal(generator(DEFAULT_SEED).random(4), head)


def test_the_bit_generator_is_pcg64() -> None:
    assert BIT_GENERATOR == "PCG64"
    assert isinstance(generator(0).bit_generator, np.random.PCG64)


def test_seed_bounds_are_canonical_json_safe() -> None:
    assert SEED_MIN == 0
    assert SEED_MAX == 2**53 - 1
    assert DEFAULT_SEED == 0
    generator(SEED_MIN)
    generator(SEED_MAX)
    generator(np.int64(42))  # numpy integers are accepted


@pytest.mark.parametrize("seed", [-1, SEED_MAX + 1, 2**64])
def test_out_of_range_seeds_are_refused(seed: int) -> None:
    with pytest.raises(InputError, match="between 0 and"):
        generator(seed)


@pytest.mark.parametrize("seed", [1.0, "1", None, True])
def test_non_integer_seeds_are_refused(seed: Any) -> None:  # noqa: ANN401 - wrong types on purpose
    with pytest.raises(InputError, match="integer"):
        generator(seed)


def test_provenance_records_seed_bit_generator_and_numpy_version() -> None:
    record = provenance(7)
    assert (record.seed, record.bit_generator) == (7, "PCG64")
    assert record.numpy_version == np.__version__
    with pytest.raises(InputError):
        provenance(-1)
