from pydantic import generics

# https://github.com/pydantic/pydantic/issues/4483
generics._generic_types_cache = {}
generics._assigned_parameters = {}
