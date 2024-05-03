## Using the plugin

### Quickstart
1. Ensure that you have an environment with the necessary dependencies installed. 
Perhaps the easiest way is to use this project's Nix shell. 
Alternatively, you could use a virtual environment that you manage yourself. 
For more, refer to the section about [installation and setup](./README.md#installation-and-environment).
1. Start Napari by typing `napari` from this project's Nix shell or with your environment activated.
1. Click and drag into the Napari window a ZARR for a particular field of view's FISH images, from `looptrace`.
1. If prompted, select to open the ZARR with Napari builtins.
1. Select "continuous" for the "auto-contrast" option in the upper-left (layer controls) pane of the Napari window.
1. Click and drag into the Napari window a folder of regional spots files for the same field of view.
1. If prompted, select `looptrace-regionals-vis` (this plugin) to open (the files in) this folder.
1. Use the sliders to adjust $z$ position (top), timepoint (bottom), or channel (middle).
1. Once you're finished viewing a particular FOV, select all layers and click the garbage can icon to remove them, then repeat the process for the next FOV of interest.

### What you should see
The Napari window should have three sliders:
* Bottom: the imaging timepoint
* Middle: the imaging channel
* Top: the $z$-slice

To support the possibility of detecting and visualising spots in multiple channels, we retain data from all imaging channels. We also keep all imaging timepoints for the moment (not just those with regional spot detection), though that may change. 

The spots are color-coded:
* Indigo: all detected spots
* Pale sky blue: spots which passed proximity-based filtration
* Pale red clay: spots which passed proximity-based and nuclei-based filtration

Spot shape differs by $z$-slice; the $z$-slice closest to the truncated $z$-coordinate of the spot's centroid will be square while everywhere else will be circular. We do not add $z$ slices for spots for which the bounding box extends below $0$, but there can be $z$ slices "beyond" the true images, if a spot was detected close to the max $z$ depth. This may also change in a future release.

If you see no spots of a certain color even when you're viewing a timepoint in which regional spots were detected, it's possible that there really are no spots of the level of filtration corresponding to the color you're expecting to see (but not seeing); it's _more likely_, though, that the layers are just in an unfortunate order. Refer to the [FAQ](#faq) for a quick fix.

### Necessary data files
1. 1 ZARR per field of view you wish to view, named like `P0001.zarr`
1. 0 or 1 files of each of the following types, per field of view, organized into a folder that has the same field of view name as the ZARR, e.g. `P0001`. There must be at least 1 of these 3 files present:
    - A `*_rois.csv` file: unfiltered regional spots
    - A `*_rois.proximity_filtered.csv` file: regional spots after discarding those which are too close together
    - A `*_rois.proximity_filtered.nuclei_filtered.csv` file: regional spots after proximity-based filtration and filtration for inclusion in nuclei

### File format notes
* For each spot, the following must be parsed:
    * Center point
    * Bounding box
    * Detection timepoint
    * Detection channel
* The center point's coordinates are read from `zc`, `yc` and `xc` columns.
* The bounding box is defined by columns suffixed `_min` and `_max` for each axis, e.g. `z_min`, `z_max`, etc.
* The timepoint is read from column `frame`.
* The channel is read from the `ch` column.

<a href="faq"></a>
### Frequently Asked Questions (FAQ)
1. __Why do I see only 1 or 2 colors of circles and boxes despite having dragged a folder containing data for more types (different filters) of spots?__\
    It's _possible_ that one or more types of filters discarded _all_ the spots, and that therefore there's nothing to visualise for a particular filtration type/level (corresponding to a particular file and color). It's _more likely_, though, that the layers are simply in an unfavorable order. Since one set of spots (e.g., proximity-filtered) will often be a subset of ("nested within") another set of spots (e.g., unfiltered), the superset can completely cover the subset. You can click and drag the layers in the Napari window so that they're in descending order of level of filtration.

