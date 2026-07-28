import sys
import warnings

if sys.version_info[:2] == (3, 10):
    warnings.filterwarnings(
        "ignore",
        message="You are using a Python version.*google.api_core",
        category=FutureWarning,
    )
