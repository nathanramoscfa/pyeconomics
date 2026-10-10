# Quickstart

Choose a model by its permanent id and pass its inputs as named fields.
Returns and rates are decimals: `0.05` means five percent.

```python
>>> import pyeconomics
>>> result = pyeconomics.run(
...     "foundations.returns",
...     calculation="holding_period",
...     beginning_value=100,
...     ending_value=108,
...     income=2,
... )
>>> result.outputs.holding_period_return
0.1
>>> result.manifest.model_id
'foundations.returns'
```

Discover the installed models and inspect their schemas and cards:

```python
from pyeconomics import registry

assert "foundations.returns" in registry.ids()
description = registry.describe("foundations.returns")
assert description
card = result.card().to_markdown()
assert "## Formula" in card
assert "## References" in card
```

Inputs and outputs are validated, and an invalid input raises an error rather
than silently producing an answer. The [model reference](reference/models/index.md)
lists the allowed calculations, units, bounds and limitations.
