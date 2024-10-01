`UseName` customizer is used to set the name of the generated class.
This customizer is useful when you want to set the name of the generated class to a specific value.

By default, when you use `CustomizedPage` class name will be changed to `${class_name}Customized`.

```py
from typing import TypeVar

from fastapi_pagination import Page
from fastapi_pagination.customization import CustomizedPage, UseName

T = TypeVar("T")

CustomPage = CustomizedPage[
    Page[T],
    UseName("CustomPage"),
]

print(CustomPage.__name__)
```