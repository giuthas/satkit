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
from typing import NewType, Optional

import numpy as np
from pydantic import computed_field, conlist

from satkit.constants import (
    IntervalBoundary, IntervalCategory, TimeseriesNormalisation)
from satkit.helpers.base_model_extensions import UpdatableBaseModel

_logger = logging.getLogger('satkit.configuration_models')

FloatPair = NewType('FloatPair', conlist(float, min_length=2, max_length=2))
IntPair = NewType('IntPair', conlist(int, min_length=2, max_length=2))


class MainConfig(UpdatableBaseModel):
    """
    _summary_
    """
    epsilon: float
    mains_frequency: float
    data_run_parameter_file: Path
    gui_parameter_file: Path
    publish_parameter_file: Optional[Path] = None


class TimeLimit(UpdatableBaseModel):
    tier: str
    interval: IntervalCategory
    label: Optional[str] = None
    boundary: IntervalBoundary
    offset: Optional[float] = None


class PdArguments(UpdatableBaseModel):
    norms: list[str]
    timesteps: list[int]
    mask_images: Optional[bool] = False
    pd_on_interpolated_data: Optional[bool] = False
    release_data_memory: Optional[bool] = True
    preload: Optional[bool] = True


class FindPeaksArguments(UpdatableBaseModel):
    height: Optional[float] = None
    threshold: Optional[float] = None
    distance: Optional[int] = None
    distance_in_seconds: Optional[float] = None
    prominence: Optional[float] = None
    width: Optional[int] = None
    wlen: Optional[int] = None
    rel_height: Optional[float] = None
    plateau_size: Optional[float] = None


class PeakDetectionParams(UpdatableBaseModel):
    modality_pattern: str
    normalisation: Optional[TimeseriesNormalisation] = None
    time_min: Optional[TimeLimit] = None
    time_max: Optional[TimeLimit] = None
    detection_params: Optional[FindPeaksArguments] = None


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
    output_directory: Optional[Path] = None
    pd_arguments: Optional[PdArguments] = None
    peaks: Optional[PeakDetectionParams] = None
    downsample: Optional[DownsampleParams] = None
    cast: Optional[CastParams] = None


class HeightRatios(UpdatableBaseModel):
    data: int
    tier: int


class AxesParams(UpdatableBaseModel):
    sharex: Optional[bool] = None
    modalities: Optional[list[str]] = None


class GuiConfig(UpdatableBaseModel):
    data_and_tier_height_ratios: HeightRatios
    data_axes: dict[str, AxesParams]
    pervasive_tiers: list[str]
    xlim: Optional[FloatPair] = None
    default_font_size: int

    @computed_field
    @property
    def number_of_data_axes(self) -> int:
        if self.data_axes:
            if 'global' in self.data_axes:
                return len(self.data_axes) - 1
            return len(self.data_axes)
        return 0


class LegendParams(UpdatableBaseModel):
    handlelength: Optional[float]
    handletextpad: Optional[float]


class PublishConfig(UpdatableBaseModel):
    output_file: str
    figure_size: Optional[FloatPair] = [8.3, 11.7]
    subplot_grid: IntPair
    subplots: dict[str, str]
    xlim: FloatPair
    xticks: list[str]
    yticks: list[str]
    use_go_signal: bool
    normalise: TimeseriesNormalisation
    plotted_tier: str
    legend: Optional[LegendParams] = None

    @computed_field
    @property
    def xtick_values(self) -> list[float]:
        return np.asarray(self.xticks, dtype=float)

    @computed_field
    @property
    def ytick_values(self) -> list[float]:
        return np.asarray(self.yticks, dtype=float)


# plot params - not implemented
#         data/tier height ratios: Map({
#             data: int
#             tier: int
#         data axes: Seq(str),
#         pervasive tiers: Seq(str)
