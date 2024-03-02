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

IntPage = CustomizedPage[
    Page[int],
    UseName("IntPage"),  # (1)
]

PageNoTotal = CustomizedPage[
    Page,
    UseIncludeTotal(False),  # (1)
]

BigPage = CustomizedPage[
    Page,
    UseParamsFields(size=500),  # (1)
]

PageOptionalParams = CustomizedPage[
    Page,
    UseOptionalParams(),  # (1)
]


class MyParams(Params): ...  # your magic here


PageWithMyParams = CustomizedPage[
    Page,
    UseParams(MyParams),  # (1)
]

PageWithCount = CustomizedPage[
    Page,
    UseFieldsAliases(total="count"),  # (1)
]

PageWithoutTotal = CustomizedPage[
    Page,
    UseExcludedFields("total"),  # (1)
]

PageStrLower = CustomizedPage[
    Page,
    UseModelConfig(anystr_lower=True),  # (1)
]

CustomPage = CustomizedPage[
    Page,
    UseName("CustomPage"),
    UseIncludeTotal(False),
    UseOptionalParams(),
]  # (1)
