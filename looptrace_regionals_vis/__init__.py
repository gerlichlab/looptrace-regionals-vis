"""Napari plugin for visualising locus-specific points from looptrace"""

import importlib.resources as importlib_resources
from pathlib import Path
from typing import cast

__version__ = "0.9.0"

_PACKAGE_NAME = package = Path(__file__).parent.name


def find_package_files(subfolder: str = "examples") -> list[Path]:
    """List the files directly in one of this package's resource folders.

    Parameters
    ----------
    subfolder : str, optional, default: 'examples'
        Name of the package data resource folder in which to search.

    Returns
    -------
    list of Path
        List of paths to files in the given/default location within this
        package.

    Raises
    ------
    FileNotFoundError
        If the given subfolder doesn't map to an extant directory in this
        package.
    NotADirectoryError
        If the given subfolder names a file, not a directory.
    ValueError
        If the resources folder exists but has no files inside.

    """
    search_folder = _get_package_resources().joinpath(subfolder)
    result = [path for path in search_folder.iterdir() if path.is_file()]
    if len(result) == 0:
        raise ValueError(
            f"Path corresponding to given subfolder in package '{package}' has no files."
        )
    return result


def get_package_examples_folder() -> Path:
    """Get the path to this package's examples folder.

    Returns
    -------
    Path

    """
    return _get_package_resources().joinpath("examples")


def _get_package_resources() -> Path:
    """Get the hook with which to access resources bundled with this package.

    Returns
    -------
    Path

    """
    # files() gives a Path for a package installed as files, as this one is.
    return cast("Path", importlib_resources.files(_PACKAGE_NAME))


def list_package_example_files() -> list[Path]:
    """List the files bundled as examples with this package.

    Returns
    -------
    list of Path

    """
    return [path for path in get_package_examples_folder().iterdir() if path.is_file()]
