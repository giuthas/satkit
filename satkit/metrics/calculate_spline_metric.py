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
Functions for producing spline metrics.
"""

import logging
from typing import Optional

import numpy as np

from satkit.data_structures import ModalityData, Recording
from satkit.modalities import Splines

from .metrics_helpers import calculate_timevector
from .spline_metric import (
    SplineMetric, SplineMetricParameters, SplineDiffsEnum,
    SplineMetricEnum, SplineNNDsEnum, SplineShapesEnum)
from .tongue_shape_analysis import spline_shape_metric

_logger = logging.getLogger('satkit.gen_spline_metric')


def spline_diff_metric(
        data: np.ndarray,
        metric: SplineMetricEnum,
        timestep: int,
        notice_base: str) -> np.ndarray:
    """
    Calculate difference based spline metrics.

    Parameters
    ----------
    data : np.ndarray
        the spline data
    time_points : np.ndarray
        number of time points in the result
    metric : SplineMetricEnum
        which metric to calculate
    timestep : int
        which timestep to take
    notice_base : str
        text prepended to logging messages

    Returns
    -------
    np.ndarray
        an array of analysis values where array.shape[0] == time_points
    """
    time_points = data.shape[0] - timestep
    result = np.zeros(time_points)

    for i in range(time_points):
        current_points = data[i, :, :]
        next_points = data[i+timestep, :, :]

        diff = np.subtract(current_points, next_points)
        if metric == SplineMetricEnum.SPLINE_L1:
            result[i] = np.sum(np.abs(diff))
        elif metric == SplineMetricEnum.SPLINE_L2:
            diff = np.square(diff)
            result[i] = np.sqrt(np.sum(diff))
        else:
            diff = np.square(diff)
            # sums over (x,y) for individual points
            diff = np.sum(diff, axis=0)
            diff = np.sqrt(diff)
            if metric == SplineMetricEnum.APBPD:
                result[i] = np.average(diff)
            elif metric == SplineMetricEnum.MPBPD:
                result[i] = np.median(diff)

    _logger.debug("%s: %s calculated.", notice_base, metric)
    return result


def spline_nnd_metric(
        data: np.ndarray,
        metric: SplineMetricEnum,
        timestep: int,
        notice_base: str) -> np.ndarray:
    """
    Calculate nearest neighbour distance based spline metrics.

    Parameters
    ----------
    data : np.ndarray
        the spline data
    time_points : np.ndarray
        number of time points in the result
    metric : SplineMetricEnum
        which metric to calculate
    timestep : int
        which timestep to take
    notice_base : str
        text prepended to logging messages

    Returns
    -------
    np.ndarray
        an array of analysis values where array.shape[0] == time_points
    """
    time_points = data.shape[0] - timestep
    result = np.zeros(time_points)
    num_points = data.shape[2]

    for i in range(time_points):
        current_points = data[i, :, :]
        next_points = data[i+timestep, :, :]

        nnd = np.zeros(num_points)
        for j in range(num_points):
            current_point = np.tile(
                current_points[:, j:j+1], (1, num_points))
            diff = np.subtract(current_point, next_points)
            diff = np.square(diff)
            diff = np.sum(diff, axis=0)
            diff = np.sqrt(diff)
            nnd[j] = np.amin(diff)
        if metric == SplineMetricEnum.ANND:
            result[i] = np.average(nnd)
        elif metric == SplineMetricEnum.MNND:
            result[i] = np.median(nnd)

    _logger.debug("%s: %s calculated.", notice_base, metric)
    return result


def calculate_spline_metric(
        splines: Splines,
        to_be_computed: dict[str, SplineMetricParameters]
) -> list[SplineMetric]:
    """
    Calculate SplineMetrics on the Splines. 


    Parameters
    ----------
    splines : Splines
        splines to process
    params : SplineMetricParameters
        Processing options.

    Returns
    -------
    Union[SplineMetric, None]
        Returns the new Modality or None if the Modality could not be
        calculated.
    """

    _logger.info('%s: Calculating spline metrics on %s.',
                 str(splines.data_path), splines.name)

    data = splines.data
    sampling_rate = splines.sampling_rate

    basename = splines.recording.metadata.basename
    prompt = splines.recording.metadata.prompt
    notice_base = basename + " " + prompt

    # TODO: This should be handled where iterating over recordings.
    if splines.recording.excluded:
        notice = notice_base + ': Token excluded.'
        _logger.info(notice)
        return None
    else:
        notice = notice_base + ': Token being processed.'
        _logger.info(notice)

    if len(splines.timevector) < 2:
        notice = 'Not enough splines found for ' + basename + " " + prompt
        _logger.critical(notice)
        return None

    timesteps = [to_be_computed[key].timestep for key in to_be_computed]
    timesteps.sort()
    timevectors = {
        timestep: calculate_timevector(splines.timevector, timestep)
        for timestep in timesteps}

    spline_distances = []
    param_set = None
    for (_, param_set) in to_be_computed.items():
        metric = param_set.metric
        _logger.debug(
            "Calculating spline metric %s.", metric)

        data = splines.in_cartesian
        if param_set.exclude_points:
            exclude_points = param_set.exclude_points
            if exclude_points[1] == 0:
                data = data[:, :, exclude_points[0]:]
            else:
                data = data[:, :,
                            exclude_points[0]:-exclude_points[1]]

        timestep = param_set.timestep

        if metric in SplineDiffsEnum:
            metric_data = spline_diff_metric(
                data, metric, timestep, notice_base)
        elif metric in SplineNNDsEnum:
            metric_data = spline_nnd_metric(
                data, metric, timestep, notice_base)
        elif metric in SplineShapesEnum:
            metric_data = spline_shape_metric(
                data, metric, notice_base)
        else:
            message = f"Unknown Spline metric: {metric}."
            raise ValueError(message)

        if metric in SplineShapesEnum:
            modality_data = ModalityData(
                metric_data, sampling_rate, splines.timevector)
        else:
            modality_data = ModalityData(
                metric_data, sampling_rate, timevectors[param_set.timestep])
        spline_distances.append(SplineMetric(splines.recording,
                                             param_set,
                                             parsed_data=modality_data))

    if param_set and param_set.release_data_memory:
        # Accessing the data modality's data causes it to be loaded into
        # memory. Keeping it there may cause memory overflow. This releases the
        # memory to garbage collection.
        splines.data = None

    return spline_distances


def add_spline_metric(recording: Recording,
                      splines: Splines,
                      preload: bool = True,
                      metrics: Optional[list[str]] = None,
                      timesteps: Optional[list[int]] = None,
                      exclude_points: Optional[tuple[int, int]] = None,
                      release_data_memory: bool = True) -> None:
    """
    Calculate missing spline metrics and add them to the recording.

    Positional arguments:
    recording -- a Recording object
    modality -- the type of the Modality to be processed. The access will 
        be by recording[modality.__name__]

    Keyword arguments:
    preload -- boolean indicating if PD should be calculated on creation 
        (preloaded) or only on access.
    releaseDataMemory -- boolean indicating if the data attribute of the 
        data modality should be set to None after access. Only set this 
        to False, if you know that you have enough memory to hold all 
        of the data in RAM.
    """
    if not preload:
        message = ("Looks like somebody is trying to leave Spline metrics "
                   "to be calculated on the fly. This is not yet supported.")
        raise NotImplementedError(message)

    if not metrics:
        metrics = ['annd']
    if not timesteps:
        timesteps = [1]

    if recording.excluded:
        _logger.info(
            "Recording %s excluded from processing.", recording.basename)
    elif not splines.__name__ in recording:
        _logger.info("Data modality '%s' not found in recording: %s.",
                     splines.__name__, recording.basename)
    else:
        all_requested = SplineMetric.get_names_and_meta(
            splines, metrics, timesteps, exclude_points, release_data_memory)
        missing_keys = set(all_requested).difference(
            recording.keys())
        to_be_computed = dict((key, value)
                              for key, value in all_requested.items()
                              if key in missing_keys)

        data_modality = recording[splines.__name__]

        if to_be_computed:
            spline_metrics = calculate_spline_metric(
                data_modality, to_be_computed)

            for spline_metric in spline_metrics:
                recording.add_modality(spline_metric)
                _logger.info("Added '%s' to recording: %s.",
                             spline_metric.name,
                             recording.basename)
        else:
            _logger.info(
                "Nothing to compute in for SplineMetrics for recording: %s.",
                recording.basename)
