<!--
Copyright (c) 2019-2024
Pertti Palo, Scott Moisik, Matthew Faytak, and Motoki Saito.

This file is part of Speech Articulation ToolKIT
(see https://github.com/giuthas/satkit/).

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.

The example data packaged with this program is licensed under the
Creative Commons Attribution-NonCommercial-ShareAlike 4.0
International (CC BY-NC-SA 4.0) License. You should have received a
copy of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0
International (CC BY-NC-SA 4.0) License along with the data. If not,
see <https://creativecommons.org/licenses/by-nc-sa/4.0/> for details.

When using the toolkit for scientific publications, please cite the
articles listed in README.markdown. They can also be found in
citations.bib in BibTeX format.
-->

# SATKIT Documentation

Until the 1.0 release none of the documentation is necessarily final nor correct.

## Setup

- Seting SATKIT up for analysis is currently covered by setting up for development:
- [Set SATKIT up for development](SetupForDevelopment.markdown)

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
  - [Modalities in Practice](ModalitiesinPractice.markdown) including notes on
    specific Modalities
    - [Splines in SATKIT](Splines.markdown)
  - [Database Classes](DatabaseClasses.markdown)
- Extending SATKIT
  - Before starting, please read Coding conventions in [SATKIT development guide](SATKIT_development_guide.markdown).
  - Implementing a New Datasource
  - [Writing a New Modality](WritingNewModality.markdown)

## SATKIT API

[API Documentation](api/index.html)

## SATKIT Files

- Data files
  - [Guidelines for Data Directory Structure](DirectoryStructure.markdown)
  - Importing and Exporting
  - [Saving and Loading](Saving_and_loading.markdown)
- Configuration
  - Global configuration
    - General parameters
    - GUI parameters
    - Data processing parameters
  - Local configuration
