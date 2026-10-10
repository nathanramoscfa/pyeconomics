# src/pyeconomics/core/descriptive.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
r"""Descriptive statistics of a series: moments, semideviation and drawdown.

The estimators are named, because each has rivals:

- mean: :math:`\bar{x} = \frac{1}{n}\sum x_i`;
- sample variance: :math:`s^2 = \frac{1}{n - 1}\sum (x_i - \bar{x})^2`
  (``ddof=1``);
- semideviation below the mean:
  :math:`\sqrt{\frac{1}{n - 1}\sum \min(x_i - \bar{x}, 0)^2}`;
- semideviation below a target *T*: :math:`\sqrt{\frac{1}{n}\sum \min(x_i - T,
  0)^2}`;
- skewness, G1: :math:`\frac{\sqrt{n(n-1)}}{n-2}\,\frac{m_3}{m_2^{3/2}}`;
- excess kurtosis, G2:
  :math:`\frac{n-1}{(n-2)(n-3)}\left[(n+1)\frac{m_4}{m_2^2} - 3(n-1)\right]`;
- maximum drawdown: :math:`\max_{j}\left(1 - x_j / \max_{i \le j} x_i\right)`;

with :math:`m_k = \frac{1}{n}\sum (x_i - \bar{x})^k`. G1 and G2 are the
adjusted estimators Joanes and Gill (1998) compare, the ones SAS, SPSS and
Excel report, and SciPy's ``skew`` and ``kurtosis`` with ``bias=False``.

Means and sums of squares use a corrected two-pass method (Chan, Golub and
LeVeque, 1983), so a series with a large offset and a small spread, such as
NIST's NumAcc1, keeps its digits.

Examples
--------
>>> from pyeconomics.core import sample_variance
>>> sample_variance([10000001.0, 10000003.0, 10000002.0])
1.0

"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

import numpy as np
from numpy.typing import NDArray

from pyeconomics.core.errors import DomainError, InputError

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = [
    "Drawdown",
    "Moments",
    "max_drawdown",
    "sample_mean",
    "sample_moments",
    "sample_variance",
    "semideviation_below_mean",
    "semideviation_below_target",
]

#: A spread this many machine epsilons of the data's magnitude, or less, counts
#: as no spread at all: the deviations are rounding error.
_ZERO_SPREAD_ULPS: Final = 64

_KURTOSIS_MIN: Final = 4

type _Vector = NDArray[np.float64]


def _series(values: Sequence[float], minimum: int) -> _Vector:
    data = np.asarray(values, dtype=np.float64)
    if data.ndim != 1 or not np.all(np.isfinite(data)):
        msg = "a series must be a one-dimensional array of finite numbers"
        raise InputError(msg)
    if data.size < minimum:
        msg = f"the series needs at least {minimum} values, not {data.size}"
        raise InputError(msg)
    return data


def _centred(data: _Vector) -> tuple[float, _Vector]:
    """Return the mean and the deviations from it, after one correction pass."""
    mean = float(np.mean(data))
    deviations = data - mean
    correction = float(np.mean(deviations))
    return mean + correction, deviations - correction


def _no_spread(data: _Vector, deviations: _Vector) -> bool:
    scale = float(np.max(np.abs(data)))
    limit = _ZERO_SPREAD_ULPS * float(np.finfo(np.float64).eps) * scale
    return bool(np.max(np.abs(deviations)) <= limit)


def sample_mean(values: Sequence[float]) -> float:
    """Return the arithmetic mean, with one correction pass.

    Examples
    --------
    >>> sample_mean([10000001.0, 10000003.0, 10000002.0])
    10000002.0

    """
    return _centred(_series(values, 1))[0]


def sample_variance(values: Sequence[float], *, ddof: int = 1) -> float:
    """Return the variance with ``n - ddof`` in the denominator.

    The default ``ddof=1`` is the unbiased sample variance.

    Raises
    ------
    InputError
        If the series has no more than ``ddof`` values.

    """
    data = _series(values, ddof + 1)
    _, deviations = _centred(data)
    return float(np.sum(deviations * deviations)) / (data.size - ddof)


def semideviation_below_mean(values: Sequence[float]) -> float:
    """Return the semideviation below the sample mean, with ``n - 1``.

    Every observation counts in the denominator; only those below the mean
    contribute to the sum.

    Examples
    --------
    >>> semideviation_below_mean([1.0, 2.0, 3.0])
    0.7071067811865476

    """
    data = _series(values, 2)
    _, deviations = _centred(data)
    below = np.minimum(deviations, 0.0)
    return math.sqrt(float(np.sum(below * below)) / (data.size - 1))


def semideviation_below_target(values: Sequence[float], target: float) -> float:
    """Return the downside deviation below ``target``, with ``n``.

    The target is given, not estimated, so the denominator is ``n``.

    Examples
    --------
    >>> semideviation_below_target([-0.02, 0.01, 0.03, -0.04], 0.0)
    0.022360679774997897

    """
    data = _series(values, 1)
    if not math.isfinite(target):
        msg = f"the target must be finite, not {target!r}"
        raise InputError(msg)
    below = np.minimum(data - target, 0.0)
    return math.sqrt(float(np.sum(below * below)) / data.size)


@dataclass(frozen=True, slots=True)
class Moments:
    """The shape of a sample: adjusted skewness (G1) and excess kurtosis (G2)."""

    skewness: float
    excess_kurtosis: float


def sample_moments(values: Sequence[float]) -> Moments:
    """Return the G1 skewness and G2 excess kurtosis of at least four values.

    Raises
    ------
    InputError
        If there are fewer than four values.
    DomainError
        If the values have no spread: both statistics divide by the variance.

    Examples
    --------
    >>> shape = sample_moments([1.0, 2.0, 3.0, 4.0])
    >>> shape.skewness, round(shape.excess_kurtosis, 12)
    (0.0, -1.2)

    """
    data = _series(values, _KURTOSIS_MIN)
    _, deviations = _centred(data)
    if _no_spread(data, deviations):
        msg = "the values have no spread, so skewness and kurtosis are undefined"
        raise DomainError(msg)
    n = data.size
    # G1 and G2 do not change with scale: dividing by the largest deviation
    # keeps m2 away from underflow for data with a tiny absolute spread.
    deviations = deviations / float(np.max(np.abs(deviations)))
    squares = deviations * deviations
    m2 = float(np.mean(squares))
    m3 = float(np.mean(squares * deviations))
    m4 = float(np.mean(squares * squares))
    g1 = m3 / m2**1.5
    skewness = g1 * math.sqrt(n * (n - 1)) / (n - 2)
    kurtosis = (n - 1) / ((n - 2) * (n - 3)) * ((n + 1) * m4 / (m2 * m2) - 3 * (n - 1))
    return Moments(skewness=skewness, excess_kurtosis=kurtosis)


@dataclass(frozen=True, slots=True)
class Drawdown:
    """The largest peak-to-trough decline of a value series."""

    depth: float
    """The decline as a fraction of the peak, from 0 to 1."""
    peak: int
    """The position of the peak, counting from 0."""
    trough: int
    """The position of the trough, counting from 0."""


def max_drawdown(values: Sequence[float]) -> Drawdown:
    """Return the maximum drawdown of positive values, with its positions.

    The peak is the running maximum before the trough (the first, if the
    maximum repeats). With no decline the depth is 0 and both positions are 0.

    Raises
    ------
    InputError
        If a value is not positive and finite, or there is none.

    Examples
    --------
    >>> max_drawdown([100.0, 120.0, 90.0, 130.0, 117.0])
    Drawdown(depth=0.25, peak=1, trough=2)

    """
    data = _series(values, 1)
    if not np.all(data > 0):
        msg = "a drawdown needs positive values"
        raise InputError(msg)
    peaks = np.maximum.accumulate(data)
    depths = 1.0 - data / peaks
    trough = int(np.argmax(depths))
    depth = float(depths[trough])
    if depth <= 0:
        return Drawdown(depth=0.0, peak=0, trough=0)
    peak = int(np.argmax(data[: trough + 1] == peaks[trough]))
    return Drawdown(depth=depth, peak=peak, trough=trough)
