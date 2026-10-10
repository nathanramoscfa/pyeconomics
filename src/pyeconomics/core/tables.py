# src/pyeconomics/core/tables.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""Results as tables: pandas, Polars, Arrow and Parquet (ADR-0008 decision 8).

One table layout serves a :class:`~pyeconomics.core.results.Result` (one row)
and a :class:`~pyeconomics.core.results.BatchResult` (one row per input row).
The columns mirror the paths in ``Result.to_dict()``:

- ``inputs.<field>`` for each input field;
- ``outputs.<field>`` for each output field;
- ``result_sha256``, the fingerprint of the row's result body.

A date is a ``datetime64[us]`` column in pandas (ADR-0008 decision 9) and a
date column in Polars and Arrow. An array is a list in each cell. A missing
value (a ``None`` output, or a field a row's calculation does not have) is a
null: ``NaN`` or ``NaT`` in pandas. A row's warnings are not columns; they
travel in the result.

pandas is a dependency. Polars and pyarrow never are: each is imported when a
conversion asks for it, and its absence raises
:class:`~pyeconomics.core.errors.MissingOptionalDependencyError`.

Examples
--------
>>> from pyeconomics.core.tables import columns_of
>>> columns_of([])
{'result_sha256': []}
"""

from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING, Any, Final

import pandas as pd

from pyeconomics.core._optional import import_optional

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from os import PathLike

    from pyeconomics.core.results import Result

__all__ = [
    "HASH_COLUMN",
    "MANIFEST_METADATA_KEY",
    "columns_of",
    "to_arrow",
    "to_pandas",
    "to_parquet",
    "to_polars",
]

#: The column that holds each row's ``result_sha256``.
HASH_COLUMN: Final = "result_sha256"

#: The Arrow schema metadata key that holds a single result's manifest, as
#: canonical JSON.
MANIFEST_METADATA_KEY: Final = "pyeconomics.manifest"


def _plain(value: object) -> object:
    """Turn a dumped field value into one every table library accepts."""
    if isinstance(value, tuple | list):
        return [_plain(item) for item in value]
    return value


def columns_of(results: Iterable[Result[Any, Any]]) -> dict[str, list[object]]:
    """Lay results out as columns of Python values, one entry per result.

    Columns appear in the order a field is first seen; a result without the
    field (another calculation of a union) holds ``None`` there.
    """
    rows: list[dict[str, object]] = []
    names: dict[str, None] = {}
    for result in results:
        row: dict[str, object] = {}
        for side, model in (("inputs", result.inputs), ("outputs", result.outputs)):
            for name, value in model.model_dump(mode="python").items():
                row[f"{side}.{name}"] = _plain(value)
        row[HASH_COLUMN] = result.manifest.result_sha256
        names.update(dict.fromkeys(row))
        rows.append(row)
    ordered = [name for name in names if name != HASH_COLUMN] + [HASH_COLUMN]
    return {name: [row.get(name) for row in rows] for name in ordered}


def _series(values: list[object]) -> pd.Series[Any]:
    """Build a column with the dtype its values call for."""
    present = [value for value in values if value is not None]
    if present and all(
        isinstance(value, dt.date) and not isinstance(value, dt.datetime)
        for value in present
    ):
        return pd.Series(values, dtype="datetime64[us]")
    if present and all(
        isinstance(value, int) and not isinstance(value, bool) for value in present
    ):
        return pd.Series(values, dtype="Int64" if None in values else "int64")
    if present and all(isinstance(value, float) for value in present):
        return pd.Series(values, dtype="float64")
    if present and all(isinstance(value, bool) for value in present):
        return pd.Series(values, dtype="boolean" if None in values else "bool")
    if present and all(isinstance(value, str) for value in present):
        return pd.Series(values, dtype="str")
    return pd.Series(values, dtype="object")


def to_pandas(columns: Mapping[str, list[object]]) -> pd.DataFrame:
    """Build a DataFrame from :func:`columns_of`'s output."""
    return pd.DataFrame({name: _series(values) for name, values in columns.items()})


def to_polars(columns: Mapping[str, list[object]]) -> Any:  # noqa: ANN401 - a polars object
    """Build a Polars DataFrame; needs ``polars``, not pyarrow."""
    polars = import_optional("polars")
    return polars.DataFrame(dict(columns))


def to_arrow(
    columns: Mapping[str, list[object]], *, manifest: str | None = None
) -> Any:  # noqa: ANN401 - a pyarrow object
    """Build an Arrow table; needs ``pyarrow``.

    Parameters
    ----------
    columns
        The output of :func:`columns_of`.
    manifest
        A manifest's canonical JSON, stored in the schema metadata under
        :data:`MANIFEST_METADATA_KEY`.
    """
    pyarrow = import_optional("pyarrow")
    table = pyarrow.table(dict(columns))
    if manifest is not None:
        table = table.replace_schema_metadata({MANIFEST_METADATA_KEY: manifest})
    return table


def to_parquet(table: Any, path: str | PathLike[str]) -> None:  # noqa: ANN401 - Arrow
    """Write an Arrow table to a Parquet file; needs ``pyarrow``."""
    parquet = import_optional("pyarrow.parquet")
    parquet.write_table(table, path)
