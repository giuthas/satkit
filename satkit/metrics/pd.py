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
Modality for PD (Pixel Difference) and its parameter class.
"""

import logging
from typing import Optional, Tuple, Union

import numpy as np

from pydantic import PositiveInt

from satkit.constants import ImageMask
from satkit.data_structures import (
    FileInformation, Modality, ModalityData,
    ModalityMetaData, Recording
)
from satkit.utility_functions import product_dict

_pd_logger = logging.getLogger('satkit.pd')


class PdParameters(ModalityMetaData):
    """
    Parameters used in generating the parent PD modality.

    Parameters
    ----------
    parent_name: str
        Name of the Modality this instance of PD was calculated on.
    metric : str
        A string specifying this Modality's metric. Defaults to the l1 norm.
    timestep : int 
        A  positive integer used as the timestep in calculating this Modality's
        data. Defaults to 1, which means comparison of consecutive frames.
    release_data_memory : bool
        Whether to assign None to `parent.data` after deriving this Modality
        from the data. Currently, has no effect as deriving PD at runtime is not
        yet supported.
    interpolated : bool
        Should this PD be calculated on interpolated images. Defaults to False
        for calculating PD on raw data. This one really can only be used on 2D
        ultrasound data. For other data raw data is the regular data.
    image_mask : ImageMask
        Should this PD be calculated on a masked image. Defaults to None to
        calculate PD on the whole image.
    """
    parent_name: str
    metric: str = 'l1'
    timestep: PositiveInt = 1
    image_mask: Optional[ImageMask] = None
    interpolated: bool = False
    release_data_memory: bool = True


class PD(Modality):
    """
    Represent Pixel Difference (PD) as a Modality. 
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

    @classmethod
    def generate_name(cls, params: PdParameters) -> str:
        """
        Generate a PD modality name to be used as its unique identifier.

        This static method **defines** what the names are. This implementation
        pattern (PD.name calls this and anywhere that needs to guess what a
        name would be calls this) is how all derived Modalities should work.

        Parameters
        ----------
        params : PdParameters
            The parameters of the PD instance. Note that this PdParameters
            instance does not need to be attached to a PD instance.

        Returns
        -------
        str
            Name of the PD instance.
        """
        # name_string = 'PD' + " " + params.metric
        name_string = cls.__name__ + " " + params.metric

        if params.timestep != 1:
            name_string = name_string + " ts" + str(params.timestep)

        if params.image_mask:
            name_string = name_string + " " + params.image_mask.value

        if params.interpolated and params.parent_name:
            name_string = ("Interpolated " + name_string + " on " +
                           params.parent_name)
        elif params.parent_name:
            name_string = name_string + " on " + params.parent_name

        if params.is_downsampled:
            name_string += " downsampled by " + str(params.downsampling_ratio)

        return name_string

    @staticmethod
    def get_names_and_meta(
            modality: Union[Modality, str],
            norms: list[str] = None,
            timesteps: list[int] = None,
            pd_on_interpolated_data: bool = False,
            mask_images: bool = False,
            release_data_memory: bool = True
    ) -> dict[str: PdParameters]:
        """
        Generate PD modality names and metadata.

        This method will generate the full cartesian product of the possible
        combinations. If only some of them are needed, make more than one call
        or weed the results afterwards.

        Parameters
        ----------
        modality : Modality
            parent modality that PD would be derived from
        norms : List[str], optional
            list of norms to be calculated, defaults to 'l2'.
        timesteps : List[int], optional
            list of timesteps to be used, defaults to 1.
        pd_on_interpolated_data : bool, optional
            indicates if interpolated data should be used for instead of
            RawUltrasound, by default False
        mask_images : bool, optional
            indicates if images should be masked, by default False
        release_data_memory: bool
            Should parent Modality's data be assigned to None after calculations
            are complete, by default True.

        Returns
        -------
        dict[str: PdParameters]
            Dictionary where the names of the PD Modalities index the 
            PdParameter objects.
        """
        if isinstance(modality, str):
            parent_name = modality
        else:
            parent_name = modality.__name__

        if not norms:
            norms = ['l2']
        if not timesteps:
            timesteps = [1]

        if mask_images:
            masks = list(ImageMask)
            masks.append(None)
        else:
            masks = [None]

        param_dict = {
            'parent_name': [parent_name],
            'metric': norms,
            'timestep': timesteps,
            'image_mask': masks,
            'interpolated': [pd_on_interpolated_data],
            'release_data_memory': [release_data_memory]}

        pd_params = [PdParameters(**item)
                     for item in product_dict(**param_dict)]

        return {PD.generate_name(params): params for params in pd_params}

    def __init__(
            self,
            owner: Recording,
            meta_data: PdParameters,
            file_info: FileInformation,
            parsed_data: Optional[ModalityData] = None,
            time_offset: Optional[float] = None
    ) -> None:
        """
        Build a Pixel Difference (PD) Modality       

        Parameters
        ----------
        owner : Recording
            the containing Recording.
        meta_data : PdParameters
            Parameters used in calculating this instance of PD.
        file_info : FileInformation
            Save paths for numerical and meta data.
        parsed_data : Optional[ModalityData], optional
            ModalityData object, by default None. Contains PD values,
            sampling rate, and either timevector and/or time_offset. Providing
            a timevector overrides any time_offset value given, but in absence
            of a timevector the time_offset will be applied on reading the data
            from file.
        time_offset : Optional[float], optional
            If not specified or 0, timeOffset will be copied from dataModality,
            by default None
        """
        # This allows the caller to be lazy.
        if not time_offset:
            if parsed_data:
                time_offset = parsed_data.timevector[0]

        super().__init__(
            owner,
            meta_data=meta_data,
            file_info=file_info,
            parsed_data=parsed_data,
            time_offset=time_offset)

    def _derive_data(self) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Calculate Pixel Difference (PD) on the data Modality parent.       
        """
        raise NotImplementedError(
            "Currently PD Modalities have to be "
            "calculated at instantiation time.")

    def get_meta(self) -> dict:
        # This conversion is done to keep nestedtext working.
        meta = self.meta_data.model_dump()
        meta['image_mask'] = str(meta['image_mask'])
        return meta

    @property
    def name(self) -> str:
        """
        Identity, metric, and parent data class.

        The name will be of the form
        'PD [metric name] on [data modality class name]'.

        This overrides the default behaviour of Modality.name.
        """
        return PD.generate_name(self.meta_data)
