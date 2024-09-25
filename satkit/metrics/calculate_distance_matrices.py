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
Calculate DistanceMatrices between a Session's Recordings.
"""

import logging
from typing import Optional

import numpy as np

# local modules
from satkit.data_structures import Modality, Session
from satkit.helpers import mean_squared_error

from .distance_matrix import DistanceMatrix

_logger = logging.getLogger('satkit.session_mse')


def calculate_mse(images: list[np.ndarray]) -> np.ndarray:
    """
    Calculate mean squared errors between all pairs in the list.

    Parameters
    ----------
    images : list[np.ndarray]
        Images of some sort as plain 2D np.ndarrays.

    Returns
    -------
    np.ndarray
        Matrix where matrix[i,j] is the MSE between the ith and jth image in
        the list. The matrix is symmetric: matrix[i,j] = matrix[j,i].
    """
    mean_squared_errors = np.zeros([len(images), len(images)])

    for i, image1 in enumerate(images):
        for j in range(i+1, len(images)):
            image2 = images[j]
            mse = mean_squared_error(image1, image2)
            mean_squared_errors[i, j] = mse
            mean_squared_errors[j, i] = mse

    return mean_squared_errors


def add_distance_matrices(
    session: Session,
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
        metrics = ['mean_squared_error']

    if session.excluded:
        _logger.info(
            "Session %s excluded from processing.", session.basename)
    elif not modality.__name__ in session:
        _logger.info("Data modality '%s' not found in session: %s.",
                     modality.__name__, session.basename)
    else:
        all_requested = DistanceMatrix.get_names_and_meta(
            modality=modality, metric=metrics,
            distance_matrix_on_interpolated_data=run_on_interpolated_data,
            release_data_memory=release_data_memory)
        missing_keys = set(all_requested).difference(
            session.keys())
        to_be_computed = dict((key, value) for key,
                              value in all_requested.items()
                              if key in missing_keys)

        if to_be_computed:
            images = [recording[modality.__name__].data
                      for recording in session.recordings]
            matrices = calculate_mse(images)

            for matrix in matrices:
                session.add_modality(matrix)
                _logger.info("Added '%s' to recording: %s.",
                             matrix.name, session.basename)
        else:
            _logger.info(
                "Nothing to compute in PD for recording: %s.",
                session.basename)
