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
Facilities for reading session import configuration.
"""

import logging
from contextlib import closing
from pathlib import Path
from typing import Union

from strictyaml import (Map, Optional,
                        ScalarValidator,
                        YAMLError, load)

from satkit.configuration import (
    PathStructure, PathValidator)
from satkit.constants import Datasource
from satkit.data_structures import SessionConfig

from .spline_import_config import load_spline_config

from satkit.configuration.exclusion_list_functions import load_exclusion_list
_logger = logging.getLogger('satkit.data_import')


class DatasourceValidator(ScalarValidator):
    """
    Validate yaml representing a Datasource.
    """

    def validate_scalar(self, chunk):
        if chunk.contents:
            try:
                return Datasource(chunk.contents)
            except ValueError:
                values = [ds.value for ds in Datasource]
                print(
                    f"Error. Only following values for data source are"
                    f"recognised: {str(values)}")
                raise
        else:
            return None


def make_session_config(
        data_root: Path,
        raw_config: dict) -> tuple[PathStructure, SessionConfig]:
    """
    Parse needed fields and create a new SessionImportConfig.

    Parameters
    ----------
    data_root : Path
        Path to the root directory for the data. If all data is in the same
        directory, this is that directory. Otherwise, this is the deepest common
        path among data types.
    raw_config : dict
        The raw config read from a yaml file.

    Returns
    -------
    tuple[PathStructure, SessionConfig]
        A tuple of PathStructure and SessionConfig
    """
    raw_config['paths']['root'] = data_root

    paths = PathStructure(**raw_config['paths'])
    raw_config.pop('paths', None)

    if paths.spline_config:
        raw_config['spline_config'] = load_spline_config(
            paths.root/paths.spline_config)

    if paths.exclusion_list:
        raw_config['exclusion_list'] = load_exclusion_list(
            paths.spline_config/paths.exclusion_list)

    return paths, SessionConfig(**raw_config)


def load_session_config(
        data_root: Path,
        filepath: Union[Path, str]) -> tuple[PathStructure, SessionConfig]:
    """
    Read a Session config file from filepath.

    Parameters
    ----------
    data_root : Path
        Path to the root directory for the data. If all data is in the same
        directory, this is that directory. Otherwise, this is the deepest common
        path among data types.
    filepath : Union[Path, str]
        Path or str to the Session import configuration file.

    Returns
    -------
    tuple[PathStructure, SessionConfig]
        A tuple of PathStructure and SessionConfig
    """
    if isinstance(filepath, str):
        filepath = Path(filepath)

    if filepath.is_file():
        with closing(open(filepath, 'r', encoding='utf-8')) as yaml_file:
            schema = Map({
                "data_source": DatasourceValidator(),
                "paths": Map({
                    Optional("wav"): PathValidator(),
                    Optional("textgrid"): PathValidator(),
                    Optional("ultrasound"): PathValidator(),
                    Optional("exclusion_list"): PathValidator(),
                    Optional("spline_config"): PathValidator()
                })
            })
            try:
                raw_session_import_config = load(yaml_file.read(), schema)
            except YAMLError as error:
                _logger.warning(
                    "Could not read Session import configuration at %s.",
                    str(filepath))
                _logger.warning(str(error))
                raise
    else:
        _logger.warning(
            "Didn't find Session import configuration at %s.", str(filepath))

    return make_session_config(data_root, raw_session_import_config.data)
