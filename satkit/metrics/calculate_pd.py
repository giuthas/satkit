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

import logging
from typing import Optional

# Numpy and scipy
import numpy as np

# local modules
from satkit.data_structures import (
    FileInformation, Modality, ModalityData, Recording)
from satkit.errors import UnrecognisedNormError

from .metrics_helpers import calculate_timevector
from .pd import ImageMask, PdParameters, PD

_logger = logging.getLogger('satkit.pd')


def calculate_metric(
        abs_diff: np.ndarray,
        norm: str,
        mask: Optional[ImageMask] = None) -> np.ndarray:
    # interpolated: bool = False) -> np.ndarray:
    """
    Module internal method for the actual PD calculation.

    Parameters
    ----------
    abs_diff : np.ndarray
        Pre-calculated absolute differences
    norm : str
        Which norm to calculate
    mask : Optional[ImageMask], optional
        Should the data be masked, by default None
    interpolated : bool, optional
        _description_, by default False

    Returns
    -------
    np.ndarray
        The PD curve

    Raises
    ------
    UnrecognisedNormError
        If the norm is not an lp norm where p belongs in [0, inf], an error is
        raised.
    """
    data = np.copy(abs_diff)
    if mask:
        if mask == ImageMask.BOTTOM:
            half = int(abs_diff.shape[1]/2)
            data = abs_diff[:, half:, :]  # The bottom is on top,
        elif mask == ImageMask.TOP:
            half = int(abs_diff.shape[1]/2)
            data = abs_diff[:, :half, :]  # and top is on bottom.
    # if mask and not interpolated:
    #     if mask == ImageMask.BOTTOM:
    #         half = int(abs_diff.shape[1]/2)
    #         data = abs_diff[:, half:, :]  # The bottom is on top in raw.
    #     elif mask == ImageMask.TOP:
    #         half = int(abs_diff.shape[1]/2)
    #         data = abs_diff[:, :half, :]  # and top is on bottom in raw.
    # elif mask:
    #     if mask == ImageMask.BOTTOM:
    #         half = int(abs_diff.shape[1]/2)
    #         data = abs_diff[:, half:, :]  # These are also upside down.
    #     elif mask == ImageMask.TOP:
    #         half = int(abs_diff.shape[1]/2)
    #         data = abs_diff[:, :half, :]  # These are also upside down.

    if norm[0] == 'l':
        if norm[1:] == '_inf':
            return np.max(data, axis=(1, 2))
        elif norm[1:] == '0':
            # The infinite series definition has also a multiplier term of 2 to
            # the power of k where k is the index of the series. We forgo it
            # because it is only needed to guarantee that the sum over the
            # series converges.
            data = data.astype(np.int32)
            added = data + 1
            elements = np.divide(data, added)
            return np.sum(elements, axis=(1, 2))
        else:
            order = float(norm[1:])
            # if order < 0.09:
            #     sums = np.sum(
            #         np.float_power(data, order, dtype='float128'),
            #         axis=(1, 2))
            # else:
            sums = np.sum(np.float_power(data, order), axis=(1, 2))

            if order < 1:
                return sums
            else:
                return np.float_power(sums, 1.0/order)
    elif norm[0] == 'd':
        return np.bincount(data.flatten().astype('uint8'))
    else:
        raise UnrecognisedNormError(
            f"Don't know how to calculate norm for {norm}.", )


def calculate_slwpd(raw_diff):
    """
    _summary_

    Parameters
    ----------
    raw_diff : _type_
        _description_

    Returns
    -------
    _type_
        _description_
    """
    square_diff = np.square(raw_diff)
    # this should be square rooted at some point
    slw_pd = np.sum(square_diff, axis=2)

    return slw_pd


def calculate_pd(
        parent_modality: Modality,
        to_be_computed: dict[str, PdParameters]) -> list[PD]:
    """
    _summary_

    Parameters
    ----------
    parent_modality : Modality
        _description_
    to_be_computed : dict[str, PdParameters]
        _description_

    Returns
    -------
    list[PD]
        _description_
    """

    _logger.info('%s: Calculating PD on %s.',
                 str(parent_modality.recorded_data_path),
                 parent_modality.name)

    data = parent_modality.data
    sampling_rate = parent_modality.sampling_rate

    # # Use this if we want to collapse e.g. rgb data without producing a
    # # PD contour for each colour or channel.
    # if raw_diff.ndim > 2:
    #     old_shape = raw_diff.shape
    #     new_shape = (old_shape[0], old_shape[1], np.prod(old_shape[2:]))
    #     raw_diff = raw_diff.reshape(new_shape)

    timesteps = [to_be_computed[key].timestep for key in to_be_computed]
    timesteps.sort()
    timevectors = {
        timestep: calculate_timevector(parent_modality.timevector, timestep)
        for timestep in timesteps}

    interpolated = [to_be_computed[key].interpolated for key in to_be_computed]
    if any(interpolated):
        _logger.info('%s: Interpolating frames of %s.',
                     str(parent_modality.data_path), parent_modality.name)
        # TODO: make this into its own derived modality and parallelise the
        # calculation. or make frame interpolation into a filter function that
        # doesn't live in the modality.
        interpolated_data = parent_modality.interpolated_frames()

        abs_diffs_interpolated = {}
        for timestep in timesteps:
            raw_diff_interpolated = np.subtract(interpolated_data[: -timestep],
                                                interpolated_data[timestep:])
            abs_diffs_interpolated[timestep] = np.abs(raw_diff_interpolated)

    abs_diffs = {}
    for timestep in timesteps:
        raw_diff = np.subtract(
            data[: -timestep],
            data[timestep:])
        abs_diffs[timestep] = np.abs(raw_diff)

    pds = []
    param_set = None
    for (_, param_set) in to_be_computed.items():
        if param_set.interpolated:
            norm_data = calculate_metric(
                abs_diffs_interpolated[param_set.timestep],
                norm=param_set.metric, mask=param_set.image_mask)
            # interpolated=param_set.interpolated)
        else:
            norm_data = calculate_metric(
                abs_diffs[param_set.timestep],
                norm=param_set.metric, mask=param_set.image_mask)
            # interpolated=param_set.interpolated)

        modality_data = ModalityData(
            norm_data, sampling_rate, timevectors[param_set.timestep])
        # TODO: add the satkit save path if it is known.
        file_info = FileInformation()
        pds.append(
            PD(
                owner=parent_modality.recording,
                metadata=param_set,
                file_info=file_info,
                parsed_data=modality_data))

    if param_set and param_set.release_data_memory:
        # Accessing the data modality's data causes it to be
        # loaded into memory. Keeping it there may cause memory
        # overflow. This releases the memory.
        parent_modality.data = None

    return pds


def add_pd(recording: Recording,
           modality: Modality,
           preload: bool = True,
           norms: Optional[list[str]] = None,
           timesteps: Optional[list[int]] = None,
           release_data_memory: bool = True,
           pd_on_interpolated_data: bool = False,
           mask_images: bool = False) -> None:
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

    if not norms:
        norms = ['l2']
    if not timesteps:
        timesteps = [1]

    if recording.excluded:
        _logger.info(
            "Recording %s excluded from processing.", recording.basename)
    elif not modality.__name__ in recording:
        _logger.info("Data modality '%s' not found in recording: %s.",
                     modality.__name__, recording.basename)
    else:
        all_requested = PD.get_names_and_meta(
            modality, norms, timesteps, pd_on_interpolated_data, mask_images,
            release_data_memory)
        missing_keys = set(all_requested).difference(
            recording.keys())
        to_be_computed = dict((key, value) for key,
                              value in all_requested.items()
                              if key in missing_keys)

        data_modality = recording[modality.__name__]

        if to_be_computed:
            pds = calculate_pd(data_modality, to_be_computed)

            for pd in pds:
                recording.add_modality(pd)
                _logger.info("Added '%s' to recording: %s.",
                             pd.name, recording.basename)
        else:
            _logger.info(
                "Nothing to compute in PD for recording: %s.",
                recording.basename)
