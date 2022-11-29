
# Built in packages
import logging
import sys
import warnings
from contextlib import closing
from copy import deepcopy
from datetime import datetime
from pathlib import PureWindowsPath
from typing import Tuple

# Numpy and scipy
import numpy as np
#from numpy.matlib import repmat
import scipy.io
from satkit.data_import.add_AAA_video import Video
# Local packages
from satkit.data_structures import Modality, MonoAudio, Recording

_3D4D_ultra_logger = logging.getLogger('satkit.ThreeD_ultrasound')

def read_3D_meta_from_mat_file(mat_file):
    """
    Read a RASL .mat file and return relevant contents as a dict.

    Positional argument:
    mat_file -- either a pathlib Path object representing the .mat 
        file or a string of the same.

    Returns -- an array of dicts that contain the following fields:
        'trial_number': number of the recording within this session,
        'prompt': prompt displayed to the participant,
        'date_and_time': a datetime object of the time recording 
            started, and
        'dat_filename': string representing the name of the .dat 
            sound file.
    """
    mat = scipy.io.loadmat(str(mat_file), squeeze_me=True)
    meta = []
    for element in mat['officialNotes']:
        # Apparently squeeze_me=True is a bit too strident and
        # somehow looses the shape of the most interesting level
        # in the loadmat call. Not using it is not a good idea
        # though so we do this:
        element = element.item()
        if len(element) > 5:
            # We try this two ways, because at least once filename
            # and date fields were in reversed order inside the
            # .mat file.
            try:
                date_and_time = datetime.strptime(
                    element[4], "%d-%b-%Y %H:%M:%S")
                file_path = element[5]
            except ValueError:
                date_and_time = datetime.strptime(
                    element[5], "%d-%b-%Y %H:%M:%S")
                file_path = element[4]

            meta_token = {
                'trial_number': element[0],
                'prompt': element[1],
                'date_and_time': date_and_time,
                'dat_filename': PureWindowsPath(file_path).name
            }
            meta.append(meta_token)
    return meta

def generateMeta(rows):
    """
    Parse a RASL .mat file's rows and return relevant contents as a dict.

    Positional argument:
    mat_file -- either a pathlib Path object representing the .mat
        file or a string of the same.

    Returns -- an array of dicts that contain the following fields:
        'trial_number': number of the recording within this session,
        'prompt': prompt displayed to the participant,
        'date_and_time': a datetime object of the time recording
            started, and
        'dat_filename': string representing the name of the .dat
            sound file.
    """
    meta = []
    for row in rows:
        date_and_time = datetime.strptime(
            row['US File Name'], "%Y%m%d%H%M%S")

        meta_token = {
            'trial_number': row['number_portion'],
            'prompt': row['Stimulus'],
            'date_and_time': date_and_time,
            'dat_filename': row['sound_filename'],
            'sound_filename': row['sound_filename']
        }
        meta.append(meta_token)
    return meta


class ThreeD_Ultrasound(Modality):
    """
    Ultrasound Recording with raw 3D/4D (probe return) data.    
    """

    def __init__(
            self, name="lip video", parent=None, preload=False,
            timeOffset=0, filename=None, meta=None):
        """
        New keyword arguments:
        filename -- the name of a .ult file containing raw ultrasound 
            data. Default is None.
        meta -- a dict with (at least) the keys listed in 
            RawUltrasound.requiredMetaKeys. Extra keys will be ignored. 
            Default is None.
        """
        super().__init__(name=name, parent=parent, preload=preload,
                         time_offset=timeOffset)

        self.meta['filename'] = filename

        if filename and preload:
            self._getData()
        else:
            self._data = None

    ### TODO: there's a initial version in formats/read_ultra_dicom
    def _get_data(self) -> Tuple[np.ndarray, np.ndarray, float]:
        return super()._get_data()

    @property
    def data(self):
        return super().data

    # before v1.0: check that the data is actually valid, also call the beep detect etc. routines on it.
    @data.setter
    def data(self, data):
        """
        Data setter method.

        Assigning anything but None is not implemented yet.
        """
        if data is not None:
            raise NotImplementedError(
                'Writing over video data has not been implemented yet.')
        else:
            self._data = data


class ThreeD_UltrasoundRecording(Recording):
    """
    3D/4D Ultrasound recording.
    """

    # This is for future use cases where meta comes from outside the
    # class itself.
    requiredMetaKeys = [
        'trial_number',
        'prompt',
        'date_and_time',
        'dat_filename'
    ]


    def __init__(self, paths=None, basename="", sound_name="",
                 requireVideo=False):
        super().__init__(path=paths['root_dir'], basename=basename)

        if basename == None:
            _3D4D_ultra_logger.critical(
                "Critical error: File basename is None.")
        elif basename == "":
            _3D4D_ultra_logger.critical(
                "Critical error: File basename is empty.")

        _3D4D_ultra_logger.debug(
            "Initialising a new 3D ultrasound recording with filename " +
            basename + ".")

        self._paths = paths
        self._paths['wav_dir'] = paths['root_dir'] / 'WAV'
        self._paths['avi_dir'] = paths['root_dir'] / 'AVI'

        # Candidates for filenames. Existence tested below.
        ult_wav_file = self._paths['wav_dir'].joinpath(sound_name + ".wav")
        textgrid = self._paths['wav_dir'].joinpath(sound_name + ".TextGrid")
        ult_file = self._paths['dicom_dir'].joinpath(basename)
        video_file = self._paths['avi_dir'].joinpath(basename)
        video_file = video_file.with_suffix(".avi")

        # Before 1.0: change the stored format to be a pathlib Path rather than
        # string.
        # check if assumed files exist, and arrange to skip them
        # if any do not
        if ult_wav_file.is_file():
            self.meta['ult_wav_file'] = str(ult_wav_file)
            self.meta['ult_wav_exists'] = True
        else:
            notice = 'Note: ' + str(ult_wav_file) + " does not exist."
            _3D4D_ultra_logger.warning(notice)
            self.meta['ult_wav_exists'] = False
            self.excluded = True

        if textgrid.is_file():
            self.meta['textgrid'] = str(textgrid)
            self.meta['textgrid_exists'] = True
            # Before 1.0: this is called here and in super().__init__()
            # only one call should actually be done.
            self._read_textgrid()
        else:
            notice = 'Note: ' + str(textgrid) + " does not exist."
            _3D4D_ultra_logger.warning(notice)
            self.meta['textgrid_exists'] = False
            self.excluded = True

        if ult_file.is_file():
            self.meta['ult_file'] = str(ult_file)
            self.meta['ult_exists'] = True
        else:
            notice = 'Note: ' + str(ult_file) + " does not exist."
            _3D4D_ultra_logger.warning(notice)
            self.meta['ult_exists'] = False
            self.excluded = True

        if video_file.is_file():
            self.meta['video_file'] = str(video_file)
            self.meta['video_exists'] = True
        else:
            notice = 'Note: ' + str(video_file) + " does not exist."
            _3D4D_ultra_logger.warning(notice)
            self.meta['video_exists'] = False
            if requireVideo:
                self.excluded = True

    def addMeta(self, meta):
        """
        Update self.meta with only the required key-value pairs.

        The keys in meta are checked against
        ThreeD_UltrasoundRecording.requiredMetaKeys.
        It is a fatal error to not provide a value for all of those keys.
        Any extra key-value pairs are discarded.

        Positional argument:
        meta -- a dict containing metadata.

        Returns None.
        """
        if meta != None:
            try:
                wanted_meta = {
                    key: meta[key]
                    for key in ThreeD_UltrasoundRecording.requiredMetaKeys}
            except KeyError:
                # Missing metadata for one recording may be ok and this
                # could be handled with just a call to
                # _recording_logger.critical and setting
                # self.excluded = True.
                notFound = set(
                    ThreeD_UltrasoundRecording.requiredMetaKeys) - set(meta)
                _3D4D_ultra_logger.critical(
                    "Part of metadata missing when processing " + self.meta
                    ['filename'] + ". ")
                _3D4D_ultra_logger.critical(
                    "Could not find " + str(notFound) + ".")
                _3D4D_ultra_logger.critical('Exiting.')
                sys.exit()

            self.meta.update(wanted_meta)

    def addModalities(self, wavPreload=True, ultPreload=False,
                      videoPreload=False):
        """
        Add audio and raw ultrasound data to the recording.

        Keyword arguments:
        wavPreload -- boolean indicating if the .wav file is to be read into
            memory on initialising. Defaults to True.
        ultPreload -- boolean indicating if the .ult file is to be read into
            memory on initialising. Defaults to False. Note: these
            files are, roughly one to two orders of magnitude
            larger than .wav files.
        videoPreload -- boolean indicating if the .avi file is to be read into
            memory on initialising. Defaults to False. Note: these
            files are, yet again, roughly one to two orders of magnitude
            larger than .ult files.

        Throws KeyError if TimeInSecsOfFirstFrame is missing from the 
        meta file: [directory]/basename + .txt.
        """
        _3D4D_ultra_logger.info("Adding modalities to recording for "
                                + self.meta['basename'] + ".")

        # TODO: need to make sure that beep detect is not run.
        waveform = MonoAudio(
            parent=self,
            preload=wavPreload,
            time_offset=0,
            filename=self.meta['ult_wav_file']
        )
        self.addModality(MonoAudio.__name__, waveform)
        _3D4D_ultra_logger.debug(
            "Added MonoAudio to Recording representing "
            + self.meta['basename'] + ".")

        # ultMeta = parseUltrasoundMetaAAA(recording.meta['ult_meta_file'])

        ultrasound = ThreeD_Ultrasound(
            parent=self,
            preload=ultPreload,
            filename=self.meta['ult_file']
        )
        self.addModality(ThreeD_Ultrasound.__name__, ultrasound)
        _3D4D_ultra_logger.debug(
            "Added RawUltrasound to Recording representing "
            + self.meta['basename'] + ".")

        if self.meta['video_exists']:
            # This is the correct value for fps for a de-interlaced
            # video for AAA recordings. Check it for other data.
            videoMeta = {
                'FramesPerSec': 59.94
            }
            warnings.warn(
                "Video (.avi) fps set to " + str(videoMeta['FramesPerSec']) +
                "This is the correct value for fps for a de-interlaced video "
                + " for AAA recordings. Check it for other data.")

            video = Video(
                parent=self,
                preload=videoPreload,
                path=self.meta['video_file'],
                meta=videoMeta
            )
            self.addModality(Video.__name__, video)
            _3D4D_ultra_logger.debug(
                "Added LipVideo to Recording representing"
                + self.meta['basename'] + ".")
