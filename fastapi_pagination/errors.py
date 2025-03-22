class FastAPIPaginationError(Exception):
    pass


class UninitializedConfigurationError(FastAPIPaginationError, RuntimeError):
    pass


__all__ = [
    "FastAPIPaginationError",
    "UninitializedConfigurationError",
]
