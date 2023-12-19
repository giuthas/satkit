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
Classes for dealing with configuration.

This file exist to remove a namespace conflict between typing.Optional and
strictyaml.Optional.
"""

from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from satkit.constants import (
    CoordinateSystems, Datasource, IntervalBoundary, IntervalCategory,
    SplineDataColumn, SplineMetaColumn)


@dataclass
class TimeLimit:
    tier: str
    interval: IntervalCategory
    boundary: IntervalBoundary


@dataclass
class ExclusionList:
    """
    List of files, prompts, and parts of prompts to be excluded from analysis.
    """
    files: Optional[list[str]] = None
    prompts: Optional[list[str]] = None
    parts_of_prompts: Optional[list[str]] = None


@dataclass
class SplineImportConfig:
    """
    Spline import csv file configuration.

    This describes how to interpret a csv file containing splines.
    """
    single_spline_file: bool
    headers: bool
    coordinates: CoordinateSystems
    interleaved_coords: bool
    meta_columns: tuple(SplineMetaColumn)
    data_columns: tuple(SplineDataColumn)
    spline_file: Optional[Path]
    spline_file_extension: Optional[str]
    delimiter: Optional[str] = '\t'

    def __post_init__(self):
        """
        Empty delimiter strings are replaced with a tabulator.
        """
        if not self.delimiter:
            self.delimiter = '\t'


@dataclass
class SplineDataConfig:
    """
    Configuration options for processing and display of splines.
    """
    ignore_points: Optional[tuple[int]] = None


@dataclass
class SplineConfig:
    """
    Configuration options for both import and processing of splines.
    """
    import_config: SplineImportConfig
    data_config: SplineDataConfig


@dataclass
class PathStructure:
    """
    Path structure of a Session for both loading and saving.
    """
    root: Path
    exclusion_list: Optional[Path] = None
    wav: Optional[Path] = None
    textgrid: Optional[Path] = None
    ultrasound: Optional[Path] = None
    spline_config: Optional[Path] = None


@dataclass
class SessionConfig:
    """
    Description of a RecordingSession for import into SATKIT.
    """
    data_source: Datasource
    exclusion_list: Optional[ExclusionList] = None
    spline_config: Optional[SplineConfig] = None
