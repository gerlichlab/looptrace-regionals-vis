"""Tests for this package's example files"""

import sys

if sys.version_info < (3, 11):
    import importlib_resources  # pragma: no cover
else:
    import importlib.resources as importlib_resources  # pragma: no cover
import string
from unittest import mock

import hypothesis as hyp
import pytest
from hypothesis import strategies as st

import looptrace_regionals_vis
from looptrace_regionals_vis import find_package_files

gen_non_extant_resource_folder = st.text(
    alphabet=string.ascii_letters + string.digits + "_-"
).filter(lambda sub: not importlib_resources.files(looptrace_regionals_vis).joinpath(sub).is_dir())


def test_package_example_files_count():
    """Test various properties of the finding of package example files."""
    examples = find_package_files("examples")
    exp_file_count = 3
    assert len(examples) == exp_file_count, (
        f"Expected {exp_file_count} example files but got {len(examples)}"
    )
    assert all(fp.is_file() for fp in examples), "Not all example files are seen as extant files!"


@hyp.given(subfolder=gen_non_extant_resource_folder)
def test_non_extant_subfolder_search_raises_expected_error(subfolder):
    """The randomised subfolder won't exist in the resources bundled with this package."""
    with pytest.raises(FileNotFoundError):
        find_package_files(subfolder)


@hyp.given(subfolder=gen_non_extant_resource_folder)
@hyp.settings(suppress_health_check=(hyp.HealthCheck.function_scoped_fixture,))
def test_empty_subfolder_search_raises_expected_error(tmp_path, subfolder):
    """Here we patch the resource-finding call so that we simulate injecting an empty folder into the package resources."""
    filemock = mock.MagicMock()
    filemock.joinpath.return_value = tmp_path
    with (
        mock.patch("looptrace_regionals_vis.importlib_resources.files", return_value=filemock),
        pytest.raises(ValueError),  # noqa: PT011
    ):
        find_package_files(subfolder)
