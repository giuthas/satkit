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
Calculate DistanceMatrices between a Session's Recordings.
"""

import logging
from pathlib import Path
from typing import Optional

import numpy as np

from satkit.data_structures import FileInformation, Session
from .distance_matrix import DistanceMatrix, DistanceMatrixParameters
from ..configuration import (
    ExclusionList, load_exclusion_list,
    remove_excluded_recordings
)
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

    recordings = remove_excluded_recordings(
        recordings=session.recordings,
        exclusion_list=params.exclusion_list)
    if len(recordings) == 0:
        _logger.info(
            "Data object '%s' not found in recordings of session: %s.",
            parent_name, session.name)
        return None

    if params.sort:
        prompts = [
            recording.metadata.prompt for recording in recordings
        ]
        if params.sort_criteria is None:
            prompts, indeces = zip(*sorted(zip(prompts, range(len(prompts)))))
            sorted_recordings = [
                recordings[index] for index in indeces
            ]
        else:
            sorted_recordings = []
            sorted_prompts = []
            for key in params.sort_criteria:
                block = [
                    recording for recording in recordings
                    if key in recording.metadata.prompt
                ]
                if len(block) == 0:
                    continue

                prompts = [
                    recording.metadata.prompt for recording in block
                ]
                prompts, indeces = zip(
                    *sorted(zip(prompts, range(len(prompts)))))
                block = [
                    block[index] for index in indeces
                ]
                sorted_recordings.extend(block)
                sorted_prompts.extend(prompts)
            remaining_prompts = set(prompts) - set(sorted_prompts)
            if len(remaining_prompts) > 0:
                last_block = [
                    recording for recording in recordings
                    if recording.metadata.prompt in remaining_prompts]
                prompts = [
                    recording.metadata.prompt for recording in last_block]
                prompts, indeces = zip(
                    *sorted(zip(prompts, range(len(prompts)))))
                block = [last_block[index] for index in indeces]
                sorted_recordings.extend(block)
        sorted_indeces = []
        for recording in sorted_recordings:
            for i, unsorted in enumerate(recordings):
                if unsorted == recording:
                    sorted_indeces.append(i)
                    break
        recordings = sorted_recordings
        params.sorted_indeces = sorted_indeces
        params.sorted_prompts = [
            recording.metadata.prompt for recording in recordings]
        params.sorted_filenames = [
            recording.metadata.basename for recording in recordings]
    images = [
        recording.statistics[parent_name].data for recording in recordings
        if parent_name in recording.statistics
    ]

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
        data_length = 2*len(images)
        matrix = np.zeros((data_length, params.slice_step_to*data_length))
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
            matrix[:, step * data_length:(step + 1) * data_length] = new_values
    else:
        match params.metric:
            case 'mean_squared_error':
                matrix = calculate_mse(images)
            case _:
                raise ValueError(f"Unknown metric {params.metric}.")


    return DistanceMatrix(
        owner=session,
        metadata=params,
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
        sort_criteria: list[str] | None = None,
        exclusion_list: Path | ExclusionList | None = None,
) -> None:
    if not preload:
        message = ("Looks like somebody is trying to leave Distance Matrices "
                   "to be calculated on the fly. This is not yet supported.")
        raise NotImplementedError(message)

    if isinstance(parent, str):
        parent_name = parent
    else:
        parent_name = parent.__name__

    if isinstance(exclusion_list, Path):
        exclusion_list = load_exclusion_list(exclusion_list)

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
        sort_criteria=sort_criteria,
        exclusion_list=exclusion_list
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
