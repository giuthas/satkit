#
# Copyright (c) 2019-2024
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
These are the code friendly wrappers for the configuration structures.

configuration_parsers contains the actual parsing of strictyaml into
comment-retaining dictionary-like structures. Here those structures get parsed
into pydantic models that know what their fields actually are.

This two level structure is maintained so that in some version after SATKIT 1.0
we can implement configuration round tripping with preserved comments.
"""

import logging
from pathlib import Path
from typing import Optional

from satkit.constants import (
    IntervalBoundary, IntervalCategory, TimeseriesNormalisation)
from satkit.helpers.base_model_extensions import UpdatableBaseModel

_logger = logging.getLogger('satkit.configuration_models')


# TODO try parsing with something like main_config =
# MainConfig(**main_config_dict)

class MainConfig(UpdatableBaseModel):
    """
    _summary_
    """
    epsilon: float
    mains_frequency: float
    data_run_parameter_file: Path
    gui_parameter_file: Path
    publish_parameter_file: Optional[Path]


class TimeLimit(UpdatableBaseModel):
    tier: str
    interval: IntervalCategory
    label: Optional[str]
    boundary: IntervalBoundary
    offset: Optional[float]


class PdArguments(UpdatableBaseModel):
    norms: list[str]
    timesteps: list[int]
    mask_images: Optional[bool] = False
    pd_on_interpolated_data: Optional[bool] = False
    release_data_memory: Optional[bool] = True
    preload: Optional[bool] = True


class FindPeaksArguments(UpdatableBaseModel):
    height: Optional[float]
    threshold: Optional[float]
    distance: Optional[int]
    distance_in_seconds: Optional[float]
    prominence: Optional[float]
    width: Optional[int]
    wlen: Optional[int]
    rel_height: Optional[float]
    plateau_size: Optional[float]


class PeakDetectionParams(UpdatableBaseModel):
    modality_pattern: str
    normalisation: Optional[TimeseriesNormalisation]
    time_min: Optional[TimeLimit]
    time_max: Optional[TimeLimit]
    detection_params: Optional[FindPeaksArguments]


class DataRunFlags(UpdatableBaseModel):
    detect_beep: Optional[bool] = False
    test: Optional[bool] = False


class DownsampleParams(UpdatableBaseModel):
    modality_pattern: str
    match_timestep: bool
    downsampling_ratios: list[int]


class CastFlags(UpdatableBaseModel):
    only_words: bool
    file: bool
    utterance: bool


class CastParams(UpdatableBaseModel):
    pronunciation_dictionary: Path
    speaker_id: str
    cast_flags: CastFlags


class DataRunConfig(UpdatableBaseModel):
    output_directory: Optional[Path]
    pd_arguments: Optional[PdArguments]
    peaks: Optional[PeakDetectionParams]
    downsample: Optional[DownsampleParams]
    cast: Optional[CastParams]

# gui params
#         data/tier height ratios: Map({
#             data: int
#             tier: int
#         data axes: MapPattern(
#             str, MapCombined(
#                 {
#                     sharex: Optional[bool
#                     modalities: Optional[Seq(str)
#                 },
#                 str, Any()
#             )),
#         pervasive tiers: Seq(str),
#         xlim: Optional[FixedSeq([float, float]),
#         default font size: int
#     number_of_data_axes = 0
#     if 'data axes' in gui_params:
#         if 'global' in gui_params['data axes']:
#             number_of_data_axes = len(gui_params['data axes']) - 1
#         else:
#             number_of_data_axes = len(gui_params['data axes'])
#     gui_params.update({'number of data axes': number_of_data_axes})


# publish params
#         output file: str
#         figure size", default=[8.3, 11.7]: Optional[FixedSeq(
#             [float, float]),
#         subplot grid: FixedSeq([int(), int()]),
#         subplots: MapPattern(str, str),
#         xlim: FixedSeq([float, float]),
#         xticks: Optional[Seq(str),
#         yticks: Optional[Seq(str),
#         use go signal: bool
#         normalise: NormalisationValidator
#         plotted tier: str
#         legend: Optional[Map({
#             handlelength: Optional[float]
#             handletextpad: Optional[float]

#     if publish_params['xticks']:
#         publish_params['xticklabels'] = publish_params['xticks'].copy()
#         publish_params['xticks'] = np.asarray(
#             publish_params['xticks'], dtype=float)

#     if publish_params['yticks']:
#         publish_params['yticklabels'] = publish_params['yticks'].copy()
#         publish_params['yticks'] = np.asarray(
#             publish_params['yticks'], dtype=float)


# plot params - not implemented
#         data/tier height ratios: Map({
#             data: int
#             tier: int
#         data axes: Seq(str),
#         pervasive tiers: Seq(str)
