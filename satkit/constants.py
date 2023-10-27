#
# Copyright (c) 2019-2023
# Pertti Palo, Scott Moisik, Matthew Faytak, and Motoki Saito.
#
# This file is part of Speech Articulation ToolKIT
# (see https://github.com/giuthas/satkit/).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# The example data packaged with this program is licensed under the
# Creative Commons Attribution-NonCommercial-ShareAlike 4.0
# International (CC BY-NC-SA 4.0) License. You should have received a
# copy of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0
# International (CC BY-NC-SA 4.0) License along with the data. If not,
# see <https://creativecommons.org/licenses/by-nc-sa/4.0/> for details.
#
# When using the toolkit for scientific publications, please cite the
# articles listed in README.markdown. They can also be found in
# citations.bib in BibTeX format.
#
"""
This module contains all sorts of constants used by SATKIT.
"""
from dataclasses import dataclass
from enum import Enum

# TODO 1.0: Decouple program and file format versions at version 1.0.
SATKIT_VERSION = '0.6'
SATKIT_FILE_VERSION = SATKIT_VERSION


class Coordinates(Enum):
    """
    Enum to differentiate coordinate systems.
    """
    CARTESIAN = 'Cartesian'
    POLAR = 'polar'


class Datasource(Enum):
    """
    Data sources SATKIT can handle.

    Used in saving and loading to identify the data source in config, as well
    as in meta and skip the step of trying to figure the data source out from
    the type of files present.
    """
    AAA = "AAA"
    # EVA = "EVA"
    RASL = "RASL"


class SplineDataColumn(Enum):
    """
    Basic data columns that any Spline should reasonably have.

    Accepted values: 'r' with 'phi', 'x' with 'y', and 'confidence'
    """
    R = "r"
    PHI = "phi"
    X = "x"
    Y = "y"
    CONFIDENCE = "confidence"


class SplineMetaColumn(Enum):
    """
    Basic metadata that any Spline should reasonably have.

    Accepted values:
    - ignore: marks a column to be ignored, unlike the others below, 
        can be used several times
    - id: used to identify the speaker, 
        often contained in a csv field called 'family name'
    - given names: appended to 'id' if not marked 'ignore'
    - date and time: dat3 and time of recording
    - prompt: prompt of recording, used to identify the recording with 'id'
    - annotation label: optional field containing annotation information
    - time in recording: timestamp of the frame this spline belongs to
    - number of spline points: number of sample points in the spline used 
        to parse the coordinates and possible confidence information    
    """
    IGNORE = "ignore"
    ID = "id"
    GIVEN_NAMES = "given names"
    DATE_AND_TIME = "date and time"
    PROMPT = "prompt"
    ANNOTATION_LABEL = "annotation label"
    TIME_IN_RECORDING = "time in recording"
    NUMBER_OF_SPLINE_POINTS = "number of spline points"


@dataclass(frozen=True)
class SatkitConfigFile():
    """
    Various configuration files used by SATKIT.

    These exist as a convenient way of not needing to risk typos. 
    """
    CSV_SPLINE_IMPORT = "csv_spline_import_config.yaml"


@dataclass(frozen=True)
class SatkitSuffix():
    """
    Suffixes for files saved by SATKIT.

    These exist as a convenient way of not needing to risk typos. To see the
    whole layered scheme SATKIT uses see the 'Saving and Loading Data' section
    in the documentation.
    """
    CONFIG = ".yaml"
    DATA = ".npz"
    META = ".satkit_meta"


class SavedObjectTypes(Enum):
    """
    Represent type of a saved satkit object in .satkit_meta.
    """
    # TODO 1.0: Check if this is actually in use.
    RECORDING_SESSION = "RecordingSession"
    RECORDING = "Recording"
    MODALITY = "Modality"


@dataclass(frozen=True)
class SourceSuffix():
    """
    Suffixes for files imported by SATKIT.

    These exist as a convenient way of not needing to risk typos and for
    recognising what SATKIT is being asked to import.

    Note that AAA_ULTRA_META_OLD is not a proper suffix and won't be recognised
    by pathlib and Path as such. Instead do this
    ```python
    directory_path = Path(from_some_source)
    directory_path/(name_string + SourceSuffix.AAA_ULTRA_META_OLD) 
    ```
    """
    AAA_ULTRA = ".ult"
    AAA_ULTRA_META_OLD = "US.txt"
    AAA_ULTRA_META_NEW = ".param"
    AAA_PROMPT = ".txt"
    AAA_SPLINES = ".spl"
    AVI = ".avi"
