# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.5.1] - 2025-03-21

### Changed
* Bump version of `gertils` dependency to v0.6.0.

## [v0.5.0] - 2025-02-21

### Added
* `LOOPTRACE__DISPLAY_SINGLETON_ROI_IDS`, as an environment variable to indicate that any singleton ROI should have its ID displayed. 
The default is false, but truth can be set with `1` or `TRUE`.
* `LOOPTRACE__DISPLAY_PROXIMITY_REJECTS_ANNOTATION`, as an environment variable to indicate that any ROI rejected for proximity should be labeled with its ID and those of its proximal neighbors. 
The default is false, but truth can be set with `1` or `TRUE`.
* `LOOPTRACE__MAX_PROXIMITY_PARTNERS_TO_DISPLAY`, as an environment variable to set the maximum number of neighbors which should be displayed for a ROI discarded on account of proximity to others. 
The default is 5.

## [v0.4.1] - 2024-12-03

### Changed
* Always display trace ID, for every final (merged or singleton) spot.
See [Issue 18](https://github.com/gerlichlab/looptrace-regionals-vis/issues/18) and [Issue 19](https://github.com/gerlichlab/looptrace-regionals-vis/issues/19).
* Use implementation of `NucleusNumber` from `gertils`.

## [v0.4.0] - 2024-11-27
This release supports `looptrace` v0.11.1.

### Changed
* Updated expected _intra_-field, _inter_-value delimiter to match changes in `looptrace`

## [v0.3.2] - 2024-11-21

### Changed
* Update version of `gertils` dependency to latest version (v0.5.1).

## [v0.3.1] - 2024-11-21
This is compatible with the 0.11.x line of `looptrace`.

### Changed
* Support Python 3.12.
* Bump up dependencies on `gertils` and `numpydoc_decorator`.

## [v0.3.0] - 2024-11-20
This is compatible with the 0.11.x line of `looptrace`.

### Changed
* Updated expected column and file names of input to match those emitted by `looptrace` processing; 
in particular, the file previously represented by `*_rois.proximity_accepted.nuclei_labeled.csv` is replaced by `*_rois.with_trace_ids.csv`.

### Added
* Now the joint tracing structure of ROIs from different regional barcodes / imaging timepoints can be visualised.

### Changed
* Adapted to new `looptrace` column names

## [v0.2.0] - 2024-10-21
* This is compatible with the 0.10.x line line of `looptrace`.

### Changed
* Patterns expected for input files:
    * `*_rois.merge_contributors.csv`
    * `*_rois.proximity_rejected.csv`
    * `*_rois.proximity_accepted.nuclei_labeled.csv`
* Visualising spots as discrete (nonoverlapping) sets
* Visualising 5 sets of spots:
    * Merge contributors
    * Proximity rejects (spots too close together)
    * Nuclear rejects (spots not in a nucleus)
    * Accepted singletons
    * Accepted mergers

## [v0.1.0] - 2024-04-28
 
### Added
* This package, first release
