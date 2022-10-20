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

# Built in packages
import abc
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Union

# Numerical arrays and more
import numpy as np
# Praat textgrids
import textgrids

_datastructures_logger = logging.getLogger('satkit.data_structures')

class Recording():
    """
    A Recording contains 0-n synchronised Modalities.

    The recording also contains the non-modality 
    specific metadata (participant, speech content, etc) 
    as a dictionary, as well as the textgrid for the whole recording.

    In inheriting classes call self._read_textgrid() after calling
    super.__init__() (with correct arguments) and doing any updates
    to self.meta['textgrid'] that are necessary.
    """

    def __init__(self, excluded: bool=False, path: Optional[Union[str, Path]]=None, 
                basename: str="", textgrid_path: Union[str, Path]="", 
                time_of_recording: Optional[Union[datetime, str]]=None) -> None:
        """"""
        self.excluded = excluded

        if isinstance(path, Path):
            self.path = path
        elif isinstance(path, str):
            self.path = Path(path)
        else:
            self.path = None

        self.basename = basename

        if textgrid_path:
            self._textgrid_path = self.path.joinpath(textgrid_path)
        else:
            self._textgrid_path = self.path.joinpath(basename + ".TextGrid")
        self.textgrid = self._read_textgrid()

        if isinstance(time_of_recording, str):
            time_of_recording = datetime.strptime(time_of_recording, '%d/%m/%Y %H:%M:%S')
        elif time_of_recording is None:
            time_of_recording = datetime.strptime('01/01/1970 00:00:00', '%d/%m/%Y %H:%M:%S')
        self.time_of_recording = time_of_recording

        self.modalities = {}
        self.annotations = {}

    def _read_textgrid(self) -> textgrids.TextGrid:
        """
        Read the textgrid specified in self.meta.

        If file does not exist or reading fails, recovery is attempted 
        by logging an error and creating an empty textgrid for this 
        recording.
        """
        textgrid = None
        if self._textgrid_path.is_file():
            try:
                textgrid = textgrids.TextGrid(self._textgrid_path)
                _datastructures_logger.info("Read textgrid in %s.", 
                                            self._textgrid_path)
            except Exception as e:
                _datastructures_logger.critical("Could not read textgrid in %s.",
                                                self._textgrid_path)
                _datastructures_logger.critical("Failed with: %s.", str(e))
                _datastructures_logger.critical("Creating an empty textgrid "
                                           + "instead.")
                textgrid = textgrids.TextGrid()
        else:
            notice = 'Note: ' + str(self._textgrid_path) + " did not exist."
            _datastructures_logger.warning(notice)
            _datastructures_logger.warning("Creating an empty textgrid "
                                      + "instead.")
            textgrid = textgrids.TextGrid()
        return textgrid

    def exclude(self) -> None:
        """
        Set self.excluded to True with a method.

        This method exists to facilitate list comprehensions being used
        for excluding recordings e.g. 
        [recording.exclude() for recording in recordings if in some_list].
        """
        self.excluded = True

    def write_textgrid(self, filepath: Path=None) -> None:
        """
        Save this recording's textgrid to file.

        Keyword argument:
        filepath -- string specifying the path and name of the 
            file to be written. If filepath is not specified, this 
            method will try to overwrite the textgrid speficied in 
            self.meta.

            If filepath is specified, subsequent calls to this 
            function will write into the new path rather than 
            the original one.
        """
        try:
            if filepath:
                self.textgridpath = filepath
                self.textgrid.write(filepath)
            else:
                self.textgrid.write(self.textgridpath)
        except Exception as e:
            _datastructures_logger.critical("Could not write textgrid to "
                                        + str(self.textgridpath) + ".")
            _datastructures_logger.critical("TextGrid save failed with error: " 
                                        + str(e))

    # should the modalities dict be accessed as a property?
    def add_modality(self, modality: 'Modality', replace: bool=False) -> None:
        """
        This method adds a new Modality object to the Recording.

        Replacing a modality has to be specified otherwise if a
        Modality with the same name already exists in this Recording
        and the replace argument is not True, an Error is raised. 

        Arguments:
        modality -- object of type Modality to be added to 
            this Recording.

        Keyword arguments:
        replace -- a boolean indicating if an existing Modality should
            be replaced.
        """
        name = modality.name
        if name in self.modalities.keys() and not replace:
            raise AttributeError(
                "A modality named " + name +
                " already exists and replace flag was False.")
        elif replace:
            self.modalities[name] = modality
            _datastructures_logger.debug("Replaced modality " + name + ".")
        else:
            self.modalities[name] = modality
            _datastructures_logger.debug("Added new modality " + name + ".")


class Modality(abc.ABC):
    """
    Abstract superclass for all data Modality classes.
    """

    def __init__(self, name: str, recording: Recording, preload: bool, 
                path: Optional[Union[str, Path]]=None, parent: Optional['Modality']=None, 
                timeOffset: float=0) -> None:
        """
        Modality constructor.

        Positional arguments:
        name -- string specifying the name of this Modality. The name 
            should be unique in the containing Recording.
        recording -- the containing Recording.
        preload -- a boolean indicating if this instance reads the 
            data from disc on construction or only when needed.

        Keyword arguments:
        parent -- the Modality this one was derived from. None means this 
            is an underived data Modality.
        timeOffset (s) -- the offset against the baseline audio track.
        """
        # Identity and position in the recording hierarchy
        self.name = name

        # use self.recording.meta[key] to set recording metadata
        self.meta = {}

        if isinstance(path, Path):
            self.path = path
        elif isinstance(path, str):
            self.path = Path(path)
        else:
            self.path = None

        self.recording = recording
        self.parent = parent

        # This is a property which when set to True will also set parent.excluded to True.
        self.excluded = False

        self.preload = preload
        # TODO: see if time_offset is being set/used correctly here. 
        # it might need to be passed to get_data
        self._time_offset = timeOffset

        # data
        if self.preload:
            self._data, self._timevector, self._sampling_rate = self._get_data()
            self._time_offset = self._timevector[0]
        else:
            self._data = None
            self._timevector = None
            self._sampling_rate = None

    def _get_data(self) -> Tuple[np.ndarray, np.ndarray, float]:
        # TODO: Provide a way to force the data to be derived. 
        # this would be used when parent modality has updated in some way
        if self.path:
            return self._load_data()
        elif self.parent:
            return self._derive_data()
        else:
            # TODO: change this into a suitable raise Error/Exception clause instead.
            print("Asked to get data but have no path and no parent Modality.\n" + 
                "Don't know how to solve this.")

    def _load_data(self) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Load data from file -- to be overridden by inheriting classes.

        This method should be implemented by subclasses to provide a unified 
        way of handling preloading and on-the-fly loading of data.

        This method is intended to rely on self.meta to know what to read.
        """
        raise NotImplementedError(
            "This method should be overridden by inheriting classes.")

    def _derive_data(self) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Derive data from another modality -- to be overridden by inheriting classes.

        This method should be implemented by subclasses to provide a unified 
        way of handling preloading and on-the-fly loading of data.

        This method is intended to rely on self.meta to know what to read.
        """
        raise NotImplementedError(
            "This method should be overridden by inheriting classes.")

    def _set_data(self, data: np.ndarray, timevector: np.ndarray, sampling_rate: float):
        """Method used to set data from either _get_data, _load_data, and _derive_data."""
        self._data = data
        self._timevector = timevector
        self._sampling_rate = sampling_rate

    @property
    def excluded(self) -> None:
        """
        Boolen property for excluding this Modality from processing.

        Setting this to True will result in the whole Recording being 
        excluded by setting self.parent.excluded = True.
        """
        # TODO: decide if this actually needs to exist and if so,
        # should the above doc string actaully be true?
        return self._excluded

    @excluded.setter
    def excluded(self, excluded):
        self._excluded = excluded

        if excluded:
            self.parent.excluded = excluded

    @property
    def is_derived_modality(self) -> bool:
        if self.parent:
            return True
        else:
            return False

    @property
    def data(self) -> np.ndarray:
        """
        Abstract property: a NumPy array. 

        The data refers to the actual data this modality represents
        and for DerivedModality it is the result of running the 
        modality's algorithm on the original data.

        The dimensions of the array are in the 
        order of [time, others]

        If this modality is not preloaded, accessing this property will
        cause data to be loaded on the fly _and_ saved in memory. To 
        release the memory, assign None to this Modality's data.
        """
        if self._data is None:
            _datastructures_logger.debug(
                "In Modality data getter. self._data was None.")
            self._set_data(self._get_data())
        return self._data

    @data.setter
    def data(self, data: np.ndarray) -> None:
        """
        Data setter method.

        Arguments:
        data - either None or a numpy.ndarray with same dtype, size, 
            and shape as self.data.

        Assigning anything but None or a numpy ndarray with matching
        dtype, size, and shape will raise a ValueError.

        If shape of the data were to change then also shape of the timevector should
        potentially change. Unlikely that we'd try to deal that in any other way but
        to create a new Modality or even Recording.
        """
        if self.data is not None and data is not None:
            if (data.dtype == self._data.dtype and data.size == self._data.size and 
                data.shape == self._data.shape):
                self._data = data
            else:
                raise ValueError(
                    "Trying to write over raw ultrasound data with " +
                    "a numpy array that has non-matching dtype, size, or shape.\n" +
                    " data.shape = " + str(data.shape) + "\n" +
                    " self.data.shape = " + str(self._data.shape) + ".")
        else:
            self._data = data

    @property
    def sampling_rate(self) -> float:
        if not self._sampling_rate:
            self._set_data(self._get_data())
        return self._sampling_rate


    @property
    def time_offset(self):
        """
        The time offset of this modality.

        Assigning a value to this property is implemented so 
        that self._timevector[0] stays equal to self._timeOffset. 

        If shape of the timevector were to change then also shape of the data should
        change. Unlikely that we'd try to deal that in any other way but
        to create a new Modality or even Recording.
        """
        if not self._time_offset:
            self._set_data(self._get_data())
        return self._time_offset

    @time_offset.setter
    def time_offset(self, timeOffset):
        self._time_offset = timeOffset
        if self.timevector:
            self._timevector = (self.timevector +
                                (timeOffset - self.timevector[0]))

    @property
    def timevector(self):
        """
        The timevector corresponding to self.data as a NumPy array. 

        If the data has not been previously loaded, accessing this 
        property will cause data to be loaded on the fly _and_ saved 
        in memory. To release the memory, assign None to this 
        Modality's data. If the data has been previously 
        loaded and after that released, the timevector still persists and  
        accessing it does not trigger a new loading operation.

        Assigning a value to this property is implemented so 
        that self._timevector[0] stays equal to self._timeOffset. 
        """
        if self._timevector is None:
            self._set_data(self._get_data())
        return self._timevector

    @timevector.setter
    def timevector(self, timevector):
        if self._timevector is None:
            raise ValueError(
                "Trying to overwrite the time vector when it has not yet been initialised."
            )
        elif timevector is None:
            raise NotImplementedError(
                "Trying to set timevector to None.\n" + 
                "Freeing timevector memory is currently not implemented."
            )
        else:
            if (timevector.dtype == self._timevector.dtype and 
                timevector.size == self._timevector.size and 
                timevector.shape == self._timevector.shape):
                self._timevector = timevector
                self.time_offset = timevector[0]
            else:
                raise ValueError(
                    "Trying to write over raw ultrasound data with " +
                    "a numpy array that has non-matching dtype, size, or shape.\n" +
                    " timevector.shape = " + str(timevector.shape) + "\n" +
                    " self.timevector.shape = " + str(self._timevector.shape) + ".")


