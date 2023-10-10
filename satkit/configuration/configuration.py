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
import sys
from contextlib import closing
from pathlib import Path
from typing import Union

from satkit.constants import Datasource
from strictyaml import (Any, Bool, FixedSeq, Float, Int, Map, MapCombined,
                        MapPattern, Optional, ScalarValidator, Seq, Str,
                        YAMLError, load)

config_dict = {}
data_run_params = {}
gui_params = {}
plot_params = {}

# This is where we store the metadata needed to write out the configuration and
# possibly not mess up the comments in it.
_raw_config_dict = {}
_raw_data_run_params_dict = {}
_raw_gui_params_dict = {}
_raw_plot_params_dict = {}


class DatasourceValidator(ScalarValidator):
    """
    Validate yaml representing a Path.

    Please note that empty fields are interpeted as not available and
    represented by None. If you want to specify current working directory, use
    '.'
    """

    def validate_scalar(self, chunk):
        if chunk.contents:
            try:
                return Datasource(chunk.contents)
            except ValueError:
                values = [ds.value for ds in Datasource]
                print(
                    f"Error. Only following values for data source are recognised: {str(values)}")
                raise
        else:
            return None


class PathValidator(ScalarValidator):
    """
    Validate yaml representing a Path.

    Please note that empty fields are interpeted as not available and
    represented by None. If you want to specify current working directory, use
    '.'
    """

    def validate_scalar(self, chunk):
        if chunk.contents:
            return Path(chunk.contents)
        else:
            return None


def load_config(filepath: Union[Path, str, None] = None) -> None:
    """
    Read the config file from filepath and recursively the other config files.

    If filepath is None, read from the default file
    'configuration/configuration.yaml'. In both cases if the file does not
    exist, report this and exit.
    """
    load_main_config(filepath)
    load_run_params(config_dict['data run parameter file'])
    load_gui_params(config_dict['gui parameter file'])
    # load_plot_params(config['plotting parameter file'])


def load_main_config(filepath: Union[Path, str, None] = None) -> None:
    """
    Read the config file from filepath.

    If filepath is None, read from the default file
    'configuration/configuration.yaml'. In both cases if the file does not
    exist, report this and exit.
    """
    if filepath is None:
        filepath = Path('configuration/configuration.yaml')
    elif isinstance(filepath, str):
        filepath = Path(filepath)

    global config_dict
    global _raw_config_dict

    if filepath.is_file():
        with closing(open(filepath, 'r')) as yaml_file:
            schema = Map({
                "epsilon": Float(),
                "mains frequency": Float(),
                "data run parameter file": PathValidator(),
                "gui parameter file": PathValidator()
            })
            try:
                _raw_config_dict = load(yaml_file.read(), schema)
            except YAMLError as error:
                print(f"Fatal error in reading {filepath}:")
                print(error)
                sys.exit()
    else:
        print(f"Didn't find {filepath}. Exiting.".format(str(filepath)))
        sys.exit()
    config_dict.update(_raw_config_dict.data)


def load_run_params(filepath: Union[Path, str, None] = None) -> None:
    """
    Read the config file from filepath.

    If filepath is None, read from the default file
    'configuration/configuration.yaml'. In both cases if the file does not
    exist, report this and exit.
    """
    if filepath is None:
        print(f"Fatal error in reading {filepath}:")
        print(error)
        sys.exit()
    elif isinstance(filepath, str):
        filepath = Path(filepath)

    global data_run_params
    global _raw_data_run_params_dict

    if filepath.is_file():
        with closing(open(filepath, 'r')) as yaml_file:
            schema = Map({
                "data properties": Map({
                    "data source": DatasourceValidator(),
                    Optional("exclusion list"): PathValidator(),
                    "data path": PathValidator(),
                    Optional("wav directory"): PathValidator(),
                    Optional("textgrid directory"): PathValidator(),
                    Optional("ultrasound directory"): PathValidator(),
                    Optional("output directory"): PathValidator()
                }),
                "flags": Map({
                    "detect beep": Bool(),
                    "test": Bool()
                }),
                "cast": Map({
                    "pronunciation dictionary": PathValidator(),
                    "speaker id": Str(),
                    "cast flags": Map({
                        "only words": Bool(),
                        "file": Bool(),
                        "utterance": Bool()
                    })
                })
            })
            try:
                _raw_data_run_params_dict = load(yaml_file.read(), schema)
            except YAMLError as error:
                print(f"Fatal error in reading {filepath}:")
                print(error)
                sys.exit()
    else:
        print(f"Didn't find {filepath}. Exiting.".format(str(filepath)))
        sys.exit()
    data_run_params.update(_raw_data_run_params_dict.data)


def load_gui_params(filepath: Union[Path, str, None] = None) -> None:
    """
    Read the config file from filepath.

    If filepath is None, read from the default file
    'configuration/configuration.yaml'. In both cases if the file does not
    exist, report this and exit.
    """
    if filepath is None:
        print(f"Fatal error in reading {filepath}:")
        print(error)
        sys.exit()
    elif isinstance(filepath, str):
        filepath = Path(filepath)

    global gui_params
    global _raw_gui_params_dict

    if filepath.is_file():
        with closing(open(filepath, 'r')) as yaml_file:
            schema = Map({
                "data/tier height ratios": Map({
                    "data": Int(),
                    "tier": Int()
                }),
                "data axes": MapPattern(
                    Str(), MapCombined(
                        {
                            Optional("sharex"): Bool(),
                            Optional("modalities"): Seq(Str())
                        },
                        Str(), Any()
                    )),
                "pervasive tiers": Seq(Str()),
                Optional("xlim"): FixedSeq([Float(), Float()]),
                "default font size": Int(),
            })
            try:
                _raw_gui_params_dict = load(yaml_file.read(), schema)
            except YAMLError as error:
                print(f"Fatal error in reading {filepath}:")
                print(error)
                sys.exit()
    else:
        print(f"Didn't find {filepath}. Exiting.".format(str(filepath)))
        sys.exit()

    gui_params.update(_raw_gui_params_dict.data)

    number_of_data_axes = 0
    if 'data axes' in gui_params:
        if 'global' in gui_params['data axes']:
            number_of_data_axes = len(gui_params['data axes']) - 1
        else:
            number_of_data_axes = len(gui_params['data axes'])
    gui_params.update({'number of data axes': number_of_data_axes})


def load_plot_params(filepath: Union[Path, str, None] = None) -> None:
    """
    Read the plot file from filepath.

    Not yet implemented. Will raise a NotImplementedError.
    """

    raise NotImplementedError

    if filepath is None:
        print(f"Fatal error in reading {filepath}:")
        print(error)
        sys.exit()
    elif isinstance(filepath, str):
        filepath = Path(filepath)

    global plot_params
    global _raw_plot_params_dict

    if filepath.is_file():
        with closing(open(filepath, 'r')) as yaml_file:
            schema = Map({
                "data/tier height ratios": Map({
                    "data": Int(),
                    "tier": Int()
                }),
                "data axes": Seq(Str()),
                "pervasive tiers": Seq(Str())
            })
            try:
                _raw_plot_params_dict = load(yaml_file.read(), schema)
            except YAMLError as error:
                print(f"Fatal error in reading {filepath}:")
                print(error)
                sys.exit()
    else:
        print(f"Didn't find {filepath}. Exiting.".format(str(filepath)))
        sys.exit()
    plot_params.update(_raw_plot_params_dict.data)
