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
import logging
import sys
from contextlib import closing
from pathlib import Path
from typing import Union
# from ruamel.yaml import YAML

# yaml=YAML()
# from icecream import ic

import numpy as np
from strictyaml import (Any, Bool, FixedSeq, Float, Int, Map, MapCombined,
                        MapPattern, Optional, ScalarValidator, Seq, Str,
                        YAMLError, load)
from .configuration_classes import IntervalBoundary, IntervalCategory

from satkit.constants import DEFAULT_ENCODING, TimeseriesNormalisation

# TODO: Convert all the public members to UpdatableBaseModel from
# satkit.helpers.base_model_extensions and implement an update method as well
# as save functionality.

config_dict = {}
data_run_params = {}
gui_params = {}
plot_params = {}
publish_params = {}

# This is where we store the metadata needed to write out the configuration and
# possibly not mess up the comments in it.
_raw_config_dict = {}
_raw_data_run_params_dict = {}
_raw_gui_params_dict = {}
_raw_plot_params_dict = {}
_raw_publish_params_dict = {}

_logger = logging.getLogger('satkit.configuration')


class PathValidator(ScalarValidator):
    """
    Validate yaml representing a Path.

    Please note that empty fields are interpreted as not available and
    represented by None. If you want to specify current working directory, use
    '.'
    """

    def validate_scalar(self, chunk):
        if chunk.contents:
            return Path(chunk.contents)
        else:
            return None


class NormalisationValidator(ScalarValidator):
    """
    Validate yaml representing a Path.

    Please note that empty fields are interpreted as not available and
    represented by None. If you want to specify current working directory, use
    '.'
    """

    def validate_scalar(self, chunk):
        if chunk.contents:
            return TimeseriesNormalisation(chunk.contents)
        else:
            return None


class IntervalCategoryValidator(ScalarValidator):
    """
    Validate yaml representing a Path.

    Please note that empty fields are interpreted as not available and
    represented by None. If you want to specify current working directory, use
    '.'
    """

    def validate_scalar(self, chunk):
        if chunk.contents:
            return IntervalCategory(chunk.contents)
        else:
            return None


class IntervalBoundaryValidator(ScalarValidator):
    """
    Validate yaml representing a Path.

    Please note that empty fields are interpreted as not available and
    represented by None. If you want to specify current working directory, use
    '.'
    """

    def validate_scalar(self, chunk):
        if chunk.contents:
            return IntervalBoundary(chunk.contents)
        else:
            return None


class TimeLimitValidator():
    # TODO: this does not look workable. either just use a mapping and remap to
    # TimeLimit after, or switch all of this to nested text or regular yaml and pydantic
    pass


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
    load_publish_params(config_dict['publish parameter file'])


def load_main_config(filepath: Union[Path, str, None] = None) -> None:
    """
    Read the config file from filepath.

    If filepath is None, read from the default file
    'configuration/configuration.yaml'. In both cases if the file does not
    exist, report this and exit.
    """
    if isinstance(filepath, str):
        filepath = Path(filepath)
    elif not isinstance(filepath, Path):
        filepath = Path('configuration/configuration.yaml')

    _logger.debug("Loading main configuration from %s", str(filepath))

    if filepath.is_file():
        with closing(
                open(filepath, 'r', encoding=DEFAULT_ENCODING)) as yaml_file:
            schema = Map({
                "epsilon": Float(),
                "mains frequency": Float(),
                "data run parameter file": PathValidator(),
                "gui parameter file": PathValidator(),
                Optional("publish parameter file"): PathValidator()
            })
            try:
                _raw_config_dict = load(yaml_file.read(), schema)
            except YAMLError as error:
                _logger.fatal("Fatal error in reading %s.",
                              str(filepath))
                _logger.fatal(str(error))
                raise
    else:
        _logger.fatal(
            "Didn't find main config file at %s.", str(filepath))
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
        print("Fatal error in loading run parameters: filepath is None")
        sys.exit()
    elif isinstance(filepath, str):
        filepath = Path(filepath)

    _logger.debug("Loading run configuration from %s", str(filepath))

    time_limit_schema = Map({
                            "tier": Str(),
                            "interval": IntervalCategoryValidator(),
                            "boundary": IntervalBoundaryValidator(),
                            })

    if filepath.is_file():
        with closing(
                open(filepath, 'r', encoding=DEFAULT_ENCODING)) as yaml_file:
            schema = Map({
                Optional("output directory"): PathValidator(),
                "flags": Map({
                    "detect beep": Bool(),
                    "test": Bool()
                }),
                Optional("pd_arguments"): Map({
                    "norms": Seq(Str()),
                    "timesteps": Seq(Int()),
                    Optional("mask_images", default=False): Bool(),
                    Optional("pd_on_interpolated_data", default=False): Bool(),
                    Optional("release_data_memory", default=True): Bool(),
                    Optional("preload", default=True): Bool(),
                }),
                Optional("peaks"): Map({
                    "modality_pattern": Str(),
                    Optional("normalisation"): NormalisationValidator(),
                    Optional("time_min"): time_limit_schema,
                    Optional("time_max"): time_limit_schema,
                    Optional('height'): Float(),
                    Optional('threshold'): Float(),
                    Optional("distance"): Int(),
                    Optional("prominence"): Float(),
                    Optional("width"): Int(),
                    Optional('wlen'): Int(),
                    Optional('rel_height'): Float(),
                    Optional('plateau_size'): Float(),
                }
                ),
                Optional("cast"): Map({
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
                _logger.fatal("Fatal error in reading %s.",
                              str(filepath))
                _logger.fatal(str(error))
                raise
    else:
        _logger.fatal(
            "Didn't find run parameter file at %s.", str(filepath))
        sys.exit()

    data_run_params.update(_raw_data_run_params_dict.data)
    if 'peaks' in data_run_params:
        if 'normalisation' not in data_run_params['peaks']:
            data_run_params['peaks']['normalisation'] = (
                TimeseriesNormalisation.none)


def load_gui_params(filepath: Union[Path, str, None] = None) -> None:
    """
    Read the config file from filepath.

    If filepath is None, read from the default file
    'configuration/configuration.yaml'. In both cases if the file does not
    exist, report this and exit.
    """
    if filepath is None:
        print("Fatal error in loading run parameters: filepath is None")
        sys.exit()
    elif isinstance(filepath, str):
        filepath = Path(filepath)

    _logger.debug("Loading GUI configuration from %s", str(filepath))

    if filepath.is_file():
        with closing(
                open(filepath, 'r', encoding=DEFAULT_ENCODING)) as yaml_file:
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
                _logger.fatal("Fatal error in reading %s.",
                              str(filepath))
                _logger.fatal(str(error))
                raise
    else:
        _logger.fatal(
            "Didn't find gui parameter file at %s.", str(filepath))
        sys.exit()

    gui_params.update(_raw_gui_params_dict.data)

    number_of_data_axes = 0
    if 'data axes' in gui_params:
        if 'global' in gui_params['data axes']:
            number_of_data_axes = len(gui_params['data axes']) - 1
        else:
            number_of_data_axes = len(gui_params['data axes'])
    gui_params.update({'number of data axes': number_of_data_axes})


def load_publish_params(filepath: Union[Path, str, None] = None) -> None:
    """
    Read the config file from filepath.

    If filepath is None, read from the default file
    'configuration/configuration.yaml'. In both cases if the file does not
    exist, report this and exit.
    """
    if filepath is None:
        print("Fatal error in loading run parameters: filepath is None")
        sys.exit()
    elif isinstance(filepath, str):
        filepath = Path(filepath)

    _logger.debug("Loading publish configuration from %s", str(filepath))

    if filepath.is_file():
        with closing(
                open(filepath, 'r', encoding=DEFAULT_ENCODING)) as yaml_file:
            schema = Map({
                "output file": Str(),
                Optional("figure size", default=[8.3, 11.7]): FixedSeq(
                    [Float(), Float()]),
                "subplot grid": FixedSeq([Int(), Int()]),
                "subplots": MapPattern(Str(), Str()),
                "xlim": FixedSeq([Float(), Float()]),
                Optional("xticks"): Seq(Str()),
                Optional("yticks"): Seq(Str()),
                "use go signal": Bool(),
                "normalise": NormalisationValidator(),
                "plotted tier": Str(),
                Optional("legend"): Map({
                    Optional("handlelength"): Float(),
                    Optional("handletextpad"): Float(),
                }),
            })
            try:
                _raw_publish_params_dict = load(yaml_file.read(), schema)
            except YAMLError as error:
                _logger.fatal("Fatal error in reading %s.",
                              str(filepath))
                _logger.fatal(str(error))
                raise
    else:
        _logger.fatal(
            "Didn't find the publish parameter file at %s.", str(filepath))
        sys.exit()

    publish_params.update(_raw_publish_params_dict.data)

    if publish_params['xticks']:
        publish_params['xticklabels'] = publish_params['xticks'].copy()
        publish_params['xticks'] = np.asarray(
            publish_params['xticks'], dtype=float)

    if publish_params['yticks']:
        publish_params['yticklabels'] = publish_params['yticks'].copy()
        publish_params['yticks'] = np.asarray(
            publish_params['yticks'], dtype=float)


def load_plot_params(filepath: Union[Path, str, None] = None) -> None:
    """
    Read the plot configuration file from filepath.

    Not yet implemented. Will raise a NotImplementedError.
    """

    raise NotImplementedError

    if filepath is None:
        print("Fatal error in loading run parameters: filepath is None")
        sys.exit()
    elif isinstance(filepath, str):
        filepath = Path(filepath)

    _logger.debug("Loading plot configuration from %s", str(filepath))

    if filepath.is_file():
        with closing(
                open(filepath, 'r', encoding=DEFAULT_ENCODING)) as yaml_file:
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
                _logger.fatal("Fatal error in reading %s.",
                              str(filepath))
                _logger.fatal(str(error))
                raise
    else:
        _logger.fatal(
            "Didn't find plot parameter file at %s.", str(filepath))
        sys.exit()

    plot_params.update(_raw_plot_params_dict.data)
