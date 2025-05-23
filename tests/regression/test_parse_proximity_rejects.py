"""Regression tests related to the parsing of the proximity-rejected ROIs"""

from pathlib import Path
from typing import TYPE_CHECKING

from looptrace_regionals_vis.reader import _parse_proximity_rejects

if TYPE_CHECKING:
    from looptrace_regionals_vis.types import RoiId


def test_parse_succeeds_when_all_records_have_single_roi_proximal(tmpdir) -> None:
    """When each proximity-rejected ROI has a single other ROI as neighbor, the parse must still work."""
    lines = """index,fieldOfView,timepoint,spotChannel,zc,yc,xc,zMin,zMax,yMin,yMax,xMin,xMax,tooCloseRois
0,P0001,16,0,13.019719,47.112637,2745.086570,7.019719,19.019719,35.112637,59.112637,2733.086570,2757.086570,1812
1,P0001,16,0,12.882916,128.017592,3067.997290,6.882916,18.882916,116.017592,140.017592,3055.997290,3079.997290,1816
2,P0001,16,0,13.033545,173.382776,3067.833044,7.033545,19.033545,161.382776,185.382776,3055.833044,3079.833044,1823
3,P0001,16,0,12.903005,418.229036,2878.154108,6.903005,18.903005,406.229036,430.229036,2866.154108,2890.154108,1831
5,P0001,16,0,13.200682,717.412058,3189.328873,7.200682,19.200682,705.412058,729.412058,3177.328873,3201.328873,2012
""".splitlines(keepends=True)
    rois_file: Path = tmpdir / "tmp.csv"
    with rois_file.open(mode="w") as tmp:
        for l in lines:  # noqa: E741
            tmp.write(l)
    initial_result = _parse_proximity_rejects(rois_file)
    expected: list[set[RoiId]] = [{i} for i in [1812, 1816, 1823, 1831, 2012]]
    observed: list[set[RoiId]] = [r[1] for r in initial_result]
    assert observed == expected
