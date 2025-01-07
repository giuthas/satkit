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
SplineMetric and supporting classes.
"""

# Built in packages
import logging
from typing import Optional, Tuple

# Numpy and scipy
import numpy as np
from pydantic import PositiveInt

from satkit.data_structures import (
    FileInformation, Modality, ModalityData, ModalityMetaData, Recording)
from satkit.external_class_extensions import (
    enum_union, ListablePrintableEnum, ValueComparedEnumMeta)
from satkit.utility_functions import product_dict

_logger = logging.getLogger('satkit.spline_metric')


class SplineDiffsEnum(ListablePrintableEnum, metaclass=ValueComparedEnumMeta):
    """
    Spline metrics that use distance between corresponding points.
    """
    APBPD = 'apbpd'
    MPBPD = 'mpbpd'
    SPLINE_L1 = 'spline_l1'
    SPLINE_L2 = 'spline_l2'


class SplineNNDsEnum(ListablePrintableEnum, metaclass=ValueComparedEnumMeta):
    """
    Spline metrics that use nearest neighbour distance.
    """
    ANND = 'annd'
    MNND = 'mnnd'


class SplineShapesEnum(ListablePrintableEnum, metaclass=ValueComparedEnumMeta):
    """
    Spline metrics that characterise shape.
    """
    CURVATURE = 'curvature'
    FOURIER = 'fourier'
    MODIFIED_CURVATURE = 'modified_curvature'
    PROCRUSTES = 'procrustes'


SplineMetricEnum = enum_union(
    [SplineDiffsEnum, SplineNNDsEnum, SplineShapesEnum], "SplineMetricEnum")
"""
Enum of all valid spline metrics.

This is formed as a UnionEnum of the subtypes.
"""


class SplineMetricParameters(ModalityMetaData):
    """
    Parameters used in generating a SplineMetric modality.

    Parameters
    ----------
    metric : SplineMetricEnum
        A string specifying this Modality's metric. Defaults to the l1 norm.
    timestep : PositiveInt
        A  positive integer used as the timestep in calculating this Modality's
        data. Defaults to 1, which means comparison of consecutive frames.
    release_data_memory : bool
        Whether to assign None to `parent.data` after deriving this Modality
        from the data. Currently, has no effect as deriving SplineMetric at
        runtime is not yet supported.
    exclude_points : tuple[int, int]
        How many points to exclude from the (beginning, end) of the spline,
        by default, None.
    """
    parent_name: str
    metric: SplineMetricEnum = SplineDiffsEnum.MPBPD
    timestep: PositiveInt = 1
    release_data_memory: bool = False
    exclude_points: Optional[tuple[int, int]] = None


class SplineMetric(Modality):
    """
    Represent a SplineMetric as a Modality. 
    """

    @classmethod
    def generate_name(cls, params: SplineMetricParameters) -> str:
        """
        Generate a SplineMetric name to be used as its unique identifier.

        This static method **defines** what the names are. This implementation
        pattern (SplineMetric.name calls this and anywhere that needs to guess
        what a name would be calls this) is how all derived Modalities should
        work.

        Parameters
        ----------
        params : SplineMetricParameters
            The parameters of the SplineMetric instance. Note that this
            SplineMetricParameters instance does not need to be attached to a
            SplineMetric instance.

        Returns
        -------
        str
            Name of the SplineMetric instance.
        """
        name_string = cls.__name__ + " " + params.metric.value

        if params.timestep != 1 and params.metric not in SplineShapesEnum:
            name_string = name_string + " ts" + str(params.timestep)

        if params.parent_name:
            name_string = name_string + " on " + params.parent_name

        if params.is_downsampled:
            name_string += " downsampled by " + params.downsampling_ratio

        return name_string

    @staticmethod
    def get_names_and_meta(
        modality: Modality,
        metrics: list[str] = None,
        timesteps: list[int] = None,
        exclude_points: tuple[int, int] = None,
        release_data_memory: bool = False
    ) -> dict[str: SplineMetricParameters]:
        """
        Generate SplineMetric modality names and metadata.

        This method will generate the full cartesian product of the possible
        combinations. If only some of them are needed, make more than one call
        or weed the results afterwards.

        Parameters
        ----------
        modality : Modality
            parent modality that SplineMetric would be derived from
        metrics : List[str], optional
            list of metrics to be calculated, defaults to 'l2'.
        timesteps : List[int], optional
            list of timesteps to be used, defaults to 1.
        exclude_points : tuple[int, int]
            How many points to exclude from the (beginning, end) of the spline,
            by default, None.
        release_data_memory: bool
            Should parent Modality's data be assigned to None after calculations
            are complete, by default False.

        Returns
        -------
        dict[str: SplineMetricParameters]
            Dictionary where the names of the SplineMetric Modalities index the
            SplineMetricParameter objects.
        """
        parent_name = modality.__name__

        if not metrics:
            metrics = SplineDiffsEnum.MPBPD
        if not timesteps:
            timesteps = [1]

        param_dict = {
            'parent_name': [parent_name],
            'metric': metrics,
            'timestep': timesteps,
            'exclude_points': [exclude_points],
            'release_data_memory': [release_data_memory]}

        spline_metric_params = [SplineMetricParameters(**item)
                                for item in product_dict(**param_dict)]

        return {SplineMetric.generate_name(params): params
                for params in spline_metric_params}

    def __init__(self,
                 owner: Recording,
                 metadata: SplineMetricParameters,
                 file_info: FileInformation,
                 parsed_data: Optional[ModalityData] = None,
                 time_offset: Optional[float] = None) -> None:
        """
        Build a SplineMetric Modality.       

        Parameters
        ----------
        owner : Recording
            the containing Recording.
        metadata : SplineMetricParameters
            Parameters used in calculating this instance of SplineMetric.
        file_info : FileInformation
            _description_
        parsed_data : Optional[ModalityData], optional
            ModalityData object, by default None. Contains SplineMetric values,
            sampling rate,and either timevector and/or time_offset. Providing a
            timevector overrides any time_offset value given, but in absence of
            a timevector the time_offset will be applied on reading the data
            from file.
        time_offset : Optional[float], optional
            Time offset in seconds against the Recordings baseline. If not
            specified or 0, timeOffset will be copied from dataModality, by
            default None
        """
        # This allows the caller to be lazy.
        if not time_offset:
            if parsed_data:
                time_offset = parsed_data.timevector[0]

        super().__init__(
            owner=owner,
            metadata=metadata,
            file_info=file_info,
            parsed_data=parsed_data,
            time_offset=time_offset,
        )

    def _derive_data(self) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Calculate the SplineMetric on the data of the parent Modality.
        """
        message = ("Currently SplineMetric Modalities have to be "
                   "calculated at instantiation time. In: " + self.name)
        raise NotImplementedError(message)

    def get_meta(self) -> dict:
        # This conversion is done to keep nestedtext working.
        meta = self.metadata.model_dump()
        return meta

    @property
    def name(self) -> str:
        """
        Identity, metric, and parent data class.

        The name will be of the form
        'PD [metric name] on [data modality class name]'.

        This overrides the default behaviour of Modality.name.
        """
        return SplineMetric.generate_name(self.metadata)
