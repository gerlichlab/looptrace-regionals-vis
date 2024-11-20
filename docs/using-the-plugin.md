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
* _Blue_: discarded on account of being too close together
* _Orange_: discarded on account of not being in a nucleus
* _Pink_: individual (unmerged), and retained
* _Purple_: merge contributor
* _Yellow_: resulting from a merge, and retained

Spot shape differs by $z$-slice; the $z$-slice closest to the truncated $z$-coordinate of the spot's centroid will be square while everywhere else will be circular. We do not add $z$ slices for spots for which the bounding box extends below $0$, but there can be $z$ slices "beyond" the true images, if a spot was detected close to the max $z$ depth. This may also change in a future release.

For the ROIs/spots _resulting from_ a merger, you should see the ID of the ROI itself and the IDs of those which were merged to create it. 
For the ROIs/spots _contributing to_ a merger, you should see the ID of the ROI itself and the ID(s) of the ROI(s) to which it contributed.

### Necessary data files
1. 1 ZARR per field of view you wish to view, named like `P0001.zarr`
1. 0 or 1 files of each of the following types, per field of view, organized into a folder that has the same field of view name as the ZARR, e.g. `P0001`. There must be at least 1 of these 3 files present:
    - A `*_rois.csv` file: unfiltered regional spots
    - A `*_rois.proximity_accepted.csv` file: regional spots after discarding those which are too close together
    - A `*_rois.proximity_accepted.nuclei_labeled.csv` file: regional spots after proximity-based filtration and labeling attribution of ROIs/spots to nuclei

### File format notes
* For each spot, the following must be parsed:
    * Center point
    * Bounding box
    * Detection timepoint
    * Detection channel
* The center point's coordinates are read from `zc`, `yc` and `xc` columns.
* The bounding box is defined by columns suffixed `Min` and `Max` for each axis, e.g. `zMin`, `zMax`, etc.
* The timepoint is read from column `timepoint`.
* The channel is read from the `channel` column.
* For the merge contributors file, the `mergeOutput` column is parsed to get the ID of the merge result.
* For the `*_rois.proximity_accepted.nuclei_labeled.csv` file, the following additional columns are parsed:
    * `mergePartners` (to tell singleton ROIs from merger output ROIs)
    * `nucleusNumber` (to tell nuclear from non-nuclear ROIs)
    * `traceId` (to label ROIs which participate in a multi-ROI trace)
    * `tracePartners` (to determine whether a ROI participates in a multi-rOI trace)
