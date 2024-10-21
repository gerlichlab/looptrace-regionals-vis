# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.2.0] - 2024-10-21

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
