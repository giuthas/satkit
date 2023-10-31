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
from typing import Optional

import numpy as np
from icecream import ic

from satkit.data_structures import ModalityData, Recording
from satkit.modalities import Splines

from .metrics_helpers import calculate_timevector
from .annd import ANND, AnndParameters

_annd_logger = logging.getLogger('satkit.annd')


def calculate_spline_distance_metric(
        spline_data: np.ndarray,
        metric: str,
        timestep: int,
        notice_base: str,
        exclude_points: tuple[int] = (10, 4)) -> np.ndarray:

    ic(spline_data.shape)
    # TODO: standardise the order of axes in Modality data or at the very least
    # include a list of their names in modality meta: 'time', 'x-y-z',
    # 'splinepoint' or some such AND enable the use of those names for data
    # indexing. DOCUMENT THIS!
    data = spline_data[:, :, exclude_points[0]:-exclude_points[1]]
    ic(data.shape)

    # loop to calculate annd, mnnd, apbpd and mpbpd
    num_points = data.shape[2]
    time_points = data.shape[1] - timestep

    annd = np.zeros(time_points)
    spline_d = np.zeros(time_points)
    spline_l1 = np.zeros(time_points)
    mnnd = np.zeros(time_points)
    apbpd = np.zeros(time_points)
    mpbpd = np.zeros(time_points)

    for i in range(time_points):
        current_points = data[:, i, :]
        next_points = data[:, i+timestep, :]

        diff = np.subtract(current_points, next_points)
        spline_l1[i] = np.sum(np.abs(diff))
        diff = np.square(diff)
        spline_d[i] = np.sqrt(np.sum(diff))
        diff = np.sum(diff, axis=0)  # sums over (x,y) for individual points
        diff = np.sqrt(diff)
        apbpd[i] = np.average(diff)
        mpbpd[i] = np.median(diff)

        nnd = np.zeros(num_points)
        for j in range(num_points):
            current_point = np.tile(current_points[:, j:j+1], (1, num_points))
            diff = np.subtract(current_point, next_points)
            diff = np.square(diff)
            diff = np.sum(diff, axis=0)
            diff = np.sqrt(diff)
            nnd[j] = np.amin(diff)

        annd[i] = np.average(nnd)
        mnnd[i] = np.median(nnd)

    notice = notice_base + ': ANND calculated.'
    _annd_logger.debug(notice)

    # data = {}
    # data['annd'] = annd
    # data['mnnd'] = mnnd
    # data['spline_l1'] = spline_l1

    # # this one is no good, but should be documented as such before removing the
    # # code
    # data['spline_d'] = spline_d/num_points

    # data['apbpd'] = apbpd
    # data['mpbpd'] = mpbpd  # median point-by-point Euclidean distance

    if metric == 'annd':
        return annd
    elif metric == 'mnnd':
        return mnnd
    elif metric == 'spline_l1':
        return spline_l1
    elif metric == 'apbpd':
        return apbpd
    else:
        return mpbpd


def calculate_annd(
        splines: Splines,
        to_be_computed: dict[str, AnndParameters]) -> list[ANND]:
    """
    Calculate Average Nearest Neighbour Distance (ANND) on the Splines. 


    Parameters
    ----------
    splines : Splines
        splines to process
    params : AnndParameters
        Processing options.

    Returns
    -------
    Union[ANND, None]
        Returns the new Modality or None if the Modality could not be
        calculated.
    """

    _annd_logger.info('%s: Calculating PD on %s.',
                      str(splines.data_path), splines.name)

    data = splines.data
    sampling_rate = splines.sampling_rate

    basename = splines.recording.meta_data.basename
    prompt = splines.recording.meta_data.prompt
    notice_base = basename + " " + prompt

    if splines.recording.excluded:
        notice = notice_base + ': Token excluded.'
        _annd_logger.info(notice)
        return None
    else:
        notice = notice_base + ': Token being processed.'
        _annd_logger.info(notice)

    if len(splines.timevector) < 2:
        notice = 'Not enough splines found for ' + basename + " " + prompt
        _annd_logger.critical(notice)
        return None

    timesteps = [to_be_computed[key].timestep for key in to_be_computed]
    timesteps.sort()
    timevectors = {
        timestep: calculate_timevector(splines.timevector, timestep)
        for timestep in timesteps}

    spline_distances = []
    param_set = None
    for (_, param_set) in to_be_computed.items():
        metric_data = calculate_spline_distance_metric(
            data,
            metric=param_set.metric,
            timestep=param_set.timestep,
            notice_base=notice_base)
        # interpolated=param_set.interpolated)

        modality_data = ModalityData(
            metric_data, sampling_rate, timevectors[param_set.timestep])
        spline_distances.append(ANND(splines.recording,
                                     param_set, parsed_data=modality_data))

    if param_set and param_set.release_data_memory:
        # Accessing the data modality's data causes it to be
        # loaded into memory. Keeping it there may cause memory
        # overflow. This releases the memory.
        splines.data = None

    return spline_distances


def add_annd(recording: Recording,
             splines: Splines,
             preload: bool = True,
             metrics: Optional[list[str]] = None,
             timesteps: Optional[list[int]] = None,
             release_data_memory: bool = True) -> None:
    """
    Calculate ANND on dataModality and add it to recording.

    Positional arguments:
    recording -- a Recording object
    modality -- the type of the Modality to be processed. The access will 
        be by recording.modalities[modality.__name__]

    Keyword arguments:
    preload -- boolean indicating if PD should be calculated on creation 
        (preloaded) or only on access.
    releaseDataMemory -- boolean indicating if the data attribute of the 
        data modality should be set to None after access. Only set this 
        to False, if you know that you have enough memory to hold all 
        of the data in RAM.
    """
    # TODO: this could be just as well merged with add_pd, because they are
    # very nearly identical.
    if not metrics:
        metrics = ['annd']
    if not timesteps:
        timesteps = [1]

    if recording.excluded:
        _annd_logger.info(
            "Recording %s excluded from processing.", recording.basename)
    elif not splines.__name__ in recording.modalities:
        _annd_logger.info("Data modality '%s' not found in recording: %s.",
                          splines.__name__, recording.basename)
    else:
        all_requested = ANND.get_names_and_meta(
            splines, metrics, timesteps, release_data_memory)
        missing_keys = set(all_requested).difference(
            recording.modalities.keys())
        to_be_computed = dict((key, value) for key,
                              value in all_requested.items()
                              if key in missing_keys)

        data_modality = recording.modalities[splines.__name__]

        if to_be_computed:
            annds = calculate_annd(data_modality, to_be_computed)

            for annd in annds:
                recording.add_modality(annd)
                _annd_logger.info("Added '%s' to recording: %s.",
                                  annd.name, recording.basename)
        else:
            _annd_logger.info(
                "Nothing to compute in ANND for recording: %s.",
                recording.basename)
