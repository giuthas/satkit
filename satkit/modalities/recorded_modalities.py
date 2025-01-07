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
Recorded data modalities
"""

import logging
import sys
from copy import deepcopy

import numpy as np

# local modules
from satkit.data_structures import (
    FileInformation, Modality, ModalityData, ModalityMetaData, Recording
)
from satkit.import_formats import (
    read_3d_ultrasound_dicom, read_avi, read_ult, read_wav,
    read_wav_and_detect_beep
)
from satkit.interpolate_raw_uti import to_fan, to_fan_2d
from .recorded_metadata_classes import RawUltrasoundMeta

_logger = logging.getLogger('satkit.modalities')


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

    @classmethod
    def generate_name(cls, params: ModalityMetaData) -> str:
        return cls.__name__

    def __init__(
            self,
            owner: Recording,
            file_info: FileInformation,
            parsed_data: ModalityData | None = None,
            time_offset: float | None = None,
            detect_beep: bool = False,
            go_signal: float | None = None,
            has_speech: bool | None = None
    ) -> None:
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
            owner=owner,
            file_info=file_info,
            parsed_data=parsed_data,
            time_offset=time_offset)

        self.detect_beep = detect_beep
        self.go_signal = go_signal
        self.has_speech = has_speech

    def _read_data(self) -> ModalityData:
        """
        Read wav data, and possibly detect go-signal & speech.
        """
        if self.detect_beep:
            parsed_data, go_signal, has_speech = read_wav_and_detect_beep(
                self.recorded_data_path)
            self.go_signal = go_signal
            self.has_speech = has_speech
            return parsed_data
        return read_wav(self.recorded_data_path)

    # TODO: uncomment and implement when implementing the save features.
    # def _load_data(self):
    # """
    # Call io functions to load wav data, and any wav related meta
    # saved with it.

    # The wav data itself is just the original file, but along that a
    # metadata save file will be read as well to recover any go-signal or
    # speech detection results. """

    def get_meta(self) -> dict:
        return {'sampling_rate': self.sampling_rate}


class RawUltrasound(Modality):
    """
    Ultrasound Recording with raw (probe return) data.
    """

    @classmethod
    def generate_name(cls, params: ModalityMetaData) -> str:
        return cls.__name__

    def __init__(self,
                 owner: Recording,
                 file_info: FileInformation,
                 parsed_data: ModalityData | None = None,
                 time_offset: float | None = None,
                 metadata: RawUltrasoundMeta | None = None
                 ) -> None:
        """
        Create a RawUltrasound Modality.

        Positional arguments:
        recording -- the containing Recording.

        Keyword arguments:
        data_path -- path of the ultrasound file
        load_path -- path of the saved data - both ultrasound and metadata
        parsed_data -- ModalityData object containing raw ultrasound,
            sampling rate, and either timevector and/or time_offset.
            Providing a timevector overrides any time_offset value given,
            but in absence of a timevector the time_offset will be applied
            on reading the data from file.
        meta -- a dict with (at least) the keys listed in
            RawUltrasound.requiredMetaKeys. Extra keys will be ignored.
            Default is None.
        """
        super().__init__(
            owner=owner,
            file_info=file_info,
            parsed_data=parsed_data,
            time_offset=time_offset,
            metadata=metadata
        )

        # TODO: these are related to GUI and should really be in a decorator
        # class and not here. State variables for fast retrieval of previously
        # tagged ultrasound frames.
        self._stored_index = None
        self._stored_image = None
        self.video_has_been_stored = False
        self.stored_video = None

    def _read_data(self) -> ModalityData:
        return read_ult(
            self.recorded_data_path, self.metadata, self._time_offset)

    def get_meta(self) -> dict:
        return self.meta

    @property
    def data(self) -> np.ndarray:
        return super().data

    @data.setter
    def data(self, data) -> None:
        super()._data_setter(data)

    def raw_image(self, index: int) -> np.ndarray:
        """
        Return the raw ultrasound frame at index.

        Parameters
        ----------
        index : int
            Index to look up.

        Returns
        -------
        np.ndarray
            The frame.
        """
        return self.data[index, :, :].copy()

    def interpolated_image(self, index):
        """
        Return an interpolated version of the ultrasound frame at index.

        A new interpolated image is calculated, if necessary. To avoid large
        memory overheads only the current frame's interpolated version maybe
        stored in memory.

        Arguments: index - the index of the ultrasound frame to be returned
        """
        _logger.debug(
            "Getting interpolated image from ultrasound. index=%d", index)
        if self.video_has_been_stored:
            _logger.debug(
                "Returning interpolated image from stored video.")
            half_way = int(self.stored_video.shape[0] / 2)
            return self.stored_video[half_way, :, :].copy()
        elif self._stored_index and self._stored_index == index:
            _logger.debug(
                "Returning previously stored interpolated image.")
            return self._stored_image
        else:
            _logger.debug(
                "Calculating interpolated image from scratch.")
            self._stored_index = index
            # frame = scipy_medfilt(self.data[index, :, :].copy(), [1,15])
            frame = self.data[index, :, :].copy()
            # half = int(frame.shape[0]/2)
            # frame[:half,:] = 0
            self._stored_image = to_fan_2d(
                frame,
                **self.interpolation_params,
            )
            return self._stored_image

    def interpolated_frames(self) -> np.ndarray:
        """
        Return an interpolated version of the ultrasound frame at index.

        A new interpolated image is calculated, if necessary. To avoid large
        memory overheads only the current frame's interpolated version maybe
        stored in memory.

        Arguments: index - the index of the ultrasound frame to be returned
        """
        data = self.data.copy()

        self.video_has_been_stored = True
        video = to_fan(
            data,
            show_progress=True,
            **self.interpolation_params,
        )
        self.stored_video = video.copy()
        # half = int(video.shape[1]/2)
        # self.stored_video[:,half:,:] = 0
        return video

    @property
    def interpolation_params(self) -> dict:
        return {
            'angle': self.metadata.angle,
            'zero_offset': self.metadata.zero_offset,
            'pixels_per_mm': self.metadata.pixels_per_mm,
            'num_vectors': self.metadata.num_vectors,
        }


class Video(Modality):
    """
    Video recording.
    """

    requiredMetaKeys = [
        'FramesPerSec'
    ]

    @classmethod
    def generate_name(cls, params: ModalityMetaData) -> str:
        return cls.__name__

    def __init__(self,
                 owner: Recording,
                 file_info: FileInformation,
                 parsed_data: ModalityData | None = None,
                 time_offset: float | None = None,
                 meta: dict | None = None
                 ) -> None:
        """
        Create a Video Modality.

        Positional arguments:
        recording -- the containing Recording.

        Keyword arguments:
        data_path -- path of the ultrasound file
        load_path -- path of the saved data - both ultrasound and metadata
        parent -- the Modality this one was derived from. Should be None
            which means this is an underived data Modality.
        parsed_data -- ModalityData object containing raw ultrasound,
            sampling rate, and either timevector and/or time_offset. Providing
            a timevector overrides any time_offset value given, but in absence
            of a timevector the time_offset will be applied on reading the
            data from file.
        meta -- a dict with (at least) the keys listed in
            Video.requiredMetaKeys. Extra keys will be ignored.
            Default is None.
        """
        # Explicitly copy meta data fields to ensure that we have what we
        # expected to get.
        if meta is not None:
            try:
                wanted_meta = {key: meta[key]
                               for key in Video.requiredMetaKeys}
                self.meta = deepcopy(wanted_meta)
            except KeyError:
                # Missing metadata for one recording may be ok and this could
                # be handled with just a call to _recording_logger.critical and
                # setting self.excluded = True
                not_found = set(Video.requiredMetaKeys) - set(meta)
                _logger.critical(
                    "Part of metadata missing when processing %s. ",
                    meta['filename'])
                _logger.critical(
                    "Could not find %s.", str(not_found))
                _logger.critical('Exiting.')
                sys.exit()

        super().__init__(
            owner=owner,
            file_info=file_info,
            parsed_data=parsed_data,
            time_offset=time_offset)

    def _read_data(self) -> ModalityData:
        return read_avi(
            self.recorded_data_path, self.meta, self._time_offset)

    def get_meta(self) -> dict:
        return {'sampling_rate': self.sampling_rate}


class ThreeD_Ultrasound(Modality):
    """
    Ultrasound Recording with interpolated 3D/4D data.
    """

    # TODO: this should be handled by a meta data class
    requiredMetaKeys = [
        'meta_file',
        'Angle',
        'FramesPerSec',
        'NumVectors',
        'PixPerVector',
        'PixelsPerMm',
        'ZeroOffset'
    ]

    @classmethod
    def generate_name(cls, params: ModalityMetaData) -> str:
        return cls.__name__

    def __init__(self,
                 owner: Recording,
                 file_info: FileInformation,
                 parsed_data: ModalityData | None = None,
                 time_offset: float | None = None,
                 meta: dict | None = None
                 ) -> None:
        """
        Create a RawUltrasound Modality.

        Positional arguments:
        recording -- the containing Recording.

        Keyword arguments:
        data_path -- path of the ultrasound file
        load_path -- path of the saved data - both ultrasound and metadata
        parsed_data -- ModalityData object containing raw ultrasound,
            sampling rate, and either timevector and/or time_offset.
            Providing a timevector overrides any time_offset value given,
            but in absence of a timevector the time_offset will be applied
            on reading the data from file.
        meta -- a dict with (at least) the keys listed in
            RawUltrasound.requiredMetaKeys. Extra keys will be ignored.
            Default is None.
        """
        # Explicitly copy meta data fields to ensure that we have what we
        # expected to get.
        if meta is not None:
            try:
                wanted_meta = {key: meta[key]
                               for key in RawUltrasound.requiredMetaKeys}
                self.meta = deepcopy(wanted_meta)
            except KeyError:
                # Missing metadata for one recording may be ok and this could
                # be handled with just a call to _recording_logger.critical and
                # setting self.excluded = True
                not_found = set(RawUltrasound.requiredMetaKeys) - set(meta)
                _logger.critical(
                    "Part of metadata missing when processing %s.",
                    meta['filename'])
                _logger.critical(
                    "Could not find %s.", str(not_found))
                _logger.critical('Exiting.')
                sys.exit()

        # Initialise super only after ensuring meta is correct,
        # because latter may already end the run.
        super().__init__(
            owner=owner,
            file_info=file_info,
            parsed_data=parsed_data,
            time_offset=time_offset)

        # TODO: these are related to GUI and should really be in a decorator
        # class and not here. State variables for fast retrieval of previously
        # tagged ultrasound frames.
        self._stored_index = None
        self._stored_image = None

    def _read_data(self) -> ModalityData:
        return read_3d_ultrasound_dicom(
            self.recorded_data_path,
            self.meta,
            self._time_offset)

    @property
    def data(self) -> np.ndarray:
        return super().data

    @data.setter
    def data(self, data) -> None:
        super()._data_setter(data)

    def get_meta(self) -> dict:
        return self.meta
