"""Napari plugin for visualising locus-specific points from looptrace"""

import importlib.resources
from pathlib import Path

from numpydoc_decorator import doc

__version__ = "0.1.0"


@doc(
    summary="Yield each file directly in this project's examples folder.",
    parameters=dict(
        subfolder="Name of the package data resource folder in which to search",
    ),
    raises=dict(
        FileNotFoundError="If the given subfolder doesn't map to an extant directory in this package",
        ValueError="If the resources folder exists but has no files inside",
    ),
    returns="List of paths to files in the given/default location within this package",
)
def find_package_files(subfolder: str = "examples") -> list[Path]:
    package = Path(__file__).parent.name
    search_folder = importlib.resources.files(package).joinpath(subfolder)
    result = [path for path in search_folder.iterdir() if path.is_file()]
    if len(result) == 0:
        raise ValueError(
            f"Path corresponding to given subfolder in package '{package}' has no files."
        )
    return result
