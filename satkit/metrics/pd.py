#
# Copyright (c) 2019-2022 Pertti Palo, Scott Moisik, Matthew Faytak, and Motoki Saito.
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
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple

# Numpy and scipy
import numpy as np
# local modules
from satkit.data_structures import Modality, ModalityData, Recording
from satkit.errors import UnrecognisedNormError

_pd_logger = logging.getLogger('satkit.pd')

class ImageMask(Enum):
    top = "top"
    bottom = "bottom"
    whole = "whole"

    def __str__(self):
        return self.value

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

def calculate_metric(abs_diff, norm, mask: Optional[ImageMask]=None, interpolated: bool=False):
    data = np.copy(abs_diff)
    if mask and not interpolated:
        if mask == ImageMask.bottom:
            half = int(abs_diff.shape[1]/2)
            data = abs_diff[:,half:,:] # The bottom is on top in raw.
        elif mask == ImageMask.top:
            half = int(abs_diff.shape[1]/2)
            data = abs_diff[:,:half,:] # and top is on bottom in raw.
    elif mask:
        if mask == ImageMask.bottom:
            half = int(abs_diff.shape[1]/2)
            data = abs_diff[:,half:,:] # These are also upside down.
        elif mask == ImageMask.top:
            half = int(abs_diff.shape[1]/2)
            data = abs_diff[:,:half,:] # These are also upside down.

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
        return np.bincount(data.flatten())
    else:
        raise UnrecognisedNormError("Don't know how to calculate norm for %s.", norm)

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
        norms: List[str]=['l2'], 
        timesteps: List[int]=[1], 
        release_data_memory: bool=True,
        pd_on_interpolated_data: bool=False,
        mask_images: bool=False) -> List['PD']:
    """
    Calculate Pixel Difference (PD) on the data Modality parent.       

    If self._timesteps is a vector of positive integers, then calculate
    pd for each of those. 
    """
    if not all(norm in PD.accepted_metrics for norm in norms):
        ValueError("Unexpected norm requested in " + str(norms))

    if not all((isinstance(timestep, int) and timestep > 0)
            for timestep in timesteps):
        ValueError("Negative or non-integer timestep in " + 
                    str(timesteps))

    _pd_logger.info(str(parent_modality.data_path)
                    + ': Calculating PD on '
                    + type(parent_modality).__name__ + '.')

    data = parent_modality.data

    # TODO wrap this up in its own modality generation, 
    # but within the same read context - so run with pd 
    # between reading data and releasing memory
    intensity = np.sum(data, axis=(1,2))

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
            pds.append(
                PD(
                parent_modality.recording,
                parent=parent_modality,
                parsed_data=modality_data,
                metric=norm, 
                timestep=timestep)
            )
            if pd_on_interpolated_data:
                norm_data = calculate_metric(abs_diff_interpolated, norm)
                modality_data = ModalityData(norm_data, sampling_rate, 
                                            timevector)
                pds.append(
                    PD(
                    parent_modality.recording,
                    parent=parent_modality,
                    parsed_data=modality_data,
                    metric=norm, 
                    timestep=timestep,
                    interpolated=True)
                )
            if mask_images:
                for mask in ImageMask:
                    norm_data = calculate_metric(abs_diff, norm, mask)
                    modality_data = ModalityData(norm_data, sampling_rate, 
                                                timevector)
                    pds.append(
                        PD(
                        parent_modality.recording,
                        parent=parent_modality,
                        parsed_data=modality_data,
                        metric=norm, 
                        timestep=timestep,
                        image_mask=mask)
                    )
                    if pd_on_interpolated_data:
                        norm_data = calculate_metric(abs_diff_interpolated, norm, mask, interpolated=True)
                        modality_data = ModalityData(norm_data, sampling_rate, 
                                                    timevector)
                        pds.append(
                            PD(
                            parent_modality.recording,
                            parent=parent_modality,
                            parsed_data=modality_data,
                            metric=norm, 
                            timestep=timestep,
                            interpolated=True,
                            image_mask=mask)
                        )

    _pd_logger.debug(str(parent_modality.data_path)
                        + ': PD calculated.')


    if release_data_memory:
        # Accessing the data modality's data causes it to be
        # loaded into memory. Keeping it there may cause memory
        # overflow. This releases the memory.
        parent_modality.data = None

    return pds

def add_pd(recording: Recording,
          modality: Modality,
          preload: bool=True,
          norms: List[str]=['l2'],
          timesteps: List[int]=[1],
          release_data_memory: bool=True,
          pd_on_interpolated_data: bool=False,
          mask_images: bool=False):
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
    #modality = recording.modalities[modality_name]
    # Name of the new modality is constructed from the type names of
    # PD and the data modality.
    pd_name = 'PD on ' + modality.__name__
    if recording.excluded:
        _pd_logger.info(
            "Recording " + recording.basename
            + " excluded from processing.")
    elif pd_name in recording.modalities:
        _pd_logger.info(
            "Modality '" + pd_name +
            "' already exists in recording: " + recording.basename + '.')
    elif not modality.__name__ in recording.modalities:
        _pd_logger.info(
            "Data modality '" + modality.__name__ +
            "' not found in recording: " + recording.basename + '.')
    else:
        dataModality = recording.modalities[modality.__name__]
        pds = calculate_pd(dataModality,
                norms=norms, 
                timesteps=timesteps, 
                release_data_memory=release_data_memory,
                pd_on_interpolated_data=pd_on_interpolated_data,
                mask_images=mask_images) 
        for pd in pds:
            recording.add_modality(pd)
        _pd_logger.info(
            "Added '" + pd_name +
            "' to recording: " + recording.basename + '.')

class PD(Modality):
    """
    Represent Pixel Difference (PD) as a Modality. 

    PD maybe calculated using several different norms and therefore the
    result may be non-singular. For this reason self.data is a dict
    containing a PD curve for each key.
    """

    accepted_metrics = [
        'l1',
        'l2',
        'l3',
        'l4',
        'l5',
        'l6',
        'l7',
        'l8',
        'l9',
        'l10',
        'inf',
    ]

    def __init__(self, 
                recording: Recording, 
                load_path: Optional[Path]=None,
                parent: Optional[Modality]=None,
                parsed_data: Optional[ModalityData]=None,
                time_offset: Optional[float]=None,
                release_data_memory: bool=True, 
                metric: str='l2',
                timestep: int=1,
                interpolated: bool=False,
                image_mask: Optional[ImageMask]=None) -> None:
        """
        Build a Pixel Difference (PD) Modality       

        Positional arguments:
        recording -- the containing Recording.        

        Keyword arguments:
        load_path -- path of the saved data - both ultrasound and metadata
        parent -- the Modality this one was derived from. None means this 
            is an underived data Modality.
            If parent is None, it will be copied from dataModality.
        parsed_data -- ModalityData object containing raw ultrasound, sampling rate,
            and either timevector and/or time_offset. Providing a timevector 
            overrides any time_offset value given, but in absence of a 
            timevector the time_offset will be applied on reading the data 
            from file. 
        timeoffset -- timeoffset in seconds against the Recordings baseline.
            If not specified or 0, timeOffset will be copied from dataModality.
        release_data_memory -- wether to assing None to parent.data after 
            deriving this Modality from the data. Currently has no effect 
            as deriving PD at runtime is not supported.
        metric -- a string specifying this Modality's metric.
        timestep -- a  positive integer used as the timestep in calculating 
            this Modality's data.
        """
        # This allows the caller to be lazy.
        if not time_offset:
            time_offset = parent.time_offset

        self.metric = metric
        self.timestep = timestep
        self.interpolated = interpolated
        self.release_data_memory = release_data_memory
        self.image_mask = image_mask

        super().__init__(
                recording, 
                data_path=None,
                load_path=load_path,
                parent=parent,
                parsed_data=parsed_data)


    def _derive_data(self) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Calculate Pixel Difference (PD) on the data Modality parent.       
        """
        raise NotImplementedError("Currently PD Modalities have to be calculated at instantiation time.")

    def get_meta(self) -> dict:
        return {
            'metric': self.metric,
            'timestep': self.timestep,
            'interpolated': self.interpolated,
            'image_mask': str(self.image_mask)
        }

    @property
    def name(self) -> str:
        """
        Identity, metric, and parent data class.
        
        The name will be of the form
        'PD [metric name] on [data modality class name]'.

        This overrides the default behaviour of Modality.name.
        """
        name_string = self.__class__.__name__ + " " + self.metric

        if self.image_mask:
            name_string = name_string + " " + self.image_mask.value

        if self.interpolated and self.parent:
            name_string = "Interpolated " + name_string + " on " + self.parent.__class__.__name__
        elif self.parent:
            name_string = name_string + " on " + self.parent.__class__.__name__

        return name_string

