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
import sys
from contextlib import closing
from pathlib import Path
from typing import Union

from strictyaml import (Bool, Map,
                        ScalarValidator, Seq,
                        YAMLError, load)

from satkit.constants import Coordinates, SplineDataColumn, SplineMetaColumn


class CoordinatesValidator(ScalarValidator):
    """
    Validate yaml representing a CoordinateType.
    """

    def validate_scalar(self, chunk):
        if chunk.contents:
            try:
                return Coordinates(chunk.contents)
            except ValueError:
                values = [ct.value for ct in Coordinates]
                print(
                    f"Error. Only following values for coordinate types are"
                    f"recognised: {str(values)}")
                raise
        else:
            return None


class SplineMetaValidator(ScalarValidator):
    """
    Validate yaml representing a Spline's meta columns.
    """

    def validate_scalar(self, chunk):
        if chunk.contents:
            try:
                return SplineMetaColumn(chunk.contents)
            except ValueError:
                values = [smd.value for smd in SplineMetaColumn]
                print(
                    f"Error. Only following values for spline metadata are"
                    f"recognised: {str(values)}")
                raise
        else:
            return None


class DataColumnValidator(ScalarValidator):
    """
    Validate yaml representing a Spline's data columns.
    """

    def validate_scalar(self, chunk):
        if chunk.contents:
            try:
                return SplineMetaColumn(chunk.contents)
            except ValueError:
                values = [smd.value for smd in SplineDataColumn]
                print(
                    f"Error. Only following values for spline data columns are"
                    f"recognised: {str(values)}")
                raise
        else:
            return None


@dataclass
class SplineImportConfig:
    """
    Spline import csv file configuration.

    This describes how to interpret a csv file containing splines.
    """
    singe_spline_file: bool
    headers: bool
    coordinates: Coordinates
    interleaved_coords: bool
    meta_columns: tuple(SplineMetaColumn)
    data_columns: tuple(SplineDataColumn)


def load_spline_import_config(
        filepath: Union[Path, str]) -> SplineImportConfig:
    """
    Read a spline config file from filepath.

    Parameters
    ----------
    filepath : Union[Path, str]
        Path or str to the spline import configuration file.

    Returns
    -------
    SplineImportConfig
        The loaded configuration.
    """
    if isinstance(filepath, str):
        filepath = Path(filepath)

    if filepath.is_file():
        with closing(open(filepath, 'r', encoding='utf8')) as yaml_file:
            schema = Map({
                "single_spline_file": Bool(),
                "headers": Bool(),
                "coordinates": CoordinatesValidator(),
                "interleaved_coords": Bool(),
                "meta_columns": Seq(SplineMetaValidator()),
                "data_columns": Seq(DataColumnValidator())
            })
            try:
                raw_spline_config = load(yaml_file.read(), schema)
            except YAMLError as error:
                print(f"Fatal error in reading {filepath}:")
                print(error)
                sys.exit()
    else:
        print(f"Didn't find {filepath}. Exiting.".format(str(filepath)))
        sys.exit()

    return SplineImportConfig(**raw_spline_config.data)
