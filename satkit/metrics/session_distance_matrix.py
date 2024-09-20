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
DistanceMatrix RecordingSessionMetric and its Parameter class.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple, Union

import numpy as np

from satkit.data_structures import (
    Modality, RecordingSession, Statistic, StatisticMetaData)
from satkit.helpers import product_dict

_logger = logging.getLogger('satkit.mse')


class DistanceMatrixParameters(StatisticMetaData):
    """
    Parameters used in generating the parent DistanceMatrix.

    Parameters
    ----------
    parent_name: str
        Name of the Modality this instance of DistanceMatrix was calculated on.
    metric : str
        A string specifying this DistanceMatrix's metric. Defaults to mean
        squared error.
    release_data_memory : bool
        Wether to assign None to parent.data after deriving this Modality from
        the data. Currently has no effect as deriving a DistanceMatrix at
        runtime is not yet supported.
    interpolated : bool
        Should this DistanceMatrix be calculated on interpolated images.
        Defaults to False for calculating DistanceMatrix on raw data. This one
        really can only be used on 2D ultrasound data. For other data raw data
        is the regular data.
    """
    parent_name: str
    metric: str = 'mean_squared_error'
    interpolated: bool = False
    release_data_memory: bool = True


class DistanceMatrix(Statistic):
    """
    DistanceMatrix gives the distances between the Recordings.

    The distances can be e.g. mean squared errors between mean ultrasound
    images, same for a selected period, etc.
    """

    accepted_metrics = [
        'mean_squared_error',
    ]

    @classmethod
    def generate_name(cls, params: DistanceMatrixParameters) -> str:
        """
        Generate a DistanceMatrix name to be used as its unique identifier.

        This static method **defines** what the names are. This implementation
        pattern (DistanceMatrix.name calls this and any where that needs to
        guess what a name would be calls this) is how all derived Modalities
        should work.

        Parameters
        ----------
        params : DistanceMatrixParameters
            The parameters of the DistanceMatrix instance. Note that this
            DistanceMatrixParameters instance does not need to be attached to a
            DistanceMatrix instance.

        Returns
        -------
        str
            Name of the DistanceMatrix instance.
        """
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
        metric: list[str] = None,
        distance_matrix_on_interpolated_data: bool = False,
        release_data_memory: bool = True
    ) -> dict[str: DistanceMatrixParameters]:
        """
        Generate DistanceMatrix names and metadata.

        This method will generate the full cartesian product of the possible
        combinations. If only some of them are needed, make more than one call
        or weed the results afterwards.

        Parameters
        ----------
        modality : Modality
            parent modality that DistanceMatrix would be derived from
        norms : List[str], optional
            list of norms to be calculated, defaults to 'mean_squared_error'.
        timesteps : List[int], optional
            list of timesteps to be used, defaults to 1.
        mse_on_interpolated_data : bool, optional
            indicates if interpolated data should be used for instead of
            RawUltrasound, by default False
        mask_images : bool, optional
            indicates if images should be masked, by default False
        release_data_memory: bool
            Should parent Modlity's data be assigned to None after calculations
            are complete, by default True.

        Returns
        -------
        dict[str: DistanceMatrixParameters]
            Dictionary where the names of the DistanceMatrices index the 
            DistanceMatrixParameter objects.
        """
        if isinstance(modality, str):
            parent_name = modality
        else:
            parent_name = modality.__name__

        if not metric:
            metric = ['mean_squared_error']

        param_dict = {
            'parent_name': [parent_name],
            'metric': metric,
            'interpolated': [distance_matrix_on_interpolated_data],
            'release_data_memory': [release_data_memory]}

        distance_matrix_params = [DistanceMatrixParameters(**item)
                                  for item in product_dict(**param_dict)]

        return {DistanceMatrix.generate_name(params): params
                for params in distance_matrix_params}

    def __init__(self,
                 owner: RecordingSession,
                 meta_data: DistanceMatrixParameters,
                 load_path: Optional[Path] = None,
                 meta_path: Optional[Path] = None,
                 parsed_data: Optional[np.ndarray] = None,
                 ) -> None:
        """
        Build a DistanceMatrix.

        Parameters
        ----------
        session : RecordingSession
            Containing RecordingSession.
        metadata : DistanceMatrixParameters
            Parameters used in calculating this instance of DistanceMatrix.
        load_path : Optional[Path], optional
            path of the saved data, by default None
        meta_path : Optional[Path], optional
            path of the saved meta data, by default None
        parsed_data : Optional[np.ndarray], optional
            The distance matrix itself, by default None
        """
        super().__init__(
            owner=owner,
            meta_data=meta_data,
            parsed_data=parsed_data,
            load_path=load_path,
            meta_path=meta_path)

        self.meta_data = meta_data

    def _derive_data(self) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Calculate the distance matrix on the data RecordingSession parent.       
        """
        raise NotImplementedError(
            "Currently MSE Modalities have to be "
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
        'DistanceMatrix [metric name] on [data modality class name]'.

        This overrides the default behaviour of Modality.name.
        """
        return DistanceMatrix.generate_name(self.meta_data)
