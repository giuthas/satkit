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
from icecream import ic

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

    _logger.info("Calculating MSE. Image sizes are %s.",
                 str([image.shape for image in images]))

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

    recordings = [
        recording for recording in session
        if parent_name in recording.statistics and not recording.excluded
    ]
    if len(recordings) == 0:
        _logger.info(
            "Data object '%s' not found in recordings of session: %s.",
            parent_name, session.name)
        return None

    if params.sort:
        prompts = [
            recording.meta_data.prompt for recording in recordings
        ]
        prompts, indeces = zip(*sorted(zip(prompts, range(len(prompts)))))
        sorted_recordings = [
            recordings[index] for index in indeces
        ]
        recordings = sorted_recordings

    images = [
        recording.statistics[parent_name].data for recording in recordings
    ]

    matrix = None
    if params.slice_max_step:
        sliced_images = []
        data_length = images[0].shape[1]
        for i in range(params.slice_max_step + 1):
            begin = i
            end = data_length - (params.slice_max_step - i)
            new_images = [
                image[:, begin:end] for image in images
            ]
            sliced_images.extend(new_images)

        match params.metric:
            case 'mean_squared_error':
                matrix = calculate_mse(sliced_images)
            case _:
                raise ValueError(f"Unknown metric {params.metric}.")

    elif params.slice_step_to:
        matrix = np.zeros((2*len(images), params.slice_step_to*2*len(images)))
        for step in range(params.slice_step_to):
            sliced_images = []
            first = [
                image[:, :-(step+1)] for image in images
            ]
            sliced_images.extend(first)
            second = [
                image[:, (step+1):] for image in images
            ]
            sliced_images.extend(second)
            match params.metric:
                case 'mean_squared_error':
                    new_values = calculate_mse(sliced_images)
                case _:
                    raise ValueError(f"Unknown metric {params.metric}.")
            ic(matrix.shape, new_values.shape)
            matrix[:, step * 2*len(images):(step + 1) * 2*len(images)] = new_values

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
        slice_max_step: int | None = None,
        slice_step_to: int | None = None,
        sort: bool = False,
) -> None:
    if not preload:
        message = ("Looks like somebody is trying to leave Distance Matrices "
                   "to be calculated on the fly. This is not yet supported.")
        raise NotImplementedError(message)

    if isinstance(parent, str):
        parent_name = parent
    else:
        parent_name = parent.__name__

    first_parent_in_session = next(
        recording.statistics[parent_name] for recording in session
        if parent_name in recording.statistics)

    all_requested = DistanceMatrix.get_names_and_meta(
        parent=first_parent_in_session,
        metric=metrics,
        release_data_memory=release_data_memory,
        slice_max_step=slice_max_step,
        slice_step_to=slice_step_to,
        sort=sort,
    )
    missing_keys = set(all_requested).difference(
        session.statistics.keys())
    to_be_computed = dict((key, value) for key, value in all_requested.items()
                          if key in missing_keys)

    if to_be_computed:
        for key in to_be_computed:
            params = to_be_computed[key]
            distance_matrix = calculate_distance_matrix(
                session, parent_name, params)
            if distance_matrix is not None:
                session.add_statistic(distance_matrix)
                _logger.info("Added '%s' to session: %s.",
                             distance_matrix.name, session.name)
    else:
        _logger.info(
            "Nothing to compute in PD for recording: %s.",
            session.name)
