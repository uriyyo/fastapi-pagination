Custom `paginate` function usually should look like this:

```python
from typing import Any, Optional, List

from fastapi_pagination.api import apply_items_transformer, create_page
from fastapi_pagination.bases import AbstractParams
from fastapi_pagination.types import AdditionalData, SyncItemsTransformer
from fastapi_pagination.utils import verify_params


# usually we call this function `paginate`
def paginate(
    items: List[Any],
    params: Optional[AbstractParams] = None,
    *,
    # transformer is a function that transforms items before
    # they are passed to page instantiation
    transformer: Optional[SyncItemsTransformer] = None,
    # additional_data is a dictionary that contains additional data
    # that will be passed to page create method
    additional_data: Optional[AdditionalData] = None,
) -> Any:
    # validate input params to be of correct type
    params, raw_params = verify_params(params, "limit-offset")

    # apply pagination to items
    items = items[raw_params.as_slice()]
    # calculate total number of items if needed
    total = len(items) if raw_params.include_total else None
    # apply transformer to items
    t_items = apply_items_transformer(items, transformer)

    # create page object with paginated items
    return create_page(
        t_items,
        params=params,
        total=total,
        **(additional_data or {}),
    )
```
