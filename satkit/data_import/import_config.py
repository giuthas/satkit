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
Classes for describing how data should be imported.
"""
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from satkit.configuration import ExclusionList
from satkit.constants import (
    CoordinateSystems, Datasource, SplineDataColumn, SplineMetaColumn)


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
    ignore_points: Optional[tuple[int]] = None

    def __post_init__(self):
        """
        Empty delimiter strings are replaced with a tabulator.
        """
        if not self.delimiter:
            self.delimiter = '\t'


@dataclass
class SessionImportConfig:
    """
    Description of a RecordingSession for import into SATKIT.
    """
    data_source: Datasource
    data_path: Path
    exclusion_list: Optional[ExclusionList]
    wav_directory: Optional[Path]
    textgrid_directory: Optional[Path]
    ultrasound_directory: Optional[Path]
    spline_import_config: Optional[SplineImportConfig]
