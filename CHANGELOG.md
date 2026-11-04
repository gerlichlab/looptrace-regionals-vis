# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.10.0] - 2026-11-04

### Added
* Support for Python 3.14, as gertils v0.9.0 has. CI runs on Python 3.12, 3.13 and 3.14.
* Support for napari 0.10 on macOS: the plugin allows napari 0.9.2 to 0.10. In napari 0.10, the example folder opens with all five layers of ROIs, on Python 3.12 and 3.14.

### Changed
* Depend on `gertils` v0.9.0, which no longer depends on numpydoc_decorator and allows Python 3.14.
* The lock is updated to the newest releases, among them napari 0.10.0, npe2 0.10.1 and PyQt6 6.12.

### Removed
* The dependency on numpydoc_decorator, whose newest release allows only Python below 3.14. See [looptrace issue 584](https://github.com/gerlichlab/looptrace/issues/584). Each docstring its `@doc` wrote when a module was imported is now written in the source, so ruff's docstring rules check it and an editor shows it. A test checks each Parameters section in the package, private functions' too, as `@doc` checked those it wrote: that it names the parameters, or a dataclass's fields, in order, with their defaults. Where `@doc` expanded a type from an annotation into a long string, or into `UnionType[...]`, which is neither Python nor numpydoc, the docstring names the type alias instead, such as `FloatLike`, `PathOrPaths` or `Reader`, as gertils and the other plugins do. `get_reader`'s docstring says that it reads a folder, where it spoke of a single-file parser, and `find_package_files`' that it lists the files of the resource folder it is given, not only the examples. The type information for numpydoc_decorator in `typings/` goes too, with its exemptions from ruff's rules. With gertils v0.9.0, which drops it too, it leaves the lock.

### Fixed
* A field of view in which no trace has more than two ROIs could not be read. Each ROI's trace partners in `*.with_trace_ids.csv` are then a single ID or none, and pandas reads such a column as floating-point numbers, which the plugin refused with a `TypeError`, so napari loaded nothing from the folder. The table's columns of ROI IDs, `neighbors` and `tracePartners`, are now read as text, as is `tooCloseRois` in `*.proximity_rejected.csv`.

## [v0.9.0] - 2026-11-02

### Added
* Support for Python 3.13, as gertils v0.8.0 has. CI runs on Python 3.12 and 3.13. The lock moves `numpydoc_decorator` 2.2.1 -> 2.3.0, which allows Python 3.13 where 2.2.1 stopped at 3.12, as gertils locks it.

### Changed
* Depend on `gertils` v0.8.0, which requires zarr 3.1 or later and numpy 1.26 or later. The plugin reads no zarr data itself; it declares zarr 3.1 or later, where it allowed zarr 2.4.12, since napari's own reader opens the image stores with it.
See [looptrace issue 579](https://github.com/gerlichlab/looptrace/issues/579), which moves looptrace to zarr 3.
* Require napari 0.9.2 or later on macOS, where 0.4.19.post1 was allowed too. The zarr reader of napari 0.4.19 cannot open a zarr 3 store, and looptrace's next release moves to napari 0.9.2 with numpy 2, where it kept 0.4.19 while it held numpy below 1.25. The plugin's lock and macOS CI already used 0.9.2.
* Type-check with `pyright` instead of `mypy`, as gertils and spotfishing do (#30). The package is checked strictly and the tests at the standard level. The line length is 88, ruff's default, where it was 100, as in the other repositories behind looptrace.
* ruff 0.7.4 -> 0.17.3 and pyright 1.1.411 -> 1.1.414, the newest releases, as in looptrace, gertils and the other plugins. The configuration names the rules that ruff renamed (`TC002`, `TC003`), no longer names those it removed (`ANN101`, `ANN102`), and ignores two that every rule now brings in: a copyright notice in each file (`CPY001`), as the LICENSE covers them all, and `X | None` for `Optional[X]` (`UP045`), which ruff split out of `UP007`, already ignored. pyright 1.1.414 finds nothing new. Five files are reformatted by ruff's newer style.

### Removed
* Support for Python 3.11. looptrace-regionals-vis requires Python 3.12 or 3.13, as gertils v0.8.0 does, and the newest releases of numpy, zarr and numcodecs. looptrace already requires Python 3.12. The Nix shell uses Python 3.12, the lowest supported, and ruff targets it.

## [v0.8.0] - 2026-10-13

### Changed
* Depend on `gertils` v0.7.0.
* Drop support for Python 3.10, which gertils v0.7.0 no longer supports: looptrace-regionals-vis requires Python 3.11 or 3.12, and no longer depends on `importlib_resources`.
* Allow napari 0.5 to 0.9 on macOS, as well as 0.4.19.post1, where it was pinned at 0.4.19.post1 since napari 0.9 needs Python 3.11. The plugin's own lock and macOS CI use napari 0.9.2; looptrace, which holds numpy below the 1.25 that napari 0.9 needs, keeps 0.4.19.
* The Nix shell uses nixpkgs 26.05, with Poetry 2, and `poetry.lock` is in Poetry 2's format.
* CI installs the newest Poetry, as it already did: the `poetry-version` the workflows set, `1.7.1`, is not an input of the action that installs Poetry, so it had no effect. Each CI job caches its environment separately, per Python.

## [v0.7.0] - 2026-10-07

### Changed
* Read the regional spots folders of `looptrace` v0.24. From v0.24 a field of view's tables are named `P0001.rois.<steps>.csv`, with `rois` a name part of its own, where earlier releases wrote `P0001_rois.<steps>.csv`; the plugin accepted only the latter, so dropping a v0.24 folder gave napari no data ("returned no data"). Both spellings are now read; the columns are the same.
* Checked under napari 0.9.2 as well as 0.4.19: the test suite passes on both. The napari pin (`==0.4.19.post1` on macOS) is unchanged, since napari 0.9 needs Python 3.11 or later and this project still supports 3.10.

## [v0.6.0] - 2026-04-19

### Changed
* Update expected files and columns list for compatibility with new `looptrace` release, version 0.18.0.

## [v0.5.8] - 2025-11-04

### Changed
* Depend on latest (v0.6.1) version of `gertils`.

## [v0.5.7] - 2025-07-18

### Fixed
* Finished the fix for the case of empty input data file.

## [v0.5.6] - 2025-07-17

### Fixed
* Now empty data files should cause no problem.

## [v0.5.5] - 2025-05-23

### Fixed
* Repaired bug by which parse of the column of adjacent ROI IDs can fail to parse when every value is a singleton, as this causes the column to be parsed as numeric rather than text.

## [v0.5.4] - 2025-04-01

### Changed
* Switch to Poetry for project build system

## [v0.5.3] - 2025-03-28

### Changed
* Fix version of `ruff` to v0.7.4, which should be the [last before a metadata info version update](https://github.com/astral-sh/ruff/issues/14681) which will require a Poetry update to at least 1.8.5.

## [v0.5.2] - 2025-03-26

### Changed
* Fix version of `ruff` to v0.8.0, which is the [last before a metadata info version update](https://github.com/astral-sh/ruff/issues/14681) which will require a Poetry update to at least 1.8.5.

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
