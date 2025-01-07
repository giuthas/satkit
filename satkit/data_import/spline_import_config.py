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
How to load and validate spline import configuration files.
"""

import logging
from contextlib import closing
from pathlib import Path
from typing import Union

from strictyaml import (
    Bool, Map, Optional, ScalarValidator, Str, Seq,
    FixedSeq, Int, YAMLError, load)

from satkit.configuration import (
    PathValidator, SplineConfig, SplineDataConfig, SplineImportConfig)
from satkit.constants import (
    CoordinateSystems, SplineDataColumn, SplineMetaColumn)

_logger = logging.getLogger('satkit.data_import')


class CoordinateSystemValidator(ScalarValidator):
    """
    Validate yaml representing a CoordinateType.
    """

    def validate_scalar(self, chunk):
        if chunk.contents:
            try:
                return CoordinateSystems(chunk.contents)
            except ValueError:
                values = [ct.value for ct in CoordinateSystems]
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
                return SplineDataColumn(chunk.contents)
            except ValueError:
                values = [smd.value for smd in SplineDataColumn]
                print(
                    f"Error. Only following values for spline data columns are"
                    f"recognised: {str(values)}")
                raise
        else:
            return None


def make_spline_config(raw_config: dict) -> SplineConfig:
    """
    Construct a SplineConfig out of a dict read by `load_spline_config`.

    Parameters
    ----------
    raw_config : dict
        The dict

    Returns
    -------
    SplineConfig
        The new SplineConfig.
    """
    import_config = SplineImportConfig(**raw_config['import_config'])
    data_config = SplineDataConfig(**raw_config['data_config'])
    return SplineConfig(import_config, data_config)


def load_spline_config(
        filepath: Union[Path, str]) -> SplineConfig:
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
        with closing(open(filepath, 'r', encoding='utf-8')) as yaml_file:
            schema = Map({
                "import_config": Map({
                    "single_spline_file": Bool(),
                    Optional("spline_file"): PathValidator(),
                    Optional("spline_file_extension"): Str(),
                    "headers": Bool(),
                    "delimiter": Str(),
                    "coordinates": CoordinateSystemValidator(),
                    "interleaved_coords": Bool(),
                    "meta_columns": Seq(SplineMetaValidator()),
                    "data_columns": Seq(DataColumnValidator())
                }),
                "data_config": Map({
                    Optional("ignore_points"): FixedSeq([Int(), Int()])
                })
            })
            try:
                raw_spline_config = load(yaml_file.read(), schema)
            except YAMLError as error:
                _logger.warning(
                    "Could not read Spline configuration at %s.",
                    str(filepath))
                _logger.warning(str(error))
                raise
    else:
        _logger.warning(
            "Didn't find Spline configuration at %s.", str(filepath))

    return make_spline_config(raw_spline_config.data)
