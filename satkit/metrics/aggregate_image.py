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
AggregateImage Statistic and its Parameter class.
"""

import logging

import numpy as np

from satkit.data_structures import (
    FileInformation, Modality, Recording, Session, Statistic, StatisticMetaData
)
from satkit.utility_functions import product_dict

_logger = logging.getLogger('satkit.aggregate_image')


class AggregateImageParameters(StatisticMetaData):
    """
    Parameters used in generating the parent AggregateImage modality.

    Parameters
    ----------
    parent_name: str
        Name of the Modality this instance of AggregateImage was calculated on.
    metric : str, optional
        Metric used in aggregation. By default, 'mean'.
    interpolated : bool, optional
        Should this AggregateImage be calculated on interpolated images.
        Defaults to False for calculating AggregateImage on raw data. This one
        really can only be used on 2D ultrasound data.
    release_data_memory : bool, optional
        Whether to assign None to `parent.data` after deriving this Metric from
        the data. Currently, has no effect as deriving AggregateImage at runtime
        is not yet supported.
    """
    parent_name: str
    metric: str = 'mean'
    interpolated: bool = False
    release_data_memory: bool = True


class AggregateImage(Statistic):
    """
    Represent an AggregateImage as a Statistic.

    Currently only allowed metric is mean, but median, mode and others could be
    added.
    """

    @classmethod
    def generate_name(cls, params: AggregateImageParameters) -> str:
        """
        Generate a name to be used as this  AggregateImage's unique identifier.

        This static method **defines** what the names are. This implementation
        pattern (AggregateImage.name calls this and anywhere that needs to guess
        what a name would be calls this) is how all derived Modalities should
        work.

        Parameters
        ----------
        params : AggregateImageParameters
            The parameters of the AggregateImage instance. Note that this
            AggregateImageParameters instance does not need to be attached to a
            AggregateImage instance.

        Returns
        -------
        str
            Name of the AverageImage instance.
        """
        name_string = cls.__name__ + " " + params.metric

        if params.interpolated and params.parent_name:
            name_string = ("Interpolated " + name_string + " on " +
                           params.parent_name)
        elif params.parent_name:
            name_string = name_string + " on " + params.parent_name

        return name_string

    @staticmethod
    def get_names_and_meta(
            modality: Modality | str,
            metric: list[str] | None = None,
            mean_image_on_interpolated_data: bool = False,
            release_data_memory: bool = True
    ) -> dict[str: AggregateImageParameters]:
        """
        Generate AggregateImage modality names and metadata.

        This method will generate the full cartesian product of the possible
        combinations. If only some of them are needed, make more than one call
        or weed the results afterwards.

        Parameters
        ----------
        modality : Modality
            parent modality that AggregateImage would be derived from
        metric : list[str] | None, optional
            list of the names of metrics to use in name generation, by default
            None which will result in 'mean' being used.
        mean_image_on_interpolated_data : bool, optional
            indicates if interpolated data should be used for instead of
            RawUltrasound, by default False
        release_data_memory: bool, optional
            Should parent Modality's data be assigned to None after
            calculations are complete, by default True.

        Returns
        -------
        dict[str: AggregateImageParameters]
            Dictionary where the names of the AggregateImage Statistics index
            the AggregateImageParameter objects.
        """
        if isinstance(modality, str):
            parent_name = modality
        else:
            parent_name = modality.__name__

        if not metric:
            metric = ['mean']

        param_dict = {
            'parent_name': [parent_name],
            'metric': metric,
            'interpolated': [mean_image_on_interpolated_data],
            'release_data_memory': [release_data_memory]}

        aggregate_image_params = [AggregateImageParameters(**item)
                                  for item in product_dict(**param_dict)]

        return {AggregateImage.generate_name(params): params
                for params in aggregate_image_params}

    def __init__(
            self,
            owner: Recording | Session,
            metadata: AggregateImageParameters,
            file_info: FileInformation,
            parsed_data: np.ndarray | None = None,
    ) -> None:
        """
        Build a AggregateImage Statistic.       

        Parameters
        ----------
        owner : Recording | Session
            the Recording or Session that this AggregateImage was calculated on.
        metadata : AggregateImageParameters
            Parameters used in calculating this instance of AggregateImage.
        file_info : FileInformation
            FileInformation -- if any -- for this AggregateImage.
        parsed_data : np.ndarray | None, optional
            the actual aggregate image, by default None
        """
        super().__init__(
            owner=owner,
            metadata=metadata,
            file_info=file_info,
            parsed_data=parsed_data,)

    def _derive_data(self) -> tuple[np.ndarray, np.ndarray, float]:
        """
        Calculate AggregateImage on the data of the parent Modality.
        """
        raise NotImplementedError(
            "Currently AggregateImage Modalities have to be "
            "calculated at instantiation time.")

    @property
    def name(self) -> str:
        """
        Identity, metric, and parent data class.

        The name will be of the form
        'AggregateImage [metric name] on [data modality class name]'.
        """
        return AggregateImage.generate_name(self.metadata)
