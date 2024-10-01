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
"""Base classes of the core datastructures."""

# Built in packages
import abc
import logging
from pathlib import Path
from typing import Optional


# Numerical arrays and more
import numpy as np

from satkit.errors import OverwriteError
from satkit.helpers import EmptyStrAsNoneBaseModel

from .meta_data_classes import StatisticMetaData

_datastructures_logger = logging.getLogger('satkit.data_structures')


class DataObject(abc.ABC):
    """
    Abstract base class for SATKIT data objects.

    Almost no class should directly inherit from this class. Exceptions are
    DataAggregator and DataContainer. The latter is the abstract baseclass for
    Modality and Statistic and the former for all data base classes: Recording,
    Session, DataSet and any others that contain either DataContainers and/or
    DataAggregators.
    """

    def __init__(self,
                 owner,
                 meta_data: EmptyStrAsNoneBaseModel,
                 load_path: Optional[Path] = None,
                 meta_path: Optional[Path] = None,
                 ) -> None:
        # The super().__init__() call below is needed to make sure that
        # inheriting classes which also inherit from UserDict and UserList are
        # initialised properly.
        super().__init__()

        self.owner = owner
        self._meta_data = meta_data
        self.load_path = load_path
        self._meta_path = meta_path

    def __getstate__(self) -> dict:
        """
        Return this DataContainer's pickle compatible state.

        To achieve pickle compatibility, subclasses should take care to delete
        any cyclical references, like is done with self.owner here.

        NOTE! This also requires owner to be reset after unpickling by the
        owners, because the unpickled class can not know who owns it.

        Returns
        -------
        dict
            The state without cyclical references.
        """
        state = self.__dict__.copy()
        del state['owner']

    @property
    def meta_data(self) -> EmptyStrAsNoneBaseModel:
        """
        Meta data of this DataObject.

        This will be of appropriate type for the subclasses and has been hidden
        behind a property to make it possible to change the internal
        representation without breaking the API.

        Returns
        -------
        EmptyStrAsNoneBaseModel
            The meta data as a Pydantic model.
        """
        return self._meta_data

    @abc.abstractmethod
    @property
    def name(self) -> str:
        """
        Name of this instance.

        In most cases name is supposed to be implemented with the following
        idiom:
        ```python
        return NAME_OF_THIS_CLASS.generate_name(self.meta_data)
        ```
        For example, for PD:
        ```python
        return PD.generate_name(self.meta_data)
        ```

        Returns
        -------
        str
            Name of this instance.
        """

    @property
    def is_fully_initialised(self) -> bool:
        """
        Check if this DataContainer has been fully initialised.

        This property will be false, if any required fields of the
        DataContainer are None.

        Returns
        -------
        bool
            True if this DataContainer is fully initialised.
        """
        if self.owner:
            return True
        return False

    def get_meta(self) -> dict:
        """
        Get meta data as a dict.

        This is a helper method for saving as nested text. Allows for rewriting
        any fields that need a simpler representation. 

        Subclasses should override this method if any of their fields require
        special handling such as derived Enums needing to be converted to plain
        text etc. 

        Returns
        -------
        dict
            The meta data in a dict.
        """
        return self.meta_data.model_dump()


class DataAggregator(DataObject):
    """
    Abstract baseclass for Recording, Session, and DataSet. 

    This class collects behaviors that are shared by the data base classes i.e.
    classes which collect DataContainers and/or DataAggregators.
    """

    def __init__(self,
                 owner: 'DataAggregator',
                 name: str,
                 meta_data: EmptyStrAsNoneBaseModel,
                 load_path: Optional[Path] = None,
                 meta_path: Optional[Path] = None,
                 statistics: Optional[dict[str, 'Statistic']] = None
                 ) -> None:
        super().__init__(
            owner=owner, meta_data=meta_data,
            load_path=load_path, meta_path=meta_path)

        self.name = name
        self.statistics = {}
        if statistics:
            self.statistics.update(statistics)

    def add_statistic(
            self, statistic: 'Statistic', replace: bool = False) -> None:
        """
        Add a Statistic to this Session.

        Parameters
        ----------
        statistic : Statistic
            Statistic to be added.
        replace : bool, optional
            Should we replace any existing Statistic by the same name, by
            default False

        Raises
        ------
        OverwriteError
            In case replace was False and there exists already a Statistic with
            the same name in this Session.
        """
        self.statistics[statistic.name] = statistic
        name = statistic.name

        if name in self.statistics and not replace:
            raise OverwriteError(
                "A modality named " + name +
                " already exists and replace flag was False.")

        if replace:
            self.statistics[name] = statistic
            _datastructures_logger.debug("Replaced statistic %s.", name)
        else:
            self.statistics[name] = statistic
            _datastructures_logger.debug("Added new statistic %s.", name)


class DataContainer(DataObject):
    """
    Abstract baseclass for Modality and Statistic. 

    This class collects behaviors shared by the classes that contain data:
    Modalities contain time varying data and Statistics contain time
    independent data.
    """
    @classmethod
    @abc.abstractmethod
    def generate_name(cls, params: EmptyStrAsNoneBaseModel) -> str:
        """Abstract version of generating a RecordingMetric name."""

    def __init__(self,
                 owner: DataAggregator,
                 meta_data: EmptyStrAsNoneBaseModel,
                 load_path: Optional[Path] = None,
                 meta_path: Optional[Path] = None,
                 ) -> None:
        super().__init__(
            owner=owner, meta_data=meta_data,
            load_path=load_path, meta_path=meta_path)

    @property
    def name(self) -> str:
        """
        Name of this instance.

        In most cases name is supposed to be overridden with the following
        idiom:
        ```python
        return NAME_OF_THIS_CLASS.generate_name(self.meta_data)
        ```
        For example, for PD:
        ```python
        return PD.generate_name(self.meta_data)
        ```

        Returns
        -------
        str
            Name of this instance.
        """
        return self.__class__.generate_name(self._meta_data)


class Statistic(DataContainer):
    """
    Abstract baseclass for statistics generated from members of a container. 

    Specifically Statistics are time independent data while Modalities are time
    dependent data.
    """
    data: np.ndarray

    @classmethod
    @abc.abstractmethod
    def generate_name(cls, params: StatisticMetaData) -> str:
        """Abstract version of generating a Statistic name."""

    def __init__(
            self,
            owner,
            meta_data: EmptyStrAsNoneBaseModel,
            parsed_data: Optional[np.ndarray] = None,
            load_path: Optional[Path] = None,
            meta_path: Optional[Path] = None,
    ) -> None:
        """
        Build a Statistic.       

        Parameters
        ----------
        owner : 
            The owner of this Statistic. Usually this will be the object whose
            contents this Statistic was calculated on.
        metadata : EmptyStrAsNoneBaseModel
            Parameters used in calculating this Statistic.
        parsed_data : Optional[np.ndarray], optional
            the actual statistic, by default None
        load_path : Optional[Path], optional
            path of the saved data, by default None
        meta_path : Optional[Path], optional
            path of the saved meta data, by default None
        """
        super().__init__(owner=owner, meta_data=meta_data,
                         load_path=load_path, meta_path=meta_path)
        self.data = parsed_data
