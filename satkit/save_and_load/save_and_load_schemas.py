#
# Copyright (c) 2019-2025
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
Pydantic models and converters for saving and loading.
"""

from datetime import datetime
from pathlib import Path, PosixPath, WindowsPath
from typing import Union

from pydantic import BaseModel, DirectoryPath

from satkit.constants import Datasource, SavedObjectTypes
from satkit.data_structures import RecordingMetaData
from satkit.metrics import (SplineDiffsEnum, SplineNNDsEnum, SplineShapesEnum)


nested_text_converters = {
    datetime: str,
    PosixPath: str,
    WindowsPath: str,
    Path: str,
    SplineDiffsEnum: str,
    SplineNNDsEnum: str,
    SplineShapesEnum: str
}


class StatisticLoadSchema(BaseModel):
    """
    Loading schema for a saved Statistic.

    Statistic is defined in the data_structures module.
    """
    object_type: str
    name: str
    format_version: str
    parameters: dict


class DataContainerLoadSchema(BaseModel):
    """
    Loading schema for a saved Modality.

    Modality is defined in the data_structures module.
    """
    object_type: str
    name: str
    format_version: str
    parameters: dict


class DataContainerListingLoadSchema(BaseModel):
    """
    Loading schema for the DataContainer listings in a saved Recording.
    """
    data_name: str
    meta_name: Union[str, None]


class RecordingLoadSchema(BaseModel):
    """
    Loading schema for a saved Recording.

    Recording is defined in the data_structures module.
    """
    object_type: SavedObjectTypes = SavedObjectTypes.RECORDING
    name: str
    format_version: str
    parameters: RecordingMetaData
    modalities: dict[str, DataContainerListingLoadSchema]
    statistics: dict[str, DataContainerListingLoadSchema]


class SessionParameterLoadSchema(BaseModel):
    """
    Loading schema for a saved Session.

    Session is defined in the data_structures module.
    """
    path: DirectoryPath
    datasource: Datasource


class SessionLoadSchema(BaseModel):
    """
    Loading schema for a saved Session.

    Session is defined in the data_structures module.
    """
    object_type: SavedObjectTypes = SavedObjectTypes.SESSION
    name: str
    format_version: str
    parameters: SessionParameterLoadSchema
    recordings: list[str]
