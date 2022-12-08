# SATKIT Documentation

Until the 1.0 release none of the documentation is necessarily final and correct.

## Setup

- Setup for analysis
- Setup for development (and analysis)

## GUI Userguide

[To be written.]

## Commandline Userguide

[To be written] but already available in a rudimentary form by running
`python satkit.py --help`

## SATKIT Runtime data structures

SATKIT's class structure aims for efficiency without sacrificing clarity. Clarity of code brings easy maintainability and that is more important in the long run than gains in execution speed.

- Introduction to SATKIT Data Structures
  - [Core Data Structures](CoreDataStructures.markdown)
  - [Modalities for Recorded Data](ModalitiesforRecordedData.markdown)
  - [Modalities for Derived Data](ModalitiesforDerivedData.markdown)
  - [Modalities in Practice](ModalitiesinPractice.markdown)
  - [Database Classes](DatabaseClasses.markdown)
- Extending SATKIT
  - Read [SATKIT Coding Conventions](SATKIT_coding_conventions.markdown).
  - Implementing a New Datasource
  - [Writing a New Modality](WritingNewModality.markdown)

## SATKIT API

[API Documentation](api/index.html)

## SATKIT Files

- Data files
  - [Guidelines for Data Directory Structure](DirectoryStructure.markdown)
  - Importing
  - Saving and Loading
- Configuration
  - Global configuration
    - General parameters
    - GUI parameters
    - Data processing parameters
  - Local configuration
