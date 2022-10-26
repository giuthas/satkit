
import logging
import sys
from contextlib import closing
from pathlib import Path
from typing import Optional, Tuple, Union

# Numpy
import numpy as np
# wav file handling
import scipy.io.wavfile as sio_wavfile
# scikit-video for io and processing of video data.
import skvideo.io

# local modules
import satkit.audio_processing as satkit_audio
from data_structures import Modality, Recording
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
    mains_frequency = None
    filter = {}


    def __init__(self, recording: Recording, preload: bool,   
                path: Optional[Union[str, Path]]=None, parent: Optional['Modality']=None, 
                time_offset: float=0, mains_frequency: float=50) -> None:
        """
        Create a MonoAudio track.

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
        self.mains_frequency = mains_frequency
        super().__init__(recording=recording, path=path, 
                parent=parent, preload=preload, time_offset=time_offset)

        # # If we do not have a filename, there is not much to init.
        # if self.path:
        #     if preload:
        #         self._get_data()
        #     else:
        #         self._data = None
        #         self._timevector = None


    def _load_data(self):
        """
        Helper for loading data, detecting beep and generating the timevector.

        Setting self.isPreloaded = True results in a call to this method.
        """
        (wav_fs, wav_frames) = sio_wavfile.read(self.path)
        # self.sampling_rate = wav_fs
        # self._data = wav_frames

        # setup the high-pass filter for removing the mains frequency (and anything below it)
        # from the recorded sound.
        if not MonoAudio.filter:
            MonoAudio.mains_frequency = self.mains_frequency
            MonoAudio.filter = satkit_audio.high_pass(
                wav_fs, self.mains_frequency)

        beep, has_speech = satkit_audio.detect_beep_and_speech(
            wav_frames, wav_fs, MonoAudio.filter['b'],
            MonoAudio.filter['a'],
            self.path)

        # before v1.0: this is a bad name for the beep: 1) this is an AAA thing,
        # 2) the recording might not be UTI
        self.stimulus_onset = beep
        self.has_speech = has_speech

        timevector = np.linspace(0, len(wav_frames),
                                       len(wav_frames),
                                       endpoint=False)
        timevector = timevector/wav_fs + self._time_offset
        return wav_frames, timevector, wav_fs

    @property
    def data(self):
        return super().data

    # TODO: before 1.0 this should already be handled by Modality.
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

    def __init__(self, recording: Recording, preload: bool, 
                path: Optional[Union[str, Path]]=None, parent: Optional['Modality']=None, 
                time_offset: float=0, meta: Optional[dict]=None) -> None:
        """
        Create a RawUltrasound Modality.

        New keyword argument:
        meta -- a dict with (at least) the keys listed in 
            RawUltrasound.requiredMetaKeys. Extra keys will be ignored. 
            Default is None.
        """
        # Explicitly copy meta data fields to ensure that we have what we expected to get.
        if meta != None:
            try:
                wanted_meta = {key: meta[key]
                               for key in RawUltrasound.requiredMetaKeys}
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

            print(wanted_meta)
            self.meta = wanted_meta

        super().__init__(recording=recording, path=path, 
                parent=parent, preload=preload, time_offset=time_offset)

        # if preload:
        #     self._get_data()
        # else:
        #     self._data = None

        # State variables for fast retrieval of previously tagged ultrasound frames.
        self._stored_index = None
        self._stored_image = None

    def _load_data(self) -> Tuple[np.ndarray, np.ndarray, float]:
        with closing(open(self.path, 'rb')) as ult_file:
            ult_data = ult_file.read()
            ultra = np.fromstring(ult_data, dtype=np.uint8)
            ultra = ultra.astype("float32")

            self.meta['no_frames'] = int(
                len(ultra) /
                (self.meta['NumVectors'] * self.meta['PixPerVector']))
            data = ultra.reshape(
                (self.meta['no_frames'],
                 self.meta['NumVectors'],
                 self.meta['PixPerVector']))

            ultra_time = np.linspace(
                0, self.meta['no_frames'],
                num=self.meta['no_frames'],
                endpoint=False)
            timevector = ultra_time / \
                self.meta['FramesPerSec'] + self.time_offset
            # this should be added for PD and similar time vectors: + .5/self.meta['framesPerSec']
            # while at the same time dropping a suitable number of timestamps

        return (data, timevector, self.meta['FramesPerSec'])

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

    # Before 1.0: Figure out how to move this to MatrixData
    # and how to extend it when necessary. Practically whole of
    # __init__ is shared with RawUltrasound and so should be in MatrixData
    # instead of here. Only _getData and data.setter's message change.
    requiredMetaKeys = [
        'FramesPerSec'
    ]

    def __init__(self, recording: Recording, preload: bool, 
                path: Optional[Union[str, Path]]=None, parent: Optional['Modality']=None, 
                time_offset: float=0, meta=None) -> None: 
        """
        New keyword arguments:
        meta -- a dict with (at least) the keys listed in 
            RawUltrasound.requiredMetaKeys. Extra keys will be ignored. 
            Default is None.
        """
        super().__init__(recording=recording, path=path, 
                parent=parent, preload=preload, time_offset=time_offset)

        self.meta['filename'] = path

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

        if path and preload:
            self._getData()
        else:
            self._data = None

    def _getData(self):
        # possibly try importing as grey scale
        # videodata = skvideo.io.vread(self.meta['filename'])
        self._data = skvideo.io.vread(self.meta['filename'])

        # TODO: Before 1.0: 'NumVectors' and 'PixPerVector' are bad names here.
        # They come from the AAA ultrasound side of things and should be
        # replaced, but haven't been yet as I'm in a hurry to get PD
        # running on videos.
        self.meta['no_frames'] = self.data.shape[0]
        self.meta['NumVectors'] = self.data.shape[1]
        self.meta['PixPerVector'] = self.data.shape[2]
        video_time = np.linspace(
            0, self.meta['no_frames'],
            num=self.meta['no_frames'],
            endpoint=False)
        self.timevector = video_time / \
            self.meta['FramesPerSec'] + self.timeOffset
        # this should be added for PD and similar time vectors:
        # + .5/self.meta['framesPerSec']
        # while at the same time dropping a suitable number
        # (most likely = timestep) of timestamps

    @property
    def data(self):
        return super().data

    # Handled by Modality already. May need to call super to make it work though.
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
