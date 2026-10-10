# tests/registry/toy_models.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""Toy models for the registry tests: no catalog model lands in Step 3.

Four models cover the shapes a catalog entry takes: a scalar, an array input, a
family of calculations (a discriminated union) and one whose computation needs an
extra that is not installed. ``variant`` rebuilds one with a changed
specification, so each ``validate()`` rule gets a model that breaks exactly it.
"""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Annotated, Any, Literal, cast

from pydantic import Field

from pyeconomics.core import (
    ChangelogEntry,
    CostClass,
    Count,
    Evidence,
    Example,
    Invariant,
    MissingOptionalDependencyError,
    Model,
    ModelInputs,
    ModelOutputs,
    Money,
    Rate,
    Reference,
    Registry,
    Return,
    ReturnArray,
    Years,
    model,
    warn,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

FISHER = Reference(
    key="fisher1930",
    citation="Fisher, I. (1930). The Theory of Interest. Macmillan.",
    url="https://www.econlib.org/library/YPDBooks/Fisher/fshToI.html",
    locator="Part I",
)

NOT_INSTALLED = "pyeconomics-toy-package-that-is-not-installed"
"""A distribution name no environment has, to stand for an uninstalled extra."""


class ZeroCouponInputs(ModelInputs):
    face_value: Money = Field(gt=0, le=1e12, description="Face value")
    rate: Rate = Field(ge=-0.5, le=1.0, description="Annual yield")
    years: Years = Field(gt=0, le=100, description="Time to maturity")


class ZeroCouponOutputs(ModelOutputs):
    price: Money = Field(ge=0, le=1e14, description="Present value")


@model(
    id="fixed_income.toy_zero_coupon",
    version=1,
    title="Toy zero-coupon bond price",
    summary="Price of a zero-coupon bond from its annual yield.",
    formula=(r"P = \frac{F}{(1 + y)^T}",),
    assumptions=("The yield is compounded once a year.",),
    limitations=("Ignores credit risk, taxes and settlement conventions.",),
    references=(FISHER,),
    evidence=Evidence.STANDARD,
    cost=CostClass.INSTANT,
    invariants=(
        Invariant(
            id="price_falls_as_yield_rises",
            statement="For a positive maturity, the price falls as the yield rises.",
        ),
    ),
    examples=(
        Example(
            name="ten_years_at_five_percent",
            inputs={"face_value": 100, "rate": 0.05, "years": 10},
        ),
    ),
    changelog=(ChangelogEntry(version=1, note="First version."),),
)
def zero_coupon(inputs: ZeroCouponInputs) -> ZeroCouponOutputs:
    discount = (1 + inputs.rate) ** inputs.years
    return ZeroCouponOutputs(price=inputs.face_value / discount)


class MeanReturnInputs(ModelInputs):
    returns: ReturnArray = Field(
        min_length=1, max_length=252, description="Periodic returns"
    )


class MeanReturnOutputs(ModelOutputs):
    mean: Return = Field(ge=-1, le=100, description="Arithmetic mean return")
    count: Count = Field(ge=1, le=252, description="Number of returns")


@model(
    id="foundations.toy_mean_return",
    version=1,
    title="Toy arithmetic mean return",
    summary="The arithmetic mean of a series of periodic returns.",
    formula=(r"\bar{r} = \frac{1}{n}\sum_{t=1}^{n} r_t",),
    assumptions=("The returns are over equal periods.",),
    limitations=("A mean of returns is not a compound growth rate.",),
    references=(
        Reference(
            key="bodie2014",
            citation="Bodie, Kane and Marcus (2014). Investments. McGraw-Hill.",
            url="https://www.mheducation.com/",
            locator="Chapter 5",
        ),
    ),
    evidence=Evidence.STANDARD,
    cost=CostClass.INSTANT,
    invariants=(
        Invariant(
            id="mean_within_range",
            statement="The mean lies between the smallest and largest return.",
        ),
    ),
    examples=(
        Example(name="four_returns", inputs={"returns": [0.01, -0.02, 0.03, 0]}),
    ),
    changelog=(ChangelogEntry(version=1, note="First version."),),
)
def mean_return(inputs: MeanReturnInputs) -> MeanReturnOutputs:
    if not any(inputs.returns):
        warn("all_zero", "every return is zero")
    return MeanReturnOutputs(
        mean=sum(inputs.returns) / len(inputs.returns), count=len(inputs.returns)
    )


class PresentValueInputs(ModelInputs):
    calculation: Literal["present_value"] = Field(
        "present_value", description="Discount a future value"
    )
    future_value: Money = Field(ge=0, le=1e12, description="Future value")
    rate: Rate = Field(ge=-0.5, le=1.0, description="Annual rate")
    years: Years = Field(ge=0, le=100, description="Years")


class FutureValueInputs(ModelInputs):
    calculation: Literal["future_value"] = Field(
        "future_value", description="Compound a present value"
    )
    present_value: Money = Field(ge=0, le=1e12, description="Present value")
    rate: Rate = Field(ge=-0.5, le=1.0, description="Annual rate")
    years: Years = Field(ge=0, le=100, description="Years")


class PresentValueOutputs(ModelOutputs):
    calculation: Literal["present_value"] = Field(
        "present_value", description="Discount a future value"
    )
    present_value: Money = Field(ge=0, le=1e14, description="Present value")


class FutureValueOutputs(ModelOutputs):
    calculation: Literal["future_value"] = Field(
        "future_value", description="Compound a present value"
    )
    future_value: Money = Field(ge=0, le=1e14, description="Future value")


TimeValueInputs = Annotated[
    PresentValueInputs | FutureValueInputs, Field(discriminator="calculation")
]
TimeValueOutputs = Annotated[
    PresentValueOutputs | FutureValueOutputs, Field(discriminator="calculation")
]


@model(
    id="foundations.toy_time_value",
    version=2,
    title="Toy time value of money",
    summary="Present and future value at a constant annual rate.",
    formula=(r"PV = \frac{FV}{(1+r)^T}", r"FV = PV (1+r)^T"),
    assumptions=("The rate is compounded once a year and constant.",),
    limitations=("No taxes, fees or uneven cash flows.",),
    references=(FISHER,),
    evidence=Evidence.STANDARD,
    cost=CostClass.INSTANT,
    no_invariants_reason="A toy: its properties are checked by the registry tests.",
    examples=(
        Example(
            name="discount",
            inputs={
                "calculation": "present_value",
                "future_value": 100,
                "rate": 0.05,
                "years": 10,
            },
        ),
        Example(
            name="compound",
            inputs={
                "calculation": "future_value",
                "present_value": 100,
                "rate": 0.05,
                "years": 10,
            },
        ),
    ),
    changelog=(
        ChangelogEntry(version=1, note="First version."),
        ChangelogEntry(version=2, note="Years may be zero."),
    ),
    aliases=("foundations.toy_tvm",),
)
def time_value(inputs: TimeValueInputs) -> TimeValueOutputs:
    growth = (1 + inputs.rate) ** inputs.years
    if isinstance(inputs, PresentValueInputs):
        return PresentValueOutputs(present_value=inputs.future_value / growth)
    return FutureValueOutputs(future_value=inputs.present_value * growth)


@model(
    id="econometrics.toy_extra",
    version=1,
    title="Toy model that needs an extra",
    summary="Imports a library the toy extra would install.",
    formula=(r"y = X \beta + \varepsilon",),
    assumptions=("The library is installed.",),
    limitations=("It is not, in the test environment.",),
    references=(FISHER,),
    evidence=Evidence.PRACTITIONER,
    cost=CostClass.LIGHT,
    no_invariants_reason="A toy: it only raises.",
    examples=(
        Example(
            name="ten_years_at_five_percent",
            inputs={"face_value": 100, "rate": 0.05, "years": 10},
        ),
    ),
    changelog=(ChangelogEntry(version=1, note="First version."),),
    extra="toy",
)
def needs_extra(_inputs: ZeroCouponInputs) -> ZeroCouponOutputs:
    library = "toy_library"
    raise MissingOptionalDependencyError(library, extra="toy")


EXTRAS: dict[str, tuple[str, ...]] = {"toy": (NOT_INSTALLED,)}
"""The extras the toy distribution declares, each with what it installs."""

ALL_MODELS: tuple[Model[Any, Any], ...] = (
    mean_return,
    needs_extra,
    time_value,
    zero_coupon,
)


def toy_registry(*models: Model[Any, Any]) -> Registry:
    """Build an isolated registry of the toy models (all of them by default)."""
    return Registry.from_models(
        *(models or ALL_MODELS), distribution="toy-dist", extras=EXTRAS
    )


def variant[I: ModelInputs, O: ModelOutputs](
    base: Model[I, O], **changes: object
) -> Model[I, O]:
    """Rebuild ``base`` with a changed specification, checking nothing."""
    replaced = dataclasses.replace(base.spec, **cast("dict[str, Any]", changes))
    return Model(replaced, base.compute)


def with_inputs(base: Model[Any, Any], **fields: object) -> Mapping[str, object]:
    """Return an example's inputs with some fields replaced."""
    return {**base.spec.examples[0].inputs, **fields}
