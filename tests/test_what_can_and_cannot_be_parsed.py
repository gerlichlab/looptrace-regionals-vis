"""Validation of what this plugin will or will not attempt to parse"""

from pathlib import Path
import string

import hypothesis as hyp
from hypothesis import strategies as st
import pytest

from looptrace_regionals_vis import find_package_files
from looptrace_regionals_vis.reader import get_reader


def test_cannot_read_list_of_files():
    assert (
        get_reader(find_package_files()) is None
    ), "Expected inability to parse list of filepaths, but got non-null reader!"


@pytest.mark.parametrize("wrap", (str, Path))
@pytest.mark.parametrize("filepath", find_package_files("examples"))
def test_would_read_each_package_example(wrap, filepath):
    arg = wrap(filepath)
    assert callable(
        get_reader(arg)
    ), f"Expected a callable reader for path {arg} but didn't get one!"


@pytest.mark.parametrize("prep_arg", [str, Path])
@pytest.mark.parametrize("make_file", [False, True])
@hyp.given(filename_prefix=st.text(alphabet=string.ascii_letters + string.digits + "_-"))
@hyp.settings(suppress_health_check=(hyp.HealthCheck.function_scoped_fixture,))
def test_readability_depends_on_proper_extension(
    tmp_path, make_file, prep_arg, filename_prefix, proc_status_inference_params
):
    fn = (
        filename_prefix
        + proc_status_inference_params.suffix
        + proc_status_inference_params.extension
    )
    fp = tmp_path / fn
    if make_file:
        fp.touch()
    arg = prep_arg(fp)
    observed = get_reader(arg)
    if make_file and proc_status_inference_params.expectation is not None:
        assert callable(observed), f"Expected callable reader for path {fp} but didn't get one!"
    else:
        assert observed is None, f"Expected null reader but got non-null!"
