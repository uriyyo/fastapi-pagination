from .api import using_params
from .page import LimitOffsetPage as Page
from .params import LimitOffsetPaginationParams as PaginationParams

pagination_params = using_params(PaginationParams)

__all__ = ["Page", "PaginationParams", "pagination_params"]
