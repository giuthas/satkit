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
DistanceMatrix Statistic and its Parameter class.
"""

import logging

import numpy as np
from pydantic import PositiveInt

from satkit.configuration import ExclusionList
from satkit.data_structures import (
    FileInformation, Modality, Session, Statistic, StatisticMetaData
)
from satkit.utility_functions import product_dict

_logger = logging.getLogger('satkit.mse')


class DistanceMatrixParameters(StatisticMetaData):
    """
    Parameters used in generating the parent DistanceMatrix.

    Parameters
    ----------
    parent_name: str
        Name of the Modality or Statistic this instance of DistanceMatrix was
        calculated on.
    metric : str
        A string specifying this DistanceMatrix's metric. Defaults to mean
        squared error.
    release_data_memory : bool
        Whether to assign None to `parent.data` after deriving this Modality
        from the data. Currently, has no effect as deriving a DistanceMatrix at
        runtime is not yet supported.
    slice_max_step: PositiveInt | None
        Simulate rotating the probe by slicing incrementally so that the sector
        is always the same size. This parameter determines how many steps of
        size one to take, by default None.
    slice_step_to: PositiveInt | None
        Instead of incrementally stepping with same size sectors, generate a
        pair of maximally distant sectors for each step size ranging from one to
        `slice_step_to`, by default None.
    sort: bool
        Sort the rows and columns of the matrix in order corresponding to the
        alphabetical order of the prompts or according to `sort_criteria` if it
        is defined. By default, False.
    sort_criteria: list[str] | None
        List of substrings to sort the rows and columns by, by default None. The
        result will consist of blocks where in first block `sort_criteria[0] in
        prompt` is True, and so on. Final block will consist of any Recordings
        left after the list has been exhausted.
    """
    parent_name: str
    metric: str = 'mean_squared_error'
    release_data_memory: bool = True
    slice_max_step: PositiveInt | None = None
    slice_step_to: PositiveInt | None = None
    sort: bool = False
    sort_criteria: list[str] | None = None
    sorted_indeces: list[int] | None = None
    sorted_prompts: list[str] | None = None
    sorted_filenames: list[str] | None = None
    exclusion_list: ExclusionList | None = None


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
        pattern (DistanceMatrix.name calls this and anywhere that needs to
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
        name_string = name_string + " on " + params.parent_name

        if params.slice_max_step:
            name_string = (
                    name_string + f" slice_max_step {params.slice_max_step}")
        elif params.slice_step_to:
            name_string = (
                    name_string + f" slice_step_to {params.slice_step_to}")

        if params.sort:
            name_string = (
                    name_string + f" sort {params.sort}")
            if params.sort_criteria:
                name_string = (
                        name_string + f" sort_criteria specified")

        return name_string

    @staticmethod
    def get_names_and_meta(
            parent: Modality | Statistic,
            metric: list[str] | None = None,
            release_data_memory: bool = True,
            slice_max_step: int | None = None,
            slice_step_to: int | None = None,
            sort: bool = False,
            sort_criteria: list[str] | None = None,
            exclusion_list: ExclusionList | None = None
    ) -> dict[str: DistanceMatrixParameters]:
        """
        Generate DistanceMatrix names and metadata.

        This method will generate the full cartesian product of the possible
        combinations. If only some of them are needed, make more than one call
        or weed the results afterwards.

        Parameters
        ----------
        parent : Modality | Statistic
            parent Modality or Statistic that DistanceMatrix would be derived
            from.
        metric : list[str] | None, optional
            list of the names of metrics to use in name generation, by default
            None which will result in 'mean_squared_error' being used.
        release_data_memory: bool
            Should parent Modality's data be assigned to None after calculations
            are complete, by default True.
        slice_max_step: PositiveInt | None
            Simulate rotating the probe by slicing incrementally so that the
            sector is always the same size. This parameter determines how many
            steps of size one to take, by default None.
        slice_step_to: PositiveInt | None
            Instead of incrementally stepping with same size sectors, generate a
            pair of maximally distant sectors for each step size ranging from
            one to `slice_step_to`, by default None.
        sort: bool
            Sort the rows and columns of the matrix in order corresponding to
            the alphabetical order of the prompts or according to
            `sort_criteria` if it is defined. By default, False.
        sort_criteria: list[str] | None
            List of substrings to sort the rows and columns by, by default None.
            The result will consist of blocks where in first block
            `sort_criteria[0] in prompt` is True, and so on. Final block will
            consist of any Recordings left after the list has been exhausted.
        exclusion_list : ExclusionList | None
            The ExclusionList to apply when generating the DistanceMatrices. By
            default, None.
        
        Returns
        -------
        dict[str: DistanceMatrixParameters]
            Dictionary where the names of the DistanceMatrices index the 
            DistanceMatrixParameter objects.
        """
        if isinstance(parent, str):
            parent_name = parent
        elif isinstance(parent, Statistic) or isinstance(parent, Modality):
            parent_name = parent.__class__.__name__
        else:
            parent_name = parent.__name__

        if not metric:
            metric = ['mean_squared_error']

        param_dict = {
            'parent_name': [parent_name],
            'metric': metric,
            'release_data_memory': [release_data_memory],
            'slice_max_step': [slice_max_step],
            'slice_step_to': [slice_step_to],
            'sort': [sort],
            'sort_criteria': [sort_criteria],
            'exclusion_list': [exclusion_list],
        }

        distance_matrix_params = [DistanceMatrixParameters(**item)
                                  for item in product_dict(**param_dict)]

        return {DistanceMatrix.generate_name(params): params
                for params in distance_matrix_params}

    def __init__(
            self,
            owner: Session,
            metadata: DistanceMatrixParameters,
            file_info: FileInformation,
            parsed_data: np.ndarray | None = None,
    ) -> None:
        """
        Build a DistanceMatrix.

        Parameters
        ----------
        owner : Session
            Containing Session.
        metadata : DistanceMatrixParameters
            Parameters used in calculating this instance of DistanceMatrix.
        file_info : FileInformation
            FileInformation -- if any -- for this DistanceMatrix.
        parsed_data : Optional[np.ndarray], optional
            The distance matrix itself, by default None
        """
        super().__init__(
            owner=owner,
            metadata=metadata,
            file_info=file_info,
            parsed_data=parsed_data, )

    def _derive_data(self) -> tuple[np.ndarray, np.ndarray, float]:
        """
        Calculate the distance matrix on the data Session parent.       
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
        return self.metadata.model_dump()

    @property
    def name(self) -> str:
        """
        Identity, metric, and parent data class.

        The name will be of the form
        'DistanceMatrix [metric name] on [data modality class name]'.

        This overrides the default behaviour of Modality.name.
        """
        return DistanceMatrix.generate_name(self.metadata)
