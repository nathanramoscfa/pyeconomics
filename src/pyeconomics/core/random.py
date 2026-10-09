# src/pyeconomics/core/random.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""Seeded random number generation (ADR-0008 decision 7).

Every stochastic model takes an integer ``seed`` input between
:data:`SEED_MIN` and :data:`SEED_MAX`, with a documented default
(:data:`DEFAULT_SEED` unless the model says otherwise), and draws only from
:func:`generator`: a NumPy ``Generator`` over a ``PCG64`` bit generator. There
is no global or unseeded state. :data:`SEED_MAX` is ``2**53 - 1``, the largest
integer canonical JSON carries exactly.

NumPy promises identical ``Generator`` streams only within a feature release
(NEP 19), so a result's manifest records :func:`provenance`: the seed, the bit
generator and NumPy's version.

Examples
--------
>>> from pyeconomics.core import generator
>>> first = generator(7).standard_normal(3)
>>> second = generator(7).standard_normal(3)
>>> bool((first == second).all())
True

"""

from __future__ import annotations

import operator
from dataclasses import dataclass
from typing import Final

import numpy as np

from pyeconomics.core.errors import InputError

__all__ = [
    "BIT_GENERATOR",
    "DEFAULT_SEED",
    "SEED_MAX",
    "SEED_MIN",
    "RandomProvenance",
    "generator",
    "provenance",
]

#: The smallest seed.
SEED_MIN: Final = 0
#: The largest seed: 2**53 - 1, exact in canonical JSON (ADR-0008 decision 12).
SEED_MAX: Final = 2**53 - 1
#: The seed a stochastic model uses unless it documents another default.
DEFAULT_SEED: Final = 0
#: The NumPy bit generator every draw comes from.
BIT_GENERATOR: Final = "PCG64"


def _seed(seed: int) -> int:
    if isinstance(seed, bool):
        msg = "the seed must be an integer, not a bool"
        raise InputError(msg)
    try:
        value = operator.index(seed)
    except TypeError as error:
        msg = f"the seed must be an integer, not {type(seed).__name__}"
        raise InputError(msg) from error
    if not SEED_MIN <= value <= SEED_MAX:
        msg = f"the seed must be between {SEED_MIN} and {SEED_MAX}, not {value}"
        raise InputError(msg)
    return value


def generator(seed: int) -> np.random.Generator:
    """Return a new random generator seeded with ``seed``.

    Parameters
    ----------
    seed
        An integer from :data:`SEED_MIN` to :data:`SEED_MAX`.

    Returns
    -------
    numpy.random.Generator
        ``Generator(PCG64(seed))``: the same seed gives the same draws under
        one NumPy feature release.

    Raises
    ------
    InputError
        If ``seed`` is not an integer in range.

    """
    return np.random.Generator(np.random.PCG64(_seed(seed)))


@dataclass(frozen=True, slots=True)
class RandomProvenance:
    """What a manifest records about a stochastic computation."""

    seed: int
    bit_generator: str
    numpy_version: str


def provenance(seed: int) -> RandomProvenance:
    """Return the provenance of draws made with ``seed``.

    Examples
    --------
    >>> record = provenance(7)
    >>> record.seed, record.bit_generator
    (7, 'PCG64')

    """
    return RandomProvenance(
        seed=_seed(seed), bit_generator=BIT_GENERATOR, numpy_version=np.__version__
    )
