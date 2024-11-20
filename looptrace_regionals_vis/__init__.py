"""Napari plugin for visualising locus-specific points from looptrace"""

import sys

if sys.version_info < (3, 11):
    import importlib_resources
else:
    import importlib.resources as importlib_resources
from pathlib import Path

from numpydoc_decorator import doc  # type: ignore[import-untyped]

__version__ = "0.3"

_PACKAGE_NAME = package = Path(__file__).parent.name


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
def find_package_files(subfolder: str = "examples") -> list[Path]:  # noqa: D103
    search_folder = _get_package_resources().joinpath(subfolder)
    result = [path for path in search_folder.iterdir() if path.is_file()]
    if len(result) == 0:
        raise ValueError(
            f"Path corresponding to given subfolder in package '{package}' has no files."
        )
    return result


@doc(summary="Get the path to this package's examples folder.")
def get_package_examples_folder() -> Path:  # noqa: D103
    return _get_package_resources().joinpath("examples")  # type: ignore[no-any-return]


@doc(summary="Get the hook with which to access resources bundled with this package.")
def _get_package_resources():  # type: ignore[no-untyped-def]  # noqa: ANN202
    return importlib_resources.files(_PACKAGE_NAME)


@doc(summary="List the files bundles as examples with this package.")
def list_package_example_files() -> list[Path]:  # noqa: D103
    return [path for path in get_package_examples_folder().iterdir() if path.is_file()]
