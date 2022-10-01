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
from contextlib import closing
import logging
from pathlib import Path
import sys
from typing import Tuple

# Numerical arrays and more
import numpy as np

# wav file handling
import scipy.io.wavfile as sio_wavfile

# Praat textgrids
import textgrids

# local modules
import satkit.audio_processing as satkit_audio
from satkit.interpolate_raw_uti import to_fan_2d

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

    def __init__(self, excluded: bool=False, path: Path=None, basename: str="",
                textgrid_name: str="") -> None:
        """"""
        self.excluded = excluded
        self.path = path
        self.basename = basename

        if textgrid_name:
            self.textgridpath = self.path.joinpath(textgrid_name)
        else:
            self._textgrid_path = self.path.joinpath(basename + ".TextGrid")
        self.textgrid = self._read_textgrid()

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
        if self.textgrid.isfile():
            try:
                textgrid = textgrids.TextGrid(self.textgrid_path)
                _datastructures_logger.info("Read textgrid in "
                                       + self.textgrid_path + ".")
            except Exception as e:
                _datastructures_logger.critical("Could not read textgrid in "
                                           + self.textgrid_path + ".")
                _datastructures_logger.critical("Failed with: " + str(e))
                _datastructures_logger.critical("Creating an empty textgrid "
                                           + "instead.")
                textgrid = textgrids.TextGrid()
        else:
            notice = 'Note: ' + self.textgrid_path + " did not exist."
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
                parent: 'Modality'=None, timeOffset: float=0) -> None:
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
        self.recording = recording
        self.parent = parent

        self.preload = preload
        # TODO: see if time_offset is being set/used correctly here. 
        # it might need to be passed to get_data
        self._time_offset = timeOffset
        self._sampling_rate = None

        # data
        if self.preload:
            self._data, self._timevector, self.sampling_rate = self._load_data()
            self._time_offset = self._timevector[0]
        else:
            self._data = None
            self._timevector = None
            self.sampling_rate = None

        # use self.recording.meta[key] to set recording metadata
        self.meta = {}

        # This is a property which when set to True will also set parent.excluded to True.
        self.excluded = False

        self.preload = preload
        self._time_offset = timeOffset
        self._sampling_rate = None

    @abc.abstractmethod
    def _load_data(self) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Load data from file -- abstract method to be overridden.

        This method should be implemented by subclasses to provide a unified 
        way of handling preloading and on-the-fly loading of data.

        This method is intended to rely on self.meta to know what to read.
        """
        raise NotImplementedError(
            "This is an abstract method that " +
            "should be overridden by inheriting classes.")

    def _set_data(self, data: np.ndarray, timevector: np.ndarray, sampling_rate: float):
        self.data = data
        self.timevector = timevector
        self.sampling_rate = sampling_rate

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
            self._set_data(self._load_data())
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
            self._set_data(self._load_data())
        return self._sampling_rate


    @property
    def time_offset(self):
        """
        The time offset of this modality.

        Assigning a value to this property is implemented so 
        that self._timevector[0] stays equal to self._timeOffset. 
        """
        if not self._time_offset:
            self._set_data(self._load_data())
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
            self._set_data(self._load_data())
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
                    

class MonoAudio(Modality):
    """
    A mono audio track. 

    Audio data is assumed to be small enough to fit in working memory.
    """

    # Mains electricity frequency and filter coefficients for removing
    # it from audio with a highpass filter.
    mainsFrequency = None
    filter = {}

    def __init__(self, name='mono audio', parent=None, preload=True,
                 timeOffset=0, filename=None, mainsFrequency=50):
        """
        Create a MonoAudio track.

        preload defaults to True because audio data is assumed to be small 
            enough to fit in working memory.
        filename should be either None or the name of a wav-file.
        mainsFrequency (Hz) is the mains frequency of the place of recording. 
            When detecting the recording onset beep, the audio is high pass 
            filtered with this frequency as the high end of the stop band.
            The frequency should be checked locally, if not clear from here
            https://en.wikipedia.org/wiki/Mains_electricity_by_country .
        """

        super().__init__(name, parent, preload, timeOffset)

        self.meta['filename'] = filename
        self.meta['mainsFrequency'] = mainsFrequency

        # If we do not have a filename, there is not much to init.
        if filename:
            if preload:
                self._load_data()
            else:
                self._data = None
                self._timevector = None

    def _load_data(self):
        """
        Helper for loading data, detecting beep and generating the timevector.

        Setting self.isPreloaded = True results in a call to this method.
        """
        (wav_fs, wav_frames) = sio_wavfile.read(self.meta['filename'])
        self.meta['wav_fs'] = wav_fs
        self._data = wav_frames

        # setup the high-pass filter for removing the mains frequency (and anything below it)
        # from the recorded sound.
        if MonoAudio.mainsFrequency != self.meta['mainsFrequency']:
            MonoAudio.mainsFrequency = self.meta['mainsFrequency']
            MonoAudio.filter = satkit_audio.high_pass(
                wav_fs, self.meta['mainsFrequency'])

        beep, has_speech = satkit_audio.detect_beep_and_speech(
            wav_frames, wav_fs, MonoAudio.filter['b'],
            MonoAudio.filter['a'],
            self.meta['filename'])

        # before v1.0: this is a bad name for the beep: 1) this is an AAA thing,
        # 2) the recording might not be UTI
        self.meta['stimulus_onset'] = beep
        self.meta['has_speech'] = has_speech

        self._timevector = np.linspace(0, len(wav_frames),
                                       len(wav_frames),
                                       endpoint=False)
        self._timevector = self._timevector/wav_fs + self.time_offset

    @property
    def data(self):
        return super().data

    # before v1.0: check that the data is actually valid, also call the beep detect etc. routines on it.
    @data.setter
    def data(self, data):
        """
        The audio data of this Modality.

        Assigning any other value except None is not implemented yet.
        """
        if data is not None:
            raise NotImplementedError(
                'Writing over mono audio data has not been implemented yet.')
        self._data = data


class RawUltrasound(Modality):
    """
    Ultrasound Recording with raw (probe return) data.
    """

    requiredMetaKeys = [
        'meta_file',
        'Angle',
        'FramesPerSec',
        'NumVectors',
        'PixPerVector',
        'PixelsPerMm',
        'ZeroOffset'
    ]

    def __init__(
            self, name="raw ultrasound", parent=None, preload=False,
            timeOffset=0, filename=None, meta=None):
        """

        New keyword arguments:
        filename -- the name of a .ult file containing raw ultrasound 
            data. Default is None.
        meta -- a dict with (at least) the keys listed in 
            RawUltrasound.requiredMetaKeys. Extra keys will be ignored. 
            Default is None.
        """
        super().__init__(name=name, parent=parent, preload=preload, timeOffset=timeOffset)

        self.meta['filename'] = filename

        # Explicitly copy meta data fields to ensure that we have what we expected to get.
        if meta != None:
            try:
                wanted_meta = {key: meta[key]
                               for key in RawUltrasound.requiredMetaKeys}
            except KeyError:
                # Missing metadata for one recording may be ok and this could be handled with just
                # a call to _recording_logger.critical and setting self.excluded = True
                notFound = set(RawUltrasound.requiredMetaKeys) - set(meta)
                _datastructures_logger.critical(
                    "Part of metadata missing when processing " + self.meta
                    ['filename'] + ". ")
                _datastructures_logger.critical(
                    "Could not find " + str(notFound) + ".")
                _datastructures_logger.critical('Exiting.')
                sys.exit()

            self.meta.update(wanted_meta)

        if filename and preload:
            self._load_data()
        else:
            self._data = None

        # State variables for fast retrieval of previously tagged ultrasound frames.
        self._stored_index = None
        self._stored_image = None

    def _load_data(self):
        with closing(open(self.meta['filename'], 'rb')) as ult_file:
            ult_data = ult_file.read()
            ultra = np.fromstring(ult_data, dtype=np.uint8)
            ultra = ultra.astype("float32")

            self.meta['no_frames'] = int(
                len(ultra) /
                (self.meta['NumVectors'] * self.meta['PixPerVector']))
            self._data = ultra.reshape(
                (self.meta['no_frames'],
                 self.meta['NumVectors'],
                 self.meta['PixPerVector']))

            ultra_time = np.linspace(
                0, self.meta['no_frames'],
                num=self.meta['no_frames'],
                endpoint=False)
            self.timevector = ultra_time / \
                self.meta['FramesPerSec'] + self.time_offset
            # this should be added for PD and similar time vectors: + .5/self.meta['framesPerSec']
            # while at the same time dropping a suitable number of timestamps

    @property
    def data(self):
        return super().data

    @data.setter
    def data(self, data):
        """
        Data setter method.

        Assigning anything but None or a numpy ndarray with matching
        dtype, size, and shape has not been implemented yet and will
        raise a NotImplementedError.
        """
        if self.data is not None:
            if (isinstance(data, np.ndarray) and data.dtype == self._data.dtype and 
                data.size == self._data.size and data.shape == self._data.shape):
                self._data = data
            else:
                raise NotImplementedError(
                    "Writing over raw ultrasound data with data that is not a numpy ndarray or " +
                    "a numpy array that has non-matching dtype, size, or shape has not been " +
                    "implemented yet.")
        else:
            self._data = data

    def interpolated_image(self, index):
        """
        Return an interpolated version of the ultrasound frame at index.
        
        A new interpolated image is calculated, if necessary. To avoid large memory overheads
        only the current frame's interpolated version maybe stored in memory.

        Arguments:
        index - the index of the ultrasound frame to be returned
        """
        if self._stored_index and self._stored_index == index:
            return self._stored_image
        else:
            self._stored_index = index
            #frame = scipy_medfilt(self.data[index, :, :].copy(), [1,15])
            frame = self.data[index, :, :].copy()
            frame = np.transpose(frame)
            frame = np.flip(frame, 0)
            self._stored_image = to_fan_2d(
                frame,
                angle=self.meta['Angle'],
                zero_offset=self.meta['ZeroOffset'],
                pix_per_mm=self.meta['PixelsPerMm'],
                num_vectors=self.meta['NumVectors'])
            return self._stored_image
