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
Calculate AverageImages for Modalities.
"""

import logging
from typing import Optional

import numpy as np

# local modules
from satkit.data_structures import FileInformation, Modality, Recording

from .aggregate_image import AggregateImage, AggregateImageParameters

_logger = logging.getLogger('satkit.session_mse')


def calculate_average_image(
        modality: Modality,
        params: AggregateImageParameters) -> AggregateImage:
    """
    Calculate average image from a Modality.

    This method does not really care if the Modality contains images, as long
    as it contains time varying data (which all Modalities do). It will
    calculate the time average with the given method in params.

    Parameters
    ----------
    modality : Modality
        Modality to calculate the average on.
    params : AggregateImageParameters
        Parameters for calculating the average.

    Returns
    -------
    AggregateImage
        The new AverageImage Statistic.
    """
    data = modality.data
    match params.metric:
        case 'mean':
            average_image = np.mean(data, axis=0)
        case _:
            raise ValueError(f'Unknown metric {params.metric}')
    file_info = FileInformation()
    return AggregateImage(
        modality.recording,
        meta_data=params,
        file_info=file_info,
        parsed_data=average_image)


def add_average_images(
    recording: Recording,
    modality: Modality,
    preload: bool = True,
    metrics: Optional[list[str]] = None,
    release_data_memory: bool = True,
    run_on_interpolated_data: bool = False,
) -> None:
    """
    Calculate PD on dataModality and add it to recording.

    Positional arguments:
    recording -- a Recording object
    modality -- the type of the Modality to be processed. The access will 
        be by recording[modality.__name__]

    Keyword arguments:
    preload -- boolean indicating if PD should be calculated on creation 
        (preloaded) or only on access.
    release_data_memory -- boolean indicating if the data attribute of the 
        data modality should be set to None after access. Only set this 
        to False, if you know that you have enough memory to hold all 
        of the data in RAM.
    """
    if not preload:
        message = ("Looks like somebody is trying to leave PD to be "
                   "calculated on the fly. This is not yet supported.")
        raise NotImplementedError(message)

    if not metrics:
        metrics = ['mean']

    if recording.excluded:
        _logger.info(
            "Recording %s excluded from processing.", recording.basename)
    elif modality.__name__ not in recording:
        _logger.info("Data modality '%s' not found in session: %s.",
                     modality.__name__, recording.basename)
    else:
        all_requested = AggregateImage.get_names_and_meta(
            modality=modality, metric=metrics,
            mean_image_on_interpolated_data=run_on_interpolated_data,
            release_data_memory=release_data_memory)
        missing_keys = set(all_requested).difference(
            recording.keys())
        to_be_computed = dict((key, value)
                              for key, value in all_requested.items()
                              if key in missing_keys)

        if to_be_computed:
            for key in to_be_computed:
                average_image = calculate_average_image(
                    modality=recording[modality.__name__],
                    params=to_be_computed[key]
                )
                recording.add_statistic(average_image)
                _logger.info("Added '%s' to recording: %s.",
                             average_image.name, recording.basename)
        else:
            _logger.info(
                "Nothing to compute in PD for recording: %s.",
                recording.basename)
