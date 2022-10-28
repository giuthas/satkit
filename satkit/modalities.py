
import logging
import sys
from copy import deepcopy
from pathlib import Path
from typing import Optional, Tuple, Union

# Numpy
import numpy as np
# scikit-video for io and processing of video data.
import skvideo.io

# local modules
from data_structures import Modality, ModalityData, Recording
from satkit.formats import read_avi, read_ult, read_wav
from satkit.interpolate_raw_uti import to_fan_2d

_modalities_logger = logging.getLogger('satkit.modalities')

class MonoAudio(Modality):
    """
    A mono audio track. 

    Audio data is assumed to be small enough for the
    whole session to fit in working memory and therefore
    this Modality preloads data at construction time.
    """

    # Mains electricity frequency and filter coefficients for removing
    # it from audio with a highpass filter.
    # mains_frequency = None
    # filter = {}


    def __init__(self, 
                recording: Recording, 
                data_path: Optional[Path]=None,
                load_path: Optional[Path]=None,
                parent: Optional[Modality]=None,
                parsed_data: Optional[ModalityData]=None,
                go_signal: Optional[float] = None, 
                has_speech: Optional[bool] = None) -> None:
        """
        Create a MonoAudio track.

        Positional arguments:
        recording -- the containing Recording.        

        Keyword arguments:
        data_path -- path of the wav file
        load_path -- path of the saved data - both wav and metadata
        parent -- the Modality this one was derived from. None means this 
            is an underived data Modality.
        parsed_data -- ModalityData object containing waveform, sampling rate,
            and either timevector and/or time_offset. Providing a timevector 
            overrides any time_offset value given, but in absence of a 
            timevector the time_offset will be applied on reading the data 
            from file. 
        go_signal -- time of the go_signal in seconds from start of recording.
        has_speech -- True if the heuristic algorithm thinks there is speech 
            audio in the sample.
        """
        super().__init__(
                recording, 
                data_path,
                load_path,
                parent,
                parsed_data)

        self.go_signal = go_signal
        self.has_speech = has_speech

    def _read_data(self):
        """
        Call io functions to read wav data, and detecting go-signal & speech.
        """
        parsed_data, go_signal, has_speech = read_wav(self.data_path)
        self.go_signal = go_signal
        self.has_speech = has_speech
        return parsed_data

    # TODO: uncomment and implement when implementing the save features.
    # def _load_data(self):
        # """
        # Call io functions to load wav data, and any wav related meta saved with it.

        # The wav data itself is just the original file, but along that a metadata
        # save file will be read as well to recover any go-signal or speech detection
        # results.
        # """

    # TODO: before 1.0 this should already be handled by Modality.
    # @property
    # def data(self):
    #     return super().data

    # # before v1.0: check that the data is actually valid, also call the beep detect etc. routines on it.
    # @data.setter
    # def data(self, data):
    #     """
    #     The audio data of this Modality.

    #     Assigning any other value except None is not implemented yet.
    #     """
    #     if data is not None:
    #         raise NotImplementedError(
    #             'Writing over mono audio data has not been implemented yet.')
    #     self._data = data


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

    def __init__(self, 
                recording: Recording, 
                data_path: Optional[Path]=None,
                load_path: Optional[Path]=None,
                parent: Optional[Modality]=None,
                parsed_data: Optional[ModalityData]=None,
                meta: Optional[dict]=None 
                ) -> None:
        """
        Create a RawUltrasound Modality.

        Positional arguments:
        recording -- the containing Recording.        

        Keyword arguments:
        data_path -- path of the ultrasound file
        load_path -- path of the saved data - both ultrasound and metadata
        parent -- the Modality this one was derived from. None means this 
            is an underived data Modality.
        parsed_data -- ModalityData object containing raw ultrasound, sampling rate,
            and either timevector and/or time_offset. Providing a timevector 
            overrides any time_offset value given, but in absence of a 
            timevector the time_offset will be applied on reading the data 
            from file. 
        meta -- a dict with (at least) the keys listed in 
            RawUltrasound.requiredMetaKeys. Extra keys will be ignored. 
            Default is None.
        """
        # Explicitly copy meta data fields to ensure that we have what we expected to get.
        if meta != None:
            try:
                wanted_meta = {key: meta[key]
                               for key in RawUltrasound.requiredMetaKeys}
                self.meta = deepcopy(wanted_meta)
            except KeyError:
                # Missing metadata for one recording may be ok and this could be handled with just
                # a call to _recording_logger.critical and setting self.excluded = True
                notFound = set(RawUltrasound.requiredMetaKeys) - set(meta)
                _modalities_logger.critical(
                    "Part of metadata missing when processing %s.",
                    self.meta['filename'])
                _modalities_logger.critical(
                    "Could not find %s.", str(notFound))
                _modalities_logger.critical('Exiting.')
                sys.exit()

        # Initialise super only after ensuring meta is correct,
        # because latter may already end the run.
        super().__init__(
                recording, 
                data_path,
                load_path,
                parent,
                parsed_data)

        # TODO: these are related to GUI and should really be in a decorator class and not here.
        # State variables for fast retrieval of previously tagged ultrasound frames.
        self._stored_index = None
        self._stored_image = None

    def _read_data(self) -> Tuple[np.ndarray, np.ndarray, float]:
        return read_ult(self.data_path, self.meta, self._time_offset)

    @property
    def data(self) -> np.ndarray:
        return super().data

    @data.setter
    def data(self, data) -> None:
        super()._data_setter(data)

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


class Video(Modality):
    """
    Ultrasound Recording with raw (probe return) data.    
    """

    requiredMetaKeys = [
        'FramesPerSec'
    ]

    def __init__(self, 
                recording: Recording, 
                data_path: Optional[Path]=None,
                load_path: Optional[Path]=None,
                parent: Optional[Modality]=None,
                parsed_data: Optional[ModalityData]=None,
                meta: Optional[dict]=None 
                ) -> None:
        """
        Create a RawUltrasound Modality.

        Positional arguments:
        recording -- the containing Recording.        

        Keyword arguments:
        data_path -- path of the ultrasound file
        load_path -- path of the saved data - both ultrasound and metadata
        parent -- the Modality this one was derived from. None means this 
            is an underived data Modality.
        parsed_data -- ModalityData object containing raw ultrasound, sampling rate,
            and either timevector and/or time_offset. Providing a timevector 
            overrides any time_offset value given, but in absence of a 
            timevector the time_offset will be applied on reading the data 
            from file. 
        meta -- a dict with (at least) the keys listed in 
            RawUltrasound.requiredMetaKeys. Extra keys will be ignored. 
            Default is None.
        """
        # Explicitly copy meta data fields to ensure that we have what we expected to get.
        if meta != None:
            try:
                wanted_meta = {key: meta[key]
                               for key in Video.requiredMetaKeys}
            except KeyError:
                # Missing metadata for one recording may be ok and this could be handled with just
                # a call to _recording_logger.critical and setting self.excluded = True
                notFound = set(Video.requiredMetaKeys) - set(meta)
                _modalities_logger.critical(
                    "Part of metadata missing when processing "
                    + self.meta['filename'] + ". ")
                _modalities_logger.critical(
                    "Could not find " + str(notFound) + ".")
                _modalities_logger.critical('Exiting.')
                sys.exit()

            self.meta.update(wanted_meta)

        super().__init__(
                recording, 
                data_path,
                load_path,
                parent,
                parsed_data)

    def _getData(self):
        return read_avi(self.data_path, self.meta, self._time_offset)


    # TODO: Handled by Modality already. May need to call super to make it work though.
    # @property
    # def data(self):
    #     return super().data

    # # before v1.0: check that the data is actually valid, also call the beep 
    # # detect etc. routines on it.
    # @data.setter
    # def data(self, data):
    #     """
    #     Data setter method.

    #     Assigning anything but None is not implemented yet.
    #     """
    #     if data is not None:
    #         raise NotImplementedError(
    #             'Writing over video data has not been implemented yet.')
    #     else:
    #         self._data = data
