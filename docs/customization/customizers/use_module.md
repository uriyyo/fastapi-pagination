`UseModule` allows to change class module. It might be useful when you need to serialize/deserialize the class 
and `fastapi-pagination` is not able to correctly resolve the module of the class.

```py
from typing import TypeVar

from fastapi_pagination import Page
from fastapi_pagination.customization import CustomizedPage, UseModule

T = TypeVar("T")

CustomPage = CustomizedPage[
    Page[T],
    UseModule("my_module"),
]

print(CustomPage.__module__)
```
