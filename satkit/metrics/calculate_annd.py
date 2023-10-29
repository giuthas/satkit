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

# Built in packages
import logging
from typing import Optional, Union

# Numpy and scipy
import numpy as np
from satkit.data_structures import Recording

from satkit.modalities import Splines

from .metrics_helpers import calculate_timevector
from .annd import ANND, AnndParameters

_annd_logger = logging.getLogger('satkit.annd')


def calculate_annd(
        splines: Splines, params: AnndParameters) -> Union[ANND, None]:
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

    for spline in splines:
        #####
        # disregard samples from front and from back
        #
        # this should be user adjustable after examining the splines
        #####
        spline['x'] = spline['x'][10:-4]
        spline['y'] = spline['y'][10:-4]

    # loop to calculate annd, mnnd, apbpd and mpbpd
    timestep = 3
    num_points = len(splines[1]['x'])
    annd = np.zeros(len(splines)-timestep)
    spline_d = np.zeros(len(splines)-timestep)
    spline_l1 = np.zeros(len(splines)-timestep)
    mnnd = np.zeros(len(splines)-timestep)
    apbpd = np.zeros(len(splines)-timestep)
    mpbpd = np.zeros(len(splines)-timestep)
    for i in range(len(splines)-timestep):
        current_points = np.stack((splines[i]['x'], splines[i]['y']))
        next_points = np.stack(
            (splines[i + timestep]['x'],
             splines[i + timestep]['y']))

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

    spline_time = np.array([spline['sample_time'] for spline in splines])
    annd_time = np.add(spline_time[timestep:], spline_time[0:-timestep])
    annd_time = np.divide(annd_time, np.repeat(2.0, len(splines)-timestep))

    notice = notice_base + ': Token processed in ANND.'
    _annd_logger.info(notice)

    data = {}
    data['annd'] = annd
    data['mnnd'] = mnnd
    data['spline_l1'] = spline_l1

    # this one is no good, but should be documented as such before removing the
    # code
    data['spline_d'] = spline_d/num_points

    data['apbpd'] = apbpd
    data['mpbpd'] = mpbpd  # median point-by-point Euclidean distance
    data['annd_time'] = annd_time

    return data


def add_annd(recording: Recording,
             splines: Splines,
             preload: bool = True,
             norms: Optional[list[str]] = None,
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
    releaseDataMemory -- boolean indicatin if the data attribute of the 
        data modality should be set to None after access. Only set this 
        to False, if you know that you have enough memory to hold all 
        of the data in RAM.
    """
    if not norms:
        norms = ['l2']
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
            splines, norms, timesteps, release_data_memory)
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
