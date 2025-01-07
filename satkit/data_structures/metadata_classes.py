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
"""Meta data classes for use by core data structures."""

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
from pydantic import PositiveInt

from satkit.configuration import PointAnnotationParams
from satkit.configuration import ExclusionList, SplineConfig
from satkit.constants import AnnotationType, Datasource
from satkit.external_class_extensions import SatkitBaseModel
from satkit.utility_functions.types import is_sequence_form

_datastructures_logger = logging.getLogger('satkit.data_structures')


@dataclass
class FileInformation:
    """
    File and Path information for SATKIT DataObjects. 

    recorded_data_file: str | None = None
        Name of the file containing the raw recorded data.
    recorded_meta_file: str | None = None
        Name of the file containing the meta data of the recording.
    recorded_path : Path | None = None
        Path to the recorded data of this DataObject - if there is original
        recorded data associated with this instance/type, defaults to None
    satkit_data_file : str | None
        Name of the SATKIT data file, if it exists, defaults to None.
    satkit_meta_file : str | None
        Name of the SATKIT meta file, if it exists, defaults to None.
    satkit_path : Path | None
        Path to the saved SATKIT data, if it exists, defaults to None.
        Generally this will mostly be equivalent to the recorded_path, except
        for the root level DataAggregator which contains the paths to the
        SATKIT and recorded data root directories.
    """
    recorded_data_file: str | None = None
    recorded_meta_file: str | None = None
    recorded_path: Path | None = None
    satkit_data_file: str | None = None
    satkit_meta_file: str | None = None
    satkit_path: Path | None = None


@dataclass
class ModalityData:
    """
    Data passed from Modality generation into Modality.

    None of the fields are optional. This class represents already loaded data.

    Axes order for the data field is [time, coordinate axes and datatypes,
    data points] and further structure. For example stereo audio data would be
    [time, channels] or just [time] for mono audio. For a more complex example,
    splines from AAA have [time, x-y-confidence, spline points] or [time,
    r-phi-confidence, spline points] for data in polar coordinates.
    """
    data: np.ndarray
    sampling_rate: float
    timevector: np.ndarray


class ModalityMetaData(SatkitBaseModel):
    """
    Baseclass of Modalities' metadata classes.
    """
    parent_name: str = None
    is_downsampled: bool = False
    downsampling_ratio: PositiveInt | str | None = None
    timestep_matched_downsampling: bool = True


@dataclass
class PointAnnotations:
    """
    Time point annotations for a Modality.

    For each modality there should be only one of these for each kind of
    annotation type. 

    annotation_type : AnnotationType
        unique identifier for the annotation type
    indeces : np.ndarray
        indeces of the annotation points. `modality_data.data[indeces[i]]` and
        `modality_data.timevector[indeces[i]]` correspond to the annotation at
        `i`.
    times : np.ndarray 
        timestamps of the annotation points
    generating_parameters : dict 
        the function call arguments and other parameters used in generating
        these annotations.
    properties : dict
        a dictionary containing arrays of each of the annotation properties
        expected for this annotation type.
    """
    annotation_type: AnnotationType
    indeces: np.ndarray
    times: np.ndarray
    generating_parameters: PointAnnotationParams
    properties: dict

    def add_annotation(
            self, index: int, time: float, properties: dict) -> None:
        """
        This method has not been implemented yet.

        Index and time should be mutually exclusive.

        Parameters
        ----------
        index : int
            index at which the annotation is to be added
        time : float
            time at which the annotation is to be added
        properties : dict
            the annotation properties that will be added to the arrays in this
            PointAnnotations' properties dict.

        Raises
        ------
        NotImplementedError
            This method has not been implemented yet.
        """
        raise NotImplementedError(
            "Adding annotations to "
            "PointAnnotations hasn't been implemented yet.")

    def apply_lower_time_limit(self, time_min: float) -> None:
        """
        Apply a lower time limit to the annotations.

        This removes the annotation points before the given time limit.

        Parameters
        ----------
        time_min : float
            The time limit.
        """
        selected = np.nonzero(self.times >= time_min)
        self.indeces = self.indeces[selected]
        self.times = self.times[selected]
        limit = selected[0]

        for key in self.properties:
            if is_sequence_form(self.properties[key]):
                self.properties[key] = self.properties[key][limit:]
            elif isinstance(self.properties[key], np.ndarray):
                self.properties[key] = self.properties[key][selected]

    def apply_upper_time_limit(self, time_max: float) -> None:
        """
        Apply an upper time limit to the annotations.

        This removes the annotation points after the given time limit.

        Parameters
        ----------
        time_max : float
            The time limit.
        """
        selected = np.nonzero(self.times <= time_max)
        self.indeces = self.indeces[selected]
        self.times = self.times[selected]
        limit = selected[-1]

        for key in self.properties:
            if is_sequence_form(self.properties[key]):
                self.properties[key] = self.properties[key][:limit]
            elif isinstance(self.properties[key], np.ndarray):
                self.properties[key] = self.properties[key][selected]


class RecordingMetaData(SatkitBaseModel):
    """Basic metadata that any Recording should reasonably have."""
    prompt: str
    time_of_recording: datetime
    participant_id: str
    # TODO: These should be taken care of by FileInformation.
    basename: str
    path: Path


class SessionConfig(SatkitBaseModel):
    """
    Description of a Session for import into SATKIT.
    """
    data_source: Datasource
    exclusion_list: ExclusionList | None = None
    spline_config: SplineConfig | None = None


class StatisticMetaData(SatkitBaseModel):
    """
    Baseclass of Statistics' metadata classes.
    """
    parent_name: str | None = None
