from typing import TypeVar

from fastapi_pagination import Page, Params
from fastapi_pagination.customization import (
    CustomizedPage,
    UseExcludedFields,
    UseFieldsAliases,
    UseIncludeTotal,
    UseModelConfig,
    UseName,
    UseOptionalParams,
    UseParams,
    UseParamsFields,
)

T = TypeVar("T")

IntPage = CustomizedPage[
    Page[int],
    UseName("IntPage"),  # (1)
]

PageNoTotal = CustomizedPage[
    Page[T],
    UseIncludeTotal(False),  # (1)
]

BigPage = CustomizedPage[
    Page[T],
    UseParamsFields(size=500),  # (1)
]

PageOptionalParams = CustomizedPage[
    Page[T],
    UseOptionalParams(),  # (1)
]


class MyParams(Params): ...  # your magic here


PageWithMyParams = CustomizedPage[
    Page[T],
    UseParams(MyParams),  # (1)
]

PageWithCount = CustomizedPage[
    Page[T],
    UseFieldsAliases(total="count"),  # (1)
]

PageWithoutTotal = CustomizedPage[
    Page[T],
    UseExcludedFields("total"),  # (1)
]

PageStrLower = CustomizedPage[
    Page[T],
    UseModelConfig(anystr_lower=True),  # (1)
]

CustomPage = CustomizedPage[
    Page[T],
    UseName("CustomPage"),
    UseIncludeTotal(False),
    UseOptionalParams(),
]  # (1)
