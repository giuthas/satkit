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

import csv
import logging
from contextlib import closing
from copy import deepcopy
from pathlib import Path
from typing import Dict, Optional

from satkit.data_structures import (
    FileInformation, Recording, SessionConfig)

from .three_dim_ultrasound import (add_rasl_3D_ultrasound,
                                   generateMeta,
                                   read_3D_meta_from_mat_file)
from .audio import add_audio
from .video import add_video
from ..configuration import ExclusionList, PathStructure, apply_exclusion_list

_logger = logging.getLogger('satkit.ThreeD_ultrasound')


def generate_rasl_recording_list(
        directory: Path,
        config: SessionConfig | None = None,
        exclusion_list: ExclusionList | None = None,
        paths: PathStructure | None = None,
        detect_beep: bool = False
):
    """
    Produce an array of Recordings from a 3D4D ultrasound directory.

    Prepare a list of Recording objects from the files exported by AAA
    into the named directory. File existence is tested for,
    and if crucial files are missing from a given recording it will be
    excluded.

    If problems are found with a recording, exclusion is marked with
    `recordingObjet.excluded` rather than not listing the recording. Log
    file will show reasons of exclusion.

    The processed files are
    ultrasound and corresponding meta: .DCM, and
    audio waveform: .dat or .wav.

    Additionally, this will be added, but missing files are considered
    non-fatal:
    TextGrid: .textgrid.

    Positional argument:
    directory -- the path to the directory to be processed.
    Returns an array of Recording objects sorted by date and time
        of recording.
    """

    # TODO: put these in the session_config.paths
    dicom_dir = directory / "DICOM"
    note_dir = directory / "NOTES"
    wav_dir = directory / 'WAV'
    avi_dir = directory / 'AVI'
    directories = {
        'root_dir': directory,
        'dicom_dir': dicom_dir,
        'note_dir': note_dir,
        'wav_dir': wav_dir,
        'avi_dir': avi_dir
    }

    dicom_files = sorted(dicom_dir.glob('*.DCM'))
    mat_file = list(note_dir.glob('officialNotes*.mat'))[0]

    # strip file extensions off of filepaths to get the base names
    dicom_basenames = [filepath.name for filepath in dicom_files]
    meta = read_3D_meta_from_mat_file(mat_file)

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
            recording = generate_3D_ultrasound_recording(
                dicom_dict[token['trial_number']],
                token['dat_filename'],
                directories)
            # TODO: replace the call below with what ever is the new way of
            # doing it.
            # recording.addMeta(token)
            recordings.append(recording)
        else:
            _logger.info(
                'No DICOM file corresponding to number %d found in %s.',
                token['trial_number'], str(directory))

    # TODO: this call is wrong, but will get fixed later.
    apply_exclusion_list(
        recordings=recordings,
        exclusion_list=exclusion_list,
        )

    for recording in recordings:
        if not recording.excluded:
            add_modalities(recording=recording, detect_beep=detect_beep)

    return sorted(recordings, key=lambda
                  token: token.metadata.time_of_recording)

    # return sorted(recordings, key=lambda token: token.meta['date_and_time'])


def generate_recording_list_old_style(directory):
    """
    Produce an array of Recordings from a directory without .mat notes file.

    Prepare a list of Recording objects from the files exported by AAA
    into the named directory. File existence is tested for,
    and if crucial files are missing from a given recording it will be
    excluded.

    If problems are found with a recording, exclusion is marked with
    `recordingObjet.excluded` rather than not listing the recording. Log
    file will show reasons of exclusion.

    The processed files are
    ultrasound and corresponding meta: .DCM, and
    audio waveform: .dat or .wav.

    Additionally, this will be added, but missing files are considered
    non-fatal:
    TextGrid: .textgrid.

    Positional argument:
    directory -- the path to the directory to be processed.
    Returns an array of Recording objects sorted by date and time
        of recording.
    """

    path = Path(directory)
    wav_dir = path / "WAV"

    dicom_dir = directory / "DICOM"
    note_dir = directory / "NOTES"
    directories = {
        'root_dir': directory,
        'dicom_dir': dicom_dir,
        'note_dir': note_dir,
    }

    with closing(open(path/"notes.csv", 'r', encoding='utf-8')) as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t',)

        rows = [row for row in reader if row]

        for row in rows:
            row['DCM'] = "DICOM/{name}_{number:0>3}.DCM".format(
                name=row['US File Name'],
                number=row['US File Number'])
            row['number_portion'] = "{number:0>3}".format(
                number=row['US File Number'])

            # print(row['Stimulus'])
            # print(row['DCM'])

            # this marks if the recording should be disregarded
            print(row['junkBox'])

            textgrid = list(wav_dir.glob(
                "*" + row['DAT File Time Stamp'] + "*.TextGrid"))[0]
            wav = deepcopy(textgrid)
            wav = wav.with_suffix('.wav')

            # print(textgrid)
            # print(wav)

            row['TextGrid'] = str(textgrid)
            row['sound_filename'] = wav.stem

    dicom_files = sorted(dicom_dir.glob('*.DCM'))
    # dicom_files = [Path(row['DCM']) for row in rows if row]

    # strip file extensions off of filepaths to get the base names
    dicom_basenames = [filepath.name for filepath in dicom_files]
    meta = generateMeta(rows)

    # Create a lookup table for matching sound and dicom.
    # First file names with their ordinal numbers.
    dicom_names_numbers = [[name, name.split('_')[1]]
                           for name in dicom_basenames]
    # Then a dict mapping number strings to filenames.
    dicom_dict = {
        name_number[1].split('.')[0]: name_number[0]
        for name_number in dicom_names_numbers
    }

    for token in meta:
        if token['trial_number'] in dicom_dict:
            token['filename'] = dicom_dict[token['trial_number']]
        else:
            meta.remove(token)

    recordings = []
    for token in meta:
        if token['trial_number'] in dicom_dict:
            _logger.debug(
                "Processing %s.", dicom_dict[token['trial_number']])
            recording = generate_3D_ultrasound_recording(
                dicom_dict[token['trial_number']],
                token['sound_filename'],
                directories,
                token)
            recordings.append(recording)
        else:
            _logger.info(
                'No DICOM file corresponding to number ' +
                token['trial_number'] + ' found in ' + str(directory) + '.')

    return sorted(recordings, key=lambda token: token.meta['date_and_time'])


def generate_3D_ultrasound_recording(
        dicom_name: str,
        sound_name: str,
        meta: dict,
        directories: Optional[Dict[str, Path]] = None
) -> Recording:
    """
    Generate an UltrasoundRecording without Modalities.

    Arguments:
    dicom_name -- name of the DICOM files to be read without type 
        extensions but with path.
    sound_name -- name of the sound files (.dat and .wav) to be read 
        without type extensions but with path.

    KeywordArguments:
    directory -- path to files

    Returns an ThreeD_UltrasoundRecording without any modalities.
    """

    _logger.info(
        "Building Recording object for " + str(dicom_name) + " in " +
        str(directories['root_dir']) + ".")

    # Candidates for filenames. Existence tested below.
    ult_wav_file = directories['wav_dir']/sound_name.with_suffix(".wav")
    textgrid = directories['wav_dir']/sound_name.with_suffix(".TextGrid")
    ult_file = directories['dicom_dir']/dicom_name
    video_file = directories['avi_dir']/dicom_name
    video_file = video_file.with_suffix(".avi")

    file_info = FileInformation(
        recorded_path=directories['root_dir'],
    )

    if textgrid.is_file():
        recording = Recording(
            metadata=meta,
            file_info=file_info,
            textgrid_path=textgrid
        )
    else:
        recording = Recording(
            metadata=meta,
            file_info=file_info,
        )

    return recording


def add_modalities(
        recording: Recording,
        wav_preload: bool = True,
        detect_beep: bool = False,
        ult_preload: bool = False,
        video_preload: bool = False
) -> None:
    """
    Add audio and raw ultrasound data to the recording.

    Keyword arguments:
    wavPreload -- boolean indicating if the .wav file is to be read into
        memory on initialising. Defaults to True.
    ultPreload -- boolean indicating if the ultrasound in .dicom files 
        should be read into memory on initialising. 
        Defaults to False. Note: these
        files are roughly one to two orders of magnitude
        larger than .wav files.
    videoPreload -- boolean indicating if the .avi file is to be read into
        memory on initialising. Defaults to False. Note: these
        files are, yet again, roughly one to two orders of magnitude
        larger than .dicom files.

    Throws KeyError if TimeInSecsOfFirstFrame is missing from the
    meta file: [directory]/basename + .txt.
    """
    _logger.info("Adding modalities to recording for %s.",
                 recording.basename)

    add_audio(
        recording=recording, preload=wav_preload, detect_beep=detect_beep)
    add_rasl_3D_ultrasound(recording, ult_preload)
    add_video(recording, video_preload)

    # def addModalities(self, wavPreload=True, ultPreload=False,
    #                   videoPreload=False):
    #     """
    #     Add audio and raw ultrasound data to the recording.

    #     Keyword arguments:
    #     wavPreload -- boolean indicating if the .wav file is to be read into
    #         memory on initialising. Defaults to True.
    #     ultPreload -- boolean indicating if the .ult file is to be read into
    #         memory on initialising. Defaults to False. Note: these
    #         files are, roughly one to two orders of magnitude
    #         larger than .wav files.
    #     videoPreload -- boolean indicating if the .avi file is to be read into
    #         memory on initialising. Defaults to False. Note: these
    #         files are, yet again, roughly one to two orders of magnitude
    #         larger than .ult files.

    #     Throws KeyError if TimeInSecsOfFirstFrame is missing from the
    #     meta file: [directory]/basename + .txt.
    #     """
    #     _3D4D_ultra_logger.info("Adding modalities to recording for "
    #                             + self.meta['basename'] + ".")

    #     # TODO: need to make sure that beep detect is not run.
    #     waveform = MonoAudio(
    #         parent=self,
    #         preload=wavPreload,
    #         time_offset=0,
    #         filename=self.meta['ult_wav_file']
    #     )
    #     self.addModality(MonoAudio.__name__, waveform)
    #     _3D4D_ultra_logger.debug(
    #         "Added MonoAudio to Recording representing "
    #         + self.meta['basename'] + ".")

    #     # ultMeta = parseUltrasoundMetaAAA(recording.meta['ult_meta_file'])

    #     ultrasound = ThreeD_Ultrasound(
    #         parent=self,
    #         preload=ultPreload,
    #         filename=self.meta['ult_file']
    #     )
    #     self.addModality(ThreeD_Ultrasound.__name__, ultrasound)
    #     _3D4D_ultra_logger.debug(
    #         "Added RawUltrasound to Recording representing "
    #         + self.meta['basename'] + ".")

    #     if self.meta['video_exists']:
    #         # This is the correct value for fps for a de-interlaced
    #         # video for AAA recordings. Check it for other data.
    #         videoMeta = {
    #             'FramesPerSec': 59.94
    #         }
    #         warnings.warn(
    #             "Video (.avi) fps set to " + str(videoMeta['FramesPerSec']) +
    #             "This is the correct value for fps for a de-interlaced video "
    #             + " for AAA recordings. Check it for other data.")

    #         video = Video(
    #             parent=self,
    #             preload=videoPreload,
    #             path=self.meta['video_file'],
    #             meta=videoMeta
    #         )
    #         self.addModality(Video.__name__, video)
    #         _3D4D_ultra_logger.debug(
    #             "Added LipVideo to Recording representing"
    #             + self.meta['basename'] + ".")
