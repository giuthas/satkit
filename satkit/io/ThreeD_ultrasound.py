#
# Copyright (c) 2019-2021 Pertti Palo, Scott Moisik, and Matthew Faytak.
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
from datetime import datetime
import logging
from pathlib import PureWindowsPath
import warnings
import sys

# Numpy and scipy
import numpy as np
from numpy.matlib import repmat
import scipy.io

# dicom reading
import pydicom

# Local packages
from satkit.recording import MatrixData, MonoAudio, Recording
from satkit.io.AAA_video import LipVideo

_3D4D_ultra_logger = logging.getLogger('satkit.ThreeD_ultrasound')


def generateRecordingList(directory):
    """
    Produce an array of Recordings from a 3D4D ultrasound directory.

    Prepare a list of Recording objects from the files exported by AAA
    into the named directory. File existence is tested for,
    and if crucial files are missing from a given recording it will be
    excluded.

    If problems are found with a recording, exclusion is marked with
    recordingObjet.excluded rather than not listing the recording. Log
    file will show reasons of exclusion.

    The processed files are
    ultrasound and corresponding meta: .DCM, and
    audio waveform: .dat or .wav.

    Additionally this will be added, but missing files are considered
    non-fatal:
    TextGrid: .textgrid.

    Positional argument:
    directory -- the path to the directory to be processed.
    Returns an array of Recording objects sorted by date and time
        of recording.
    """

    dicom_dir = directory / "DICOM"
    note_dir = directory / "NOTES"
    directories = {
        'root_dir': directory,
        'dicom_dir': dicom_dir,
        'note_dir': note_dir,
    }

    dicom_files = sorted(dicom_dir.glob('*.DCM'))
    mat_file = list(note_dir.glob('*.mat'))[0]

    # strip file extensions off of filepaths to get the base names
    dicom_basenames = [filepath.name for filepath in dicom_files]
    meta = ThreeD_UltrasoundRecording.readMetaFromMat(mat_file)

    # Create a lookup table for matching sound and dicom.
    # First file names with their ordinal numbers.
    dicom_names_numbers = [[name, name.split('_')[1]]
                           for name in dicom_basenames]
    # Then a dict mapping number strings to filenames.
    dicom_dict = {
        name_number[1].split('.')[0]: name_number[0]
        for name_number in dicom_names_numbers
    }

    recordings = []
    for token in meta:
        if token['trial_number'] in dicom_dict:
            print(dicom_dict[token['trial_number']])
            recording = generateUltrasoundRecording(
                dicom_dict[token['trial_number']],
                token['dat_filename'],
                directories)
            recording.addMeta(token)
            recordings.append(recording)
        else:
            _3D4D_ultra_logger.info(
                'No DICOM file corresponding to number ' +
                token['trial_number'] + ' found in ' + directory + '.')

    return sorted(recordings, key=lambda token: token.meta['date'])


def generateUltrasoundRecording(dicom_name, sound_name, directories=None):
    """
    Generate an UltrasoundRecording without Modalities.

    Arguments:
    dicom_name -- name of the DICOM files to be read without type 
        extensions but with path.
    sound_name -- name of the sound files (.dat and .wav) to be read 
        without type extensions but with path.

    KeywordArguments:
    directory -- path to files

    Returns an AAA_UltrasoundRecording without any modalities.
    """

    _3D4D_ultra_logger.info(
        "Building Recording object for " + dicom_name + " in " +
        directories['root_dir'] + ".")

    recording = ThreeD_UltrasoundRecording(
        paths=directories,
        basename=dicom_name,
        sound_name=sound_name
    )

    # If we aren't going to process this recording,
    # don't bother with the rest.
    if recording.excluded:
        _3D4D_ultra_logger.info(
            "Recording " + dicom_name + " automatically excluded.")

    return recording


class ThreeD_Ultrasound(MatrixData):
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
                         timeOffset=timeOffset)

        self.meta['filename'] = filename

        if filename and preload:
            self._getData()
        else:
            self._data = None

    def _getData(self):
        ds = pydicom.dcmread(self.meta['filename'])

        # There are other options, but we don't deal with them just yet.
        # Before 1.0: fix the above. see loadPhillipsDCM.m on how.
        if len(ds.SequenceOfUltrasoundRegions) == 3:
            type = ds[0x200d, 0x3016][1][0x200d, 0x300d].valuex
            if type == 'UDM_USD_DATATYPE_DIN_3D_ECHO':
                self._read_3D_ultra(ds)
            else:
                _3D4D_ultra_logger.critical(
                    "Unknown DICOM ultrasound type: " + type + " in "
                    + self.meta['filename'] + ".")
                _3D4D_ultra_logger.critical('Exiting.')
                sys.exit()
        else:
            _3D4D_ultra_logger.critical(
                "Do not know what to do with data with "
                + str(len(ds.SequenceOfUltrasoundRegions)) + " regions in "
                + self.meta['filename'] + ".")
            _3D4D_ultra_logger.critical('Exiting.')
            sys.exit()

        # Before 1.0: 'NumVectors' and 'PixPerVector' are bad names here.
        # They come from the AAA ultrasound side of things and should be
        # replaced, but haven't been yet as I'm in a hurry to get PD
        # running on 3d4d ultrasound.
        self.meta['no_frames'] = self.data.shape[0]
        self.meta['NumVectors'] = self.data.shape[1]
        self.meta['PixPerVector'] = self.data.shape[2]
        ultra3D_time = np.linspace(
            0, self.meta['no_frames'],
            num=self.meta['no_frames'],
            endpoint=False)
        self.timevector = ultra3D_time / \
            self.meta['FramesPerSec'] + self.timeOffset

    def _read_3D_ultra(self, ds):
        ultra_sequence = ds[0x200d, 0x3016][1][0x200d, 0x3020][0]

        # data dimensions
        numberOfFrames = int(ultra_sequence[0x200d, 0x3010].value)
        shape = [int(token) for token in ds[0x200d, 0x3301].value]
        frameSize = np.prod(shape)
        shape.append(numberOfFrames)

        # data scale in real space-time
        scale = [float(token) for token in ds[0x200d, 0x3303].value]
        self.meta['FramesPerSec'] = float(ds[0x200d, 0x3207].value)

        # Before 1.0: unify the way scaling works across the data.
        # here we have an attribute, in AAA ultrasound we have meta
        # keys.
        self._scale = scale

        # The starting index for the non-junk data
        # no junk from pydicom at the beginning. only at end of each frame
        # s = 32

        # Get the number of junk data points between each frame
        interval = (
            len(ultra_sequence[0x200d, 0x300e].value)-frameSize*shape[3])
        interval = int(interval/shape[3])

        data = np.frombuffer(
            ultra_sequence[0x200d, 0x300e].value, dtype=np.uint8)

        # would but no junk in beginning in pydicom
        #data = data[32:]

        data.shape = (frameSize+interval, numberOfFrames)
        index = np.transpose(repmat(np.arange(frameSize), numberOfFrames, 1))

        data = np.take_along_axis(data, index, axis=0)
        data.shape = shape
        print(shape)
        self._data = np.transpose(data)
        print(self._data.shape)

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

    @staticmethod
    def readMetaFromMat(mat_file):
        """
        Read a WASL .mat file and return relevant contents as a dict.

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
        ult_file = self._paths['dicom_dir'].jointpath(basename + ".DCM")
        video_file = self._paths['avi_dir'].joinpath(basename + ".avi")

        # Before 1.0: change the stored format to be a pathlib Path rather than
        # string.
        # check if assumed files exist, and arrange to skip them
        # if any do not
        if ult_wav_file.isfile():
            self.meta['ult_wav_file'] = str(ult_wav_file)
            self.meta['ult_wav_exists'] = True
        else:
            notice = 'Note: ' + str(ult_wav_file) + " does not exist."
            _3D4D_ultra_logger.warning(notice)
            self.meta['ult_wav_exists'] = False
            self.excluded = True

        if ult_file.isfile():
            self.meta['ult_file'] = str(ult_file)
            self.meta['ult_exists'] = True
        else:
            notice = 'Note: ' + str(ult_file) + " does not exist."
            _3D4D_ultra_logger.warning(notice)
            self.meta['ult_exists'] = False
            self.excluded = True

        if video_file.isfile():
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
            timeOffset=0,
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

            video = LipVideo(
                parent=self,
                preload=videoPreload,
                filename=self.meta['video_file'],
                meta=videoMeta
            )
            self.addModality(LipVideo.__name__, video)
            _3D4D_ultra_logger.debug(
                "Added LipVideo to Recording representing"
                + self.meta['basename'] + ".")
