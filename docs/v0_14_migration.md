# Breaking Changes in v0.14

## 1. `total` becomes required by default

`total` field now becomes required in `Page` and `LimitOffsetPage` classes.
It was previously optional, but now it is required for non-optional pages.

## 2. `UseIncludeTotal` updates `total` field type.

`UseIncludeTotal` customization now updates `total` field to required or optional based on its value.

## 3. `CursorPage` now includes `total` field by default

`CursorPage` class now includes `total` field by default.
Now all pages have same default behavior regarding `total` field.

You can still use `UseIncludeTotal` to disable `total` field in `CursorPage`.

```python
from typing import TypeVar

from fastapi_pagination.cursor import CursorPage
from fastapi_pagination.customization import UseIncludeTotal, CustomizedPage

T = TypeVar("T")

CursorPageNoTotal = CustomizedPage[
    CursorPage[T],
    UseIncludeTotal(False),
]

```

## 4. `beanie` min version update

`beanie` package now requires version `2.0.0` or higher.