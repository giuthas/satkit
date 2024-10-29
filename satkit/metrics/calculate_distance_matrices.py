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

from satkit.data_structures import FileInformation, Session
from .distance_matrix import DistanceMatrix, DistanceMatrixParameters
from ..utility_functions import mean_squared_error

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

    shapes = [image.shape for image in images]
    if not all(shape == shapes[0] for shape in shapes):
        _logger.critical(
            'Images must have the same shape. Found \n%s',
            str(shapes))
        raise ValueError(
            'Images must have the same shape. See log for details.')

    for i, image1 in enumerate(images):
        for j in range(i + 1, len(images)):
            image2 = images[j]
            mse = mean_squared_error(image1, image2)
            mean_squared_errors[i, j] = mse
            mean_squared_errors[j, i] = mse

    return mean_squared_errors


def calculate_distance_matrix(
        session: Session,
        parent_name: str,
        params: DistanceMatrixParameters
) -> DistanceMatrix | None:
    images = [recording.statistics[parent_name].data
              for recording in session.recordings
              if parent_name in recording.statistics and
              not recording.excluded]

    if params.slice_size:
        begin = params.slice_offset
        end = params.slice_offset + params.slice_size
        images = [recording.statistics[parent_name].data[begin:end, :]
                  for recording in session.recordings
                  if parent_name in recording.statistics and
                  not recording.excluded]

    if not images:
        _logger.info(
            "Data object '%s' not found in recordings of session: %s.",
            parent_name, session.name)
        return None

    match params.metric:
        case 'mean_squared_error':
            matrix = calculate_mse(images)
        case _:
            raise ValueError(f"Unknown metric {params.metric}.")

    return DistanceMatrix(
        owner=session,
        meta_data=params,
        file_info=FileInformation(),
        parsed_data=matrix, )


def add_distance_matrices(
        session: Session,
        parent: str,
        preload: bool = True,
        metrics: Optional[list[str]] = None,
        release_data_memory: bool = True,
        slice_size: int | None = None,
        slice_offset: tuple[int] | None = None,
) -> None:
    if not preload:
        message = ("Looks like somebody is trying to leave PD to be "
                   "calculated on the fly. This is not yet supported.")
        raise NotImplementedError(message)

    if isinstance(parent, str):
        parent_name = parent
    else:
        parent_name = parent.__name__

    all_requested = DistanceMatrix.get_names_and_meta(
        parent=parent, metric=metrics,
        release_data_memory=release_data_memory)
    missing_keys = set(all_requested).difference(
        session.statistics.keys())
    to_be_computed = dict((key, value) for key, value in all_requested.items()
                          if key in missing_keys)

    if to_be_computed:
        for key in to_be_computed:
            params = to_be_computed[key]
            distance_matrix = calculate_distance_matrix(
                session, parent_name, params)
            # images = [recording.statistics[parent_name].data
            #           for recording in session.recordings
            #           if parent_name in recording.statistics and
            #           not recording.excluded]
            # if not images:
            #     _logger.info(
            #         "Data object '%s' not found in recordings of session: %s.",
            #         parent_name, session.name)
            #     return
            #
            # matrix = calculate_mse(images)
            #
            # distance_matrix = DistanceMatrix(
            #     owner=session,
            #     meta_data=params,
            #     file_info=FileInformation(),
            #     parsed_data=matrix,)
            if distance_matrix is not None:
                session.add_statistic(distance_matrix)
                _logger.info("Added '%s' to session: %s.",
                             distance_matrix.name, session.name)
    else:
        _logger.info(
            "Nothing to compute in PD for recording: %s.",
            session.name)
