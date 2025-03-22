class FastAPIPaginationError(Exception):
    pass


class UninitializedPageError(FastAPIPaginationError, RuntimeError):
    pass


__all__ = [
    "FastAPIPaginationError",
    "UninitializedPageError",
]
