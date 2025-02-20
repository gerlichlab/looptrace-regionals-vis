"""Various configurable settings for using the plugin"""

import os

DEFAULT_MAX_NUM_PARTNERS_TO_DISPLAY: int = 5


def _get_default_false(env_var: str) -> bool:
    try:
        return os.environ[env_var] in ["True", "TRUE", "T", "1"]
    except KeyError:
        return False


def display_proximity_rejects_annotation() -> bool:
    """Whether to display the annotation of the proximity rejects"""
    return _get_default_false("LOOPTRACE__DISPLAY_PROXIMITY_REJECTS_ANNOTATION")


def display_roi_id_for_singletons() -> bool:
    """Whether to display the ROI ID for singleton ROIs"""
    return _get_default_false("LOOPTRACE__DISPLAY_SINGLETON_ROI_IDS")


def get_maximum_number_of_proximity_partners_to_display() -> int:
    """Determine the maximum number of neighbors to display for a proximity-rejected ROI."""
    return (
        int(
            os.getenv(
                "LOOPTRACE__MAX_PROXIMITY_PARTNERS_TO_DISPLAY", DEFAULT_MAX_NUM_PARTNERS_TO_DISPLAY
            )
        )
        if display_proximity_rejects_annotation()
        else 0
    )
