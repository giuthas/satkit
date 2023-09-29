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
# Built in packages
from typing import Optional

# Numpy and scipy
import numpy as np
from icecream import ic
# local modules
from satkit.data_structures import Modality, ModalityData, ModalityMetaData, Recording
from satkit.errors import UnrecognisedNormError
from .pd import ImageMask, PdParameters, PD
from satkit.processing_helpers import product_dict

_pd_logger = logging.getLogger('satkit.pd')


def calculate_timevector(original_timevector, timestep):
    if timestep == 1:
        half_step_early = (original_timevector[0:-1])
        half_step_late = (original_timevector[1:])
        timevector = (half_step_early+half_step_late)/2
    elif timestep % 2 == 1:
        begin = timestep // 2
        end = -(timestep // 2 + 1)
        half_step_early = (original_timevector[begin:end])
        half_step_late = (original_timevector[begin+1:end+1])
        timevector = (half_step_early+half_step_late)/2
    else:
        timevector = original_timevector[timestep//2:-timestep//2]
    return timevector


def calculate_metric(
        abs_diff, norm, mask: Optional[ImageMask] = None, interpolated:
        bool = False):
    data = np.copy(abs_diff)
    if mask and not interpolated:
        if mask == ImageMask.bottom:
            half = int(abs_diff.shape[1]/2)
            data = abs_diff[:, half:, :]  # The bottom is on top in raw.
        elif mask == ImageMask.top:
            half = int(abs_diff.shape[1]/2)
            data = abs_diff[:, :half, :]  # and top is on bottom in raw.
    elif mask:
        if mask == ImageMask.bottom:
            half = int(abs_diff.shape[1]/2)
            data = abs_diff[:, half:, :]  # These are also upside down.
        elif mask == ImageMask.top:
            half = int(abs_diff.shape[1]/2)
            data = abs_diff[:, :half, :]  # These are also upside down.

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
            #     sums = np.sum(np.float_power(data, order, dtype='float128'), axis=(1, 2))
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
            "Don't know how to calculate norm for %s.", norm)


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
        norms: list[str] = ['l1'],
        timesteps: list[int] = [1],
        release_data_memory: bool = True,
        pd_on_interpolated_data: bool = False,
        mask_images: bool = False) -> list['PD']:
    """
    Calculate Pixel Difference (PD) on the data Modality parent.       

    If self._timesteps is a vector of positive integers, then calculate
    pd for each of those. 
    """
    if not all(norm in PD.accepted_metrics for norm in norms):
        ValueError("Unexpected norm requested in " + str(norms))

    _pd_logger.info(str(parent_modality.data_path)
                    + ': Calculating PD on '
                    + parent_modality.name + '.')

    data = parent_modality.data
    parent_name = parent_modality.name

    # # TODO: Make this happen in processing LipVideo, not here.
    # # Hacky hack to recognise LipVideo data and change the timestep for it.
    # if len(data.shape) != 3:
    #     timesteps[0] = 2

    # # Use this if we want to collapse e.g. rgb data without producing a
    # # PD contour for each colour or channel.
    # if raw_diff.ndim > 2:
    #     old_shape = raw_diff.shape
    #     new_shape = (old_shape[0], old_shape[1], np.prod(old_shape[2:]))
    #     raw_diff = raw_diff.reshape(new_shape)

    if pd_on_interpolated_data:
        _pd_logger.info(str(parent_modality.data_path)
                        + ': Interpolating frames of '
                        + parent_modality.name + '.')
        interpolated_data = parent_modality.interpolated_frames()

    pds = []
    sampling_rate = parent_modality.sampling_rate
    for timestep in timesteps:
        timevector = calculate_timevector(parent_modality.timevector,
                                          timestep)
        raw_diff = np.subtract(data[: -timestep], data[timestep:])
        abs_diff = np.abs(raw_diff)
        if pd_on_interpolated_data:
            raw_diff_interpolated = np.subtract(interpolated_data[: -timestep],
                                                interpolated_data[timestep:])
            abs_diff_interpolated = np.abs(raw_diff_interpolated)
        for norm in norms:
            norm_data = calculate_metric(abs_diff, norm)
            modality_data = ModalityData(norm_data, sampling_rate,
                                         timevector)
            pd_params = PdParameters(
                metric=norm, timestep=timestep, interpolated=False,
                release_data_memory=release_data_memory, image_mask=None,
                parent_name=parent_name)
            pds.append(
                PD(parent_modality.recording, pd_params,
                    parsed_data=modality_data)
            )
            if pd_on_interpolated_data:
                norm_data = calculate_metric(abs_diff_interpolated, norm)
                modality_data = ModalityData(norm_data, sampling_rate,
                                             timevector)
                pd_params = PdParameters(
                    metric=norm, timestep=timestep, interpolated=True,
                    release_data_memory=release_data_memory, image_mask=None,
                    parent_name=parent_name)
                pds.append(
                    PD(parent_modality.recording, pd_params,
                        parsed_data=modality_data)
                )
            if mask_images:
                for mask in ImageMask:
                    norm_data = calculate_metric(abs_diff, norm, mask)
                    modality_data = ModalityData(norm_data, sampling_rate,
                                                 timevector)
                    pd_params = PdParameters(
                        metric=norm, timestep=timestep, interpolated=False,
                        release_data_memory=release_data_memory,
                        image_mask=mask, parent_name=parent_name)
                    pds.append(
                        PD(parent_modality.recording, pd_params,
                            parsed_data=modality_data)
                    )
                    if pd_on_interpolated_data:
                        norm_data = calculate_metric(
                            abs_diff_interpolated, norm, mask,
                            interpolated=True)
                        modality_data = ModalityData(norm_data, sampling_rate,
                                                     timevector)
                        pd_params = PdParameters(
                            metric=norm, timestep=timestep, interpolated=True,
                            release_data_memory=release_data_memory,
                            image_mask=mask, parent_name=parent_name)
                        pds.append(
                            PD(parent_modality.recording, pd_params,
                                parsed_data=modality_data)
                        )

    _pd_logger.debug(str(parent_modality.data_path)
                     + ': PD calculated.')

    if release_data_memory:
        # Accessing the data modality's data causes it to be
        # loaded into memory. Keeping it there may cause memory
        # overflow. This releases the memory.
        parent_modality.data = None

    return pds


def calculate_intensity(parent_modality: Modality):
    data = parent_modality.data
    return np.sum(data, axis=(1, 2))
    # TODO: Compare this to the PD similarity matrix used by Gabor et al.


def calculate_pd_from_params(
        parent_modality: Modality,
        to_be_computed: dict[str, PdParameters]
) -> list[PD]:
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

    parent_name = parent_modality.name
    _pd_logger.info(str(parent_modality.data_path)
                    + ': Calculating PD on '
                    + parent_name + '.')

    data = parent_modality.data
    sampling_rate = parent_modality.sampling_rate

    # # TODO: Make this happen in processing LipVideo, not here.
    # # Hacky hack to recognise LipVideo data and change the timestep for it.
    # if len(data.shape) != 3:
    #     timesteps[0] = 2

    # # Use this if we want to collapse e.g. rgb data without producing a
    # # PD contour for each colour or channel.
    # if raw_diff.ndim > 2:
    #     old_shape = raw_diff.shape
    #     new_shape = (old_shape[0], old_shape[1], np.prod(old_shape[2:]))
    #     raw_diff = raw_diff.reshape(new_shape)

    ic(to_be_computed)
    timesteps = [to_be_computed[key].timestep for key in to_be_computed]
    timesteps.sort()
    timevectors = {
        timestep: calculate_timevector(parent_modality.timevector, timestep)
        for timestep in timesteps}

    interpolated = [to_be_computed[key].interpolated for key in to_be_computed]
    if any(interpolated):
        _pd_logger.info(str(parent_modality.data_path)
                        + ': Interpolating frames of '
                        + parent_modality.name + '.')
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
    for (_, param_set) in to_be_computed.items():
        if param_set.interpolated:
            norm_data = calculate_metric(
                abs_diffs_interpolated[param_set.timestep],
                norm=param_set.metric, mask=param_set.image_mask,
                interpolated=param_set.interpolated)
        else:
            norm_data = calculate_metric(
                abs_diffs[param_set.timestep],
                norm=param_set.metric, mask=param_set.image_mask,
                interpolated=param_set.interpolated)

        modality_data = ModalityData(
            norm_data, sampling_rate, timevectors[param_set.timestep])
        pds.append(PD(parent_modality.recording,
                   param_set, parsed_data=modality_data))

    if param_set.release_data_memory:
        # Accessing the data modality's data causes it to be
        # loaded into memory. Keeping it there may cause memory
        # overflow. This releases the memory.
        parent_modality.data = None

    return pds


def add_pd(recording: Recording,
           modality: Modality,
           preload: bool = True,
           norms: list[str] = ['l2'],
           timesteps: list[int] = [1],
           release_data_memory: bool = True,
           pd_on_interpolated_data: bool = False,
           mask_images: bool = False):
    """
    Calculate PD on dataModality and add it to recording.

    Positional arguments:
    recording -- a Recording object
    modality -- the type of the Modality to be processed. The access will 
        be by recording.modalities[modality.__name__]

    Keyword arguments:
    preload -- boolean indicating if PD should be calculated on creation 
        (preloaded) or only on access.
    releaseDataMemor -- boolean indicatin if the data attribute of the 
        data modality should be set to None after access. Only set this 
        to False, if you know that you have enough memory to hold all 
        of the data in RAM.
    """

    if recording.excluded:
        _pd_logger.info(
            "Recording " + recording.basename
            + " excluded from processing.")
    elif not modality.__name__ in recording.modalities:
        _pd_logger.info(
            "Data modality '" + modality.__name__ +
            "' not found in recording: " + recording.basename + '.')
    else:
        all_requested = PD.get_names_and_meta(
            modality, norms, timesteps, pd_on_interpolated_data, mask_images)
        missing_keys = set(all_requested).difference(
            recording.modalities.keys())
        to_be_computed = dict((key, value) for key,
                              value in all_requested.items()
                              if key in missing_keys)

        dataModality = recording.modalities[modality.__name__]
        # pds = calculate_pd(dataModality,
        #                    norms=norms,
        #                    timesteps=timesteps,
        #                    release_data_memory=release_data_memory,
        #                    pd_on_interpolated_data=pd_on_interpolated_data,
        #                    mask_images=mask_images)

        if to_be_computed:
            pds = calculate_pd_from_params(dataModality, to_be_computed)

            for pd in pds:
                recording.add_modality(pd)
            _pd_logger.info(
                "Added '" + pd.name +
                "' to recording: " + recording.basename + '.')
        else:
            _pd_logger.info(
                "Nothing to compute in PD for recording: " +
                recording.basename + '.')
