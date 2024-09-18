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
MeanImage RecordingMetric and its Parameter class.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple, Union

import numpy as np

from satkit.data_structures import (
    Modality, Recording, RecordingMetric, RecordingMetricMetaData)
from satkit.helpers import product_dict

_logger = logging.getLogger('satkit.mean_image')


class MeanImageParameters(RecordingMetricMetaData):
    """
    Parameters used in generating the parent MeanImage modality.

    Parameters
    ----------
    parent_name: str
        Name of the Modality this instance of MeanImage was calculated on.
    release_data_memory : bool
        Wether to assign None to parent.data after deriving this Metric from
        the data. Currently has no effect as deriving MeanImage at runtime is
        not yet supported.
    interpolated : bool
        Should this MeanImage be calculated on interpolated images. Defaults to
        False for calculating MeanImage on raw data. This one really can only
        be used on 2D ultrasound data. 
    """
    parent_name: str
    interpolated: bool = False
    release_data_memory: bool = True


class MeanImage(RecordingMetric):
    """
    Represent Mean Image of a Recording as a RecordingMetric. 
    """

    @classmethod
    def generate_name(cls, params: MeanImageParameters) -> str:
        """
        Generate a MeanImage metric name to be used as its unique identifier.

        This static method **defines** what the names are. This implementation
        pattern (MeanImage.name calls this and any where that needs to guess
        what a name would be calls this) is how all derived Modalities should
        work.

        Parameters
        ----------
        params : MeanImageParameters
            The parameters of the MeanImage instance. Note that this
            MeanImageParameters instance does not need to be attached to a
            MeanImage instance.

        Returns
        -------
        str
            Name of the MeanImage instance.
        """
        # name_string = 'MeanImage' + " " + params.metric
        name_string = cls.__name__ + " " + params.metric

        if params.interpolated and params.parent_name:
            name_string = ("Interpolated " + name_string + " on " +
                           params.parent_name)
        elif params.parent_name:
            name_string = name_string + " on " + params.parent_name

        return name_string

    @staticmethod
    def get_names_and_meta(
        modality: Union[Modality, str],
        mean_image_on_interpolated_data: bool = False,
        release_data_memory: bool = True
    ) -> dict[str: MeanImageParameters]:
        """
        Generate MeanImage modality names and metadata.

        This method will generate the full cartesian product of the possible
        combinations. If only some of them are needed, make more than one call
        or weed the results afterwards.

        Parameters
        ----------
        modality : Modality
            parent modality that MeanImage would be derived from
        mean_image_on_interpolated_data : bool, optional
            indicates if interpolated data should be used for instead of
            RawUltrasound, by default False
        release_data_memory: bool
            Should parent Modality's data be assigned to None after
            calculations are complete, by default True.

        Returns
        -------
        dict[str: MeanImageParameters]
            Dictionary where the names of the MeanImage RecordingMetrics index
            the MeanImageParameter objects.
        """
        if isinstance(modality, str):
            parent_name = modality
        else:
            parent_name = modality.__name__

        param_dict = {
            'parent_name': [parent_name],
            'interpolated': [mean_image_on_interpolated_data],
            'release_data_memory': [release_data_memory]}

        mean_image_params = [MeanImageParameters(**item)
                             for item in product_dict(**param_dict)]

        return {MeanImage.generate_name(params): params
                for params in mean_image_params}

    def __init__(self,
                 recording: Recording,
                 metadata: MeanImageParameters,
                 load_path: Optional[Path] = None,
                 meta_path: Optional[Path] = None,
                 parsed_data: Optional[np.ndarray] = None,
                 ) -> None:
        """
        Build a MeanImage RecordingMetric.       

        Parameters
        ----------
        recording : Recording
            the containing Recording.
        metadata : MeanImageParameters
            Parameters used in calculating this instance of MeanImage.
        load_path : Optional[Path], optional
            path of the saved data, by default None
        meta_path : Optional[Path], optional
            path of the saved meta data, by default None
        parsed_data : Optional[np.ndarray], optional
            the actual mean image, by default None
        """
        super().__init__(
            recording,
            metadata=metadata,
            data_path=None,
            load_path=load_path,
            meta_path=meta_path,
            parsed_data=parsed_data)

        self.meta_data = metadata

    def _derive_data(self) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Calculate MeanImage on the data of the parent Modality.  
        """
        raise NotImplementedError(
            "Currently MeanImage Modalities have to be "
            "calculated at instantiation time.")

    def get_meta(self) -> dict:
        """
        Get meta data as a dict.

        This is a helper method for saving as nested text. Allows for rewriting
        any fields that need a simpler representation.

        Returns
        -------
        dict
            The meta data in a dict.
        """
        return self.meta_data.model_dump()

    @property
    def name(self) -> str:
        """
        Identity, metric, and parent data class.

        The name will be of the form
        'MeanImage [metric name] on [data modality class name]'.
        """
        return MeanImage.generate_name(self.meta_data)
