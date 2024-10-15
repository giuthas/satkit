# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

[//]: # (Possible headings in a release:)
[//]: # (Highlights for shiny new features.)
[//]: # (Added for new features.)
[//]: # (Changed for changes in existing functionality.)
[//]: # (Refactor when functionality does not change but moves.)
[//]: # (Documentation for updates to docs.)
[//]: # (Testing for updates to tests.)
[//]: # (Deprecated for soon-to-be removed features.)
[//]: # (Removed for now removed features.)
[//]: # (Fixed for any bug fixes.)
[//]: # (Security in case of vulnerabilities.)
[//]: # (New contributors for first contributions.)

[//]: # (And ofcourse if a version needs to be YANKED:)
[//]: # (## [version number] [data] [YANKED])


## [Unreleased]

### Added

- SATKIT will soon be available on pypi, probably under the long name:
  speech_articulation_toolkit.

- TODO: import the roadmap here.

## [0.10.0]

### Highlights

- 

### Added

- Statistic is a new kind of derived data class. It is meant as the base class
  for data that is not time-dependent.
- There are now new abstract base classes that Session, Recording, Statistic, and
  Modality derive from. These are meant for gathering common functionality of the
  four main classes together rather than direct inheritance.
- AggregateImage is a new Statistic and its current only implementation is the
  metric 'mean', which is used to calculate mean images.
- Mean Images are used as the basis of calculating another Statistic: 

### Deprecated

- satkit.py will eventually be removed when running SATKIT will be moved to
  access points. This means SATKIT -- when correctly installed -- will run with
  from the command line with: `satkit [command] [arguments]`.

### Fixed

- AAA ultrasound importer now reads dates both in `%d/%m/%Y %H:%M:%S` and
  `%Y-%m-%d %I:%M:%S %p`.