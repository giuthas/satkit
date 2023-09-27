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
from dataclasses import dataclass
from enum import Enum
from typing import Union

# TODO 1.0: Decouple program and file format versions at version 1.0.
SATKIT_VERSION = '0.6'
SATKIT_FILE_VERSION = SATKIT_VERSION


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

    def __str__(self):
        return self.value


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

    def __str__(self):
        return self.value


class Datasource(Enum):
    """
    Data sources SATKIT can handle.

    Used in saving and loading to identify the data source in config, as well as
    in meta and skip the step of trying to figure the data source out from the
    type of files present.
    """
    AAA = "AAA"
    # EVA = "EVA"
    RASL = "RASL"


class SavedObjectTypes(Enum):
    # TODO 1.0: Check if this is actually in use.
    """
    """
    RECORDING_SESSION = "RecordingSession"
    RECORDING = "Recording"
    MODALITY = "Modality"
