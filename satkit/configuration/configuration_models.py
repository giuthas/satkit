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

`configuration_parsers` contains the actual parsing of strictyaml into
comment-retaining dictionary-like structures. Here those structures get parsed
into pydantic models that know what their fields actually are.

This two level structure is maintained so that in some version after SATKIT 1.0
we can implement configuration round tripping with preserved comments.
"""

import logging
from pathlib import Path
import re
from typing import Any, NewType

import numpy as np
from pydantic import conlist

from satkit.constants import (
    CoordinateSystems, Datasource,
    IntervalBoundary, IntervalCategory,
    SplineDataColumn, SplineMetaColumn
)
from satkit.external_class_extensions import UpdatableBaseModel

_logger = logging.getLogger('satkit.configuration_models')

FloatPair = NewType('FloatPair', conlist(float, min_length=2, max_length=2))
IntPair = NewType('IntPair', conlist(int, min_length=2, max_length=2))


class ExclusionList(UpdatableBaseModel):
    """
    List of files, prompts, and parts of prompts to be excluded from analysis.
    """
    path: Path
    files: list[str] | None = None
    prompts: list[str] | None = None
    parts_of_prompts: list[str] | None = None


class SplineImportConfig(UpdatableBaseModel):
    """
    Spline import csv file configuration.

    This describes how to interpret a csv file containing splines.
    """
    single_spline_file: bool
    headers: bool
    coordinates: CoordinateSystems
    interleaved_coords: bool
    meta_columns: tuple[SplineMetaColumn]
    data_columns: tuple[SplineDataColumn]
    spline_file: Path | None = None
    spline_file_extension: str | None = None
    delimiter: str = '\t'

    def __post_init__(self):
        """
        Empty delimiter strings are replaced with a tabulator.
        """
        if not self.delimiter:
            self.delimiter = '\t'


class SplineDataConfig(UpdatableBaseModel):
    """
    Configuration options for processing and display of splines.
    """
    ignore_points: tuple[int] | None = None


class SplineConfig(UpdatableBaseModel):
    """
    Configuration options for both import and processing of splines.
    """
    import_config: SplineImportConfig
    data_config: SplineDataConfig


class PathStructure(UpdatableBaseModel):
    """
    Path structure of a Session for both loading and saving.
    """
    root: Path
    exclusion_list: Path | None = None
    wav: Path | None = None
    textgrid: Path | None = None
    ultrasound: Path | None = None
    spline_config: Path | None = None


class MainConfig(UpdatableBaseModel):
    """
    _summary_
    """
    epsilon: float
    mains_frequency: float
    data_run_parameter_file: Path
    gui_parameter_file: Path
    publish_parameter_file: Path | None = None


class SearchPattern(UpdatableBaseModel):
    """
    Representation for simple and regexp search patterns.

    Members
    ----------
    pattern : str
        The pattern to search for
    is_regexp : bool, optional
        If the pattern should be treated as a regexp or not. Defaults to False.
    """
    pattern: str
    is_regexp: bool = False

    def match(self, string: str) -> bool:
        """
        Match this pattern to the argument string.

        If this pattern is not a regexp then this method will return True only
        when the pattern is found verbatim in the argument string.

        Parameters
        ----------
        string : str
            The string to match to.

        Returns
        -------
        bool
            True if this pattern matches the argument.
        """
        if self.is_regexp:
            return bool(re.match(self.pattern, string))

        return self.pattern in string

    @staticmethod
    def build(value: dict | str) -> 'SearchPattern':
        """
        Build a SearchPattern from a dictionary or a string.

        Parameters
        ----------
        value : dict | str
            The dictionary or string to build the SearchPattern from. If the
            parameter is a string it is used as the pattern, if it is a dict
            it's passed as keyword arguments to the SearchPattern constructor.

        Returns
        -------
        SearchPattern
            The constructed SearchPattern.

        Raises
        ------
        ValueError
            If the value is not a dict or a string.
        """
        if isinstance(value, str):
            return SearchPattern(pattern=value)

        if isinstance(value, dict):
            return SearchPattern(**value)

        raise ValueError("Unrecognised input value type: "
                         + type(value).__name__ + ".")


class TimeseriesNormalisation(UpdatableBaseModel):
    """
    Selection between peak normalised, bottom normalised or both.

    Contains a boolean for each peak and bottom normalisation.
    """
    peak: bool = False
    bottom: bool = False

    # TODO: this class needs a special dumper to save things correctly.

    @staticmethod
    def build(
            value: str
    ) -> 'TimeseriesNormalisation':
        """
        Construct a TimeseriesNormalisation object from a string value.

        The value usually comes from a config file.

        Parameters
        ----------
        value : str
            'none': no normalisation
            'peak': divide all data points y-values by the largest y-value
            'bottom': deduct the lowest y-value from all data points y-values
            'both': do first bottom normalisation and then peak normalisation.

        Returns
        -------
        TimeseriesNormalisation
            The new TimeseriesNormalisation with fields set as expected.
        """
        match value:
            case 'none':
                return TimeseriesNormalisation()
            case 'peak':
                return TimeseriesNormalisation(peak=True)
            case 'bottom':
                return TimeseriesNormalisation(bottom=True)
            case 'both':
                return TimeseriesNormalisation(peak=True, bottom=True)
            case _:
                raise ValueError("Unrecognised value: " + value + ".")


class TimeLimit(UpdatableBaseModel):
    tier: str
    interval: IntervalCategory
    boundary: IntervalBoundary
    label: str | None = None
    offset: float | None = None


class AggregateImageArguments(UpdatableBaseModel):
    metrics: list[str]
    preload: bool = True
    release_data_memory: bool = True
    run_on_interpolated_data: bool = False


class PdArguments(UpdatableBaseModel):
    norms: list[str]
    timesteps: list[int]
    mask_images: bool = False
    pd_on_interpolated_data: bool = False
    release_data_memory: bool = True
    preload: bool = True


class SplineMetricArguments(UpdatableBaseModel):
    metrics: list[str]
    timesteps: list[int]
    exclude_points: IntPair | None = None
    release_data_memory: bool = False
    preload: bool = True


class DistanceMatrixArguments(UpdatableBaseModel):
    metrics: list[str]
    exclusion_list: Path
    preload: bool = True
    release_data_memory: bool = False
    slice_max_step: int | None = None
    slice_step_to: int | None = None
    sort: bool = False
    sort_criteria: list[str] | None = None


class PointAnnotationParams(UpdatableBaseModel):
    normalisation: TimeseriesNormalisation | None = None
    time_min: TimeLimit | None = None
    time_max: TimeLimit | None = None


class FindPeaksScipyArguments(UpdatableBaseModel):
    height: float = None
    threshold: float = None
    distance: int = None
    prominence: float = None
    width: int = None
    wlen: int = None
    rel_height: float = None
    plateau_size: float = None


class PeakDetectionParams(PointAnnotationParams):
    modality_pattern: SearchPattern
    number_of_ignored_frames: int = 10
    distance_in_seconds: float | None = None
    find_peaks_args: FindPeaksScipyArguments | None = None


class DataRunFlags(UpdatableBaseModel):
    detect_beep: bool = False
    test: bool = False


class DownsampleParams(UpdatableBaseModel):
    """
    Parameters for downsampling metrics.

    Members
    ----------
    modality_pattern : str
        Simple search string to used to find the modalities.
    downsampling_ratios : tuple[int]
        Which downsampling ratios should be attempted. Depending on the next
        parameter all might not actually be used.
    match_timestep : bool, optional
        If the timestep of the Modality to be downsampled should match the
        downsampling_ratio, by default True
    """
    modality_pattern: SearchPattern
    downsampling_ratios: list[int]
    match_timestep: bool = True


class CastFlags(UpdatableBaseModel):
    only_words: bool
    file: bool
    utterance: bool


class CastParams(UpdatableBaseModel):
    pronunciation_dictionary: Path
    speaker_id: str
    cast_flags: CastFlags


class DataRunConfig(UpdatableBaseModel):
    output_directory: Path | None = None
    aggregate_image_arguments: AggregateImageArguments | None = None
    pd_arguments: PdArguments | None = None
    spline_metric_arguments: SplineMetricArguments | None = None
    distance_matrix_arguments: DistanceMatrixArguments | None = None
    peaks: PeakDetectionParams | None = None
    downsample: DownsampleParams | None = None
    cast: CastParams | None = None


class HeightRatios(UpdatableBaseModel):
    data: int
    tier: int


class AxesParams(UpdatableBaseModel):
    """
    Parameters for an axes in a plot.

    Parameters
    ----------
    colors_in_sequence : bool
        Should the line color rotation be ordered into a perceptual sequence,
        by default True
    mark_peaks: bool
        Should peak detection peaks (if available) be marked on the plot. This
        might get confusing if there is more than one timeseries on this axes.
        By default, None
    sharex: bool
        Does this axes share x limits with other axes, by default None
    y_offset: float
        y_offset between the modalities timeseries, by default None
    """
    # TODO: these docstrings should contain links to full, simple examples of
    # the corresponding yaml files

    colors_in_sequence: bool = True
    mark_peaks: bool | None = None
    sharex: bool | None = None
    ylim: tuple[float, float] | None = None
    y_offset: float | None = None


class AxesDefinition(AxesParams):
    """
    Parameters and plotted modalities for an axes in a plot.

    Parameters
    ----------
    modalities: list[str]
        List of the modalities to be plotted on these axes, by default None
    """
    modalities: list[str] | None = None
    sharex: bool = True


class GeneralAxesParams(UpdatableBaseModel):
    data_axes: AxesParams | None = None
    tier_axes: AxesParams | None = None


class GuiConfig(UpdatableBaseModel):
    data_and_tier_height_ratios: HeightRatios
    general_axes_params: GeneralAxesParams
    data_axes: dict[str, AxesDefinition]
    pervasive_tiers: list[str]
    xlim: FloatPair | str | None = None
    auto_xlim: bool | None = None
    default_font_size: int

    def plotted_modality_names(self) -> set[str]:
        """
        Return a set of the plotted modalities' names.

        This is run across all of the data axes. If you want the names plotted
        on a given axes, look them up from the `AxesDefinition`.

        Returns
        -------
        set[str]
            Set of strings containing the plotted modalities' names.
        """
        names = []
        for axes_def in self.data_axes.values():
            if axes_def.modalities is not None:
                names.extend(axes_def.modalities)
        return set(names)

    # TODO make a computed callback for getting params for a given axes so that
    # globals don't need to be copied over

    # def model_post_init(self, __context: Any) -> None:
    #     if 'global' in self.data_axes:
    #         for axes in self.data_axes:
    #             update axes params with global
    #         delete global? or move it to a different place?
    #     return super().model_post_init(__context)

    @property
    def number_of_data_axes(self) -> int:
        """
        Number of data axes. 

        DEPRECATED: This property will be removed as data axes list should not
        contain any extra information like a `global` directive.

        Returns
        -------
        int
            The number of data axes.
        """
        if self.data_axes:
            if 'global' in self.data_axes:
                return len(self.data_axes) - 1
            return len(self.data_axes)
        return 0


class LegendParams(UpdatableBaseModel):
    handlelength: float | None = None
    handletextpad: float | None = None


class PlotConfig(UpdatableBaseModel):
    output_file: str | None = None
    figure_size: FloatPair | None = None
    legend: LegendParams | None = None


class TimeseriesPlotConfig(PlotConfig):
    use_go_signal: bool
    normalise: TimeseriesNormalisation
    plotted_tier: str
    subplot_grid: IntPair
    subplots: dict[str, str]
    xlim: FloatPair
    xticks: list[str] | None = None
    yticks: list[str] | None = None

    # @computed_field
    @property
    def xtick_values(self) -> np.ndarray | None:
        """
        The xtick values as an `np.ndarray`.

        Returns
        -------
        np.ndarray | None
            The xtick values as an `np.ndarray` or None if there are none.
        """
        if self.xticks:
            return np.asarray(self.xticks, dtype=float)
        return None

    # @computed_field
    @property
    def ytick_values(self) -> np.ndarray | None:
        """
        The ytick values as an `np.ndarray`.

        Returns
        -------
        np.ndarray | None
            The ytick values as an `np.ndarray` or None if there are none.
        """
        if self.yticks:
            return np.asarray(self.yticks, dtype=float)
        return None


class AnnotationStatsPlotConfig(PlotConfig):
    modality_pattern: SearchPattern
    plotted_annotation: str
    aggregate: bool
    aggregation_methods: list[str]
    panel_by: str


class PublishConfig(PlotConfig):
    publish_directory: Path
    timeseries_plot: TimeseriesPlotConfig | None = None
    annotation_stats_plot: TimeseriesPlotConfig | None = None

    def model_post_init(self, __context: Any) -> None:
        if self.timeseries_plot:
            if not self.timeseries_plot.output_file:
                self.timeseries_plot.output_file = self.output_file
            if not self.timeseries_plot.figure_size:
                self.timeseries_plot.figure_size = self.figure_size
            if not self.timeseries_plot.legend:
                self.timeseries_plot.legend = self.legend

        if self.annotation_stats_plot:
            if not self.annotation_stats_plot.output_file:
                self.annotation_stats_plot.output_file = self.output_file
            if not self.annotation_stats_plot.figure_size:
                self.annotation_stats_plot.figure_size = self.figure_size
            if not self.annotation_stats_plot.legend:
                self.annotation_stats_plot.legend = self.legend

# plot params - not implemented
#         data/tier height ratios: Map({
#             data: int
#             tier: int
#         data axes: Seq(str),
#         pervasive tiers: Seq(str)
