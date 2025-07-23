"""
Utility functions and variables used by all the other scripts.
"""

import tomllib  # needs python 3.11

with open("project_metadata.toml", "rb") as f:
    project_metadata = tomllib.load(f)


__version__ = project_metadata["project"]["version"]
