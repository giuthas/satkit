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
from contextlib import closing
from datetime import datetime
import glob
import logging
import os
import os.path
from pathlib import Path

# Numpy
import numpy as np

# Local packages
from satkit.recording import RawUltrasound, Recording, MonoAudio
from satkit.io.AAA_video import LipVideo

_AAA_logger = logging.getLogger('satkit.AAA')


#
# The logic here is to do a as much as we can with minimal arguments.
# Therefore, generate_recording_list uses helpers to read all the meta
# and all the Data that it can without using any other arguments.
#
# Next step is to decorate that list with single file passes
# like the exclusion list and splines.
#

def generate_recording_list(directory):
    """
    Produce an array of Recordings from an AAA export directory.

    Prepare a list of Recording objects from the files exported by AAA
    into the named directory. File existence is tested for,
    and if crucial files are missing from a given recording it will be
    excluded.

    Each recording meta file (.txt, not US.txt) will
    be represented by a Recording object regardless of whether a complete
    set of files was found for the recording. Exclusion is marked with
    recordingObjet.excluded rather than not listing the recording. Log
    file will show reasons of exclusion.

    The processed files are
    recording meta: .txt,
    ultrasound meta: US.txt or .param,
    ultrasound: .ult, and
    audio waveform: .wav.

    Additionally these will be added, but missing files are considered
    non-fatal
    TextGrid: .textgrid, and
    avi video: .avi.

    directory -- the path to the directory to be processed.
    Returns an array of Recording objects sorted by date and time
        of recording.
    """
    # this is equivalent with the following:
    # sorted(glob.glob(directory + '/.' +  '/*US.txt'))
    ult_meta_files = sorted(glob.glob(directory + '/*US.txt'))
    if len(ult_meta_files) == 0:
        ult_meta_files = sorted(glob.glob(directory + '/*.param'))

    # this takes care of *.txt and *US.txt overlapping. Goal
    # here is to include also failed recordings with missing
    # ultrasound data in the list for completeness.
    ult_prompt_files = [prompt_file
                        for prompt_file in glob.glob(directory + '/*.txt')
                        if not prompt_file in ult_meta_files
                        ]
    ult_prompt_files = sorted(ult_prompt_files)

    # strip file extensions off of filepaths to get the base names
    base_paths = [os.path.splitext(prompt_file)[0]
                  for prompt_file in ult_prompt_files]
    basenames = [Path(path).name for path in base_paths]
    recordings = [
        generate_ultrasound_recording(basename, directory)
        for basename in basenames
    ]
    return sorted(recordings, key=lambda token: token.meta['date'])


def generate_ultrasound_recording(basename, directory=""):
    """
    Generate an UltrasoundRecording without Modalities.

    Arguments:
    basename -- name of the files to be read without type extensions but
        with path.

    KeywordArguments:
    directory -- path to files

    Returns an AaaUltrasoundRecording without any modalities.
    """

    _AAA_logger.info(
        "Building Recording object for %s in %s.", basename, directory)

    recording = AaaUltrasoundRecording(
        path=directory,
        basename=basename
    )

    # If we aren't going to process this recording,
    # don't bother with the rest.
    if recording.excluded:
        _AAA_logger.info(
            'Recording %s automatically excluded.', basename)

    return recording


def parse_ultrasound_meta_aaa(filename):
    """
    Parse metadata from an AAA export file into a dictionary.

    This is either a 'US.txt' or a '.param' file. They have 
    the same format.

    Arguments:
    filename -- path and name of file to be parsed.

    Returns a dictionary which should contain the following keys:
        NumVectors -- number of scanlines in a frame
        PixPerVector -- number of pixels in a scanline
        ZeroOffset --
        BitsPerPixel -- byte length of a single pixel in the .ult file
        Angle -- angle in radians between two scanlines
        Kind --
        PixelsPerMm -- depth resolution of a scanline
        FramesPerSec -- framerate of ultrasound recording
        TimeInSecsOfFirstFrame -- time from recording start to first frame
    """
    meta = {}
    with closing(open(filename, 'r', encoding="utf8")) as metafile:
        for line in metafile:
            (key, value_str) = line.split("=")
            try:
                value = int(value_str)
            except ValueError:
                value = float(value_str)
            meta[key] = value

        _AAA_logger.debug(
            "Read and parsed ultrasound metafile %s.", filename)
        meta['meta_file'] = filename
    return meta


def parse_spline_line(line):
    """Parse a single line in a old AAA spline export file."""
    # This relies on none of the fields being empty and is necessary to be
    # able to process AAA's output which sometimes has extra tabs.
    cells = line.split('\t')
    token = {'id': cells[0],
             'date_and_time': datetime.strptime(
        cells[1],
        '%m/%d/%Y %I:%M:%S %p'),
        'sample_time': float(cells[2]),
        'prompt': cells[3],
        'nro_spline_points': int(cells[4]),
        'beg': 0, 'end': 42}

    # token['x'] = np.fromiter(cells[8:8+token['nro_spline_points']:2], dtype='float')
    # token['y'] = np.fromiter(cells[9:9+token['nro_spline_points']:2], dtype='float')

    #    temp = [token['x'], token['y']]
    #    nans = np.sum(np.isnan(temp), axis=0)
    #    print(token['prompt'])
    #    print('first ' + str(nans[::-1].cumsum(0).argmax(0)))
    #    print('last ' + str(nans.cumsum(0).argmax(0)))

    token['r'] = np.fromiter(
        cells[5: 5 + token['nro_spline_points']],
        dtype='float')
    token['phi'] = np.fromiter(
        cells
        [5 + token['nro_spline_points']: 5 + 2 * token['nro_spline_points']],
        dtype='float')
    token['conf'] = np.fromiter(
        cells
        [5 + 2 * token['nro_spline_points']: 5 + 3 * token
         ['nro_spline_points']],
        dtype='float')
    token['x'] = np.multiply(token['r'], np.sin(token['phi']))
    token['y'] = np.multiply(token['r'], np.cos(token['phi']))

    return token


def retrieve_splines(filename):
    """
    Read all splines from the file.
    """
    with closing(open(filename, 'r',encoding="utf8")) as splinefile:
        splinefile.readline()  # Discard the headers on first line.
        table = [parse_spline_line(line) for line in splinefile.readlines()]

    _AAA_logger.info("Read file %s.", filename)
    return table


def add_splines_from_file(recording_list, spline_file):
    """
    Add a Spline data object to each recording.

    The splines are read from a single AAA export file and added to
    the correct Recording by identifying the Recordings based on the date
    and time of the original recording. If no splines are found for a
    given Recording, an empty Spline object will be attached to it.

    Arguments:
    recording_list -- a list of Recording objects
    spline_file -- an AAA export file containing splines

    Return -- None. Recordings are modified in place.
    """
    # select the right recording here - we are accessing a database.
    # splines = retrieve_splines(token['spline_file'], token['prompt'])
    # splines = retrieve_splines('annd_sample/File003_splines.csv',
    #                            token['prompt'])
    raise NotImplementedError(
        "Adding splines nor the Spline modality have not yet been implemented.")
    # if spline_file:
    #     splines = retrieve_splines(spline_file)
    #     for token in recording_list:
    #         table = [
    #             row for row in splines
    #             if row['date_and_time'] == token['date_and_time']]
    #         token['splines'] = table
    #         _AAA_logger.debug(
    #             token['prompt'] + ' has ' + str(len(table)) + 'splines.')
    #
    # return recording_list


class AaaUltrasoundRecording(Recording):
    """
    Ultrasound recording exported from AAA.
    """

    def __init__(self, path=None, basename="", requireVideo=False):
        super().__init__(path=path, basename=basename)
        self._read_textgrid()

        if basename is None:
            _AAA_logger.critical("Critical error: File basename is None.")
        elif basename == "":
            _AAA_logger.critical("Critical error: File basename is empty.")

        _AAA_logger.debug(
            "Initialising a new recording with filename %s.", basename)

        # Prompt file should always exist and correspond to the basename because
        # the basename list is generated from the directory listing of prompt files.
        ult_prompt_file = os.path.join(path, basename + ".txt")
        self.meta['ult_prompt_file'] = ult_prompt_file
        self.parse_aaa_promptfile(ult_prompt_file)

        # (prompt, date_and_time, participant) = read_prompt(ult_prompt_file)
        # meta['prompt'] = prompt
        # meta['date_and_time'] = date_and_time
        # meta['participant'] = participant

        # Candidates for filenames. Existence tested below.
        ult_meta_file = os.path.join(path, basename + "US.txt")
        ult_meta_file2 = os.path.join(path, basename + ".param")
        ult_wav_file = os.path.join(path, basename + ".wav")
        ult_file = os.path.join(path, basename + ".ult")
        video_file = os.path.join(path, basename + ".avi")

        # check if assumed files exist, and arrange to skip them if any do not
        if os.path.isfile(ult_meta_file):
            self.meta['ult_meta_file'] = ult_meta_file
            self.meta['ult_meta_exists'] = True
        elif os.path.isfile(ult_meta_file2):
            self.meta['ult_meta_file'] = ult_meta_file2
            self.meta['ult_meta_exists'] = True
        else:
            notice = 'Note: ' + ult_meta_file + " does not exist."
            _AAA_logger.warning(notice)
            self.meta['ult_meta_exists'] = False
            self.excluded = True

        if os.path.isfile(ult_wav_file):
            self.meta['ult_wav_file'] = ult_wav_file
            self.meta['ult_wav_exists'] = True
        else:
            notice = 'Note: ' + ult_wav_file + " does not exist."
            _AAA_logger.warning(notice)
            self.meta['ult_wav_exists'] = False
            self.excluded = True

        if os.path.isfile(ult_file):
            self.meta['ult_file'] = ult_file
            self.meta['ult_exists'] = True
        else:
            notice = 'Note: ' + ult_file + " does not exist."
            _AAA_logger.warning(notice)
            self.meta['ult_exists'] = False
            self.excluded = True

        if os.path.isfile(video_file):
            self.meta['video_file'] = video_file
            self.meta['video_exists'] = True
        else:
            notice = 'Note: ' + video_file + " does not exist."
            _AAA_logger.warning(notice)
            self.meta['video_exists'] = False
            if requireVideo:
                self.excluded = True

        # TODO this needs to be moved to a decorator function
        # if 'water swallow' in self.meta['prompt']:
        #     notice = 'Note: ' + basename + ' prompt is a water swallow.'
        #     _AAA_logger.info(notice)
        #     self.meta['type'] = 'water swallow'
        #     self.excluded = True
        # elif 'bite plate' in self.meta['prompt']:
        #     notice = 'Note: ' + basename + ' prompt is a bite plate.'
        #     _AAA_logger.info(notice)
        #     self.meta['type'] = 'bite plate'
        #     self.excluded = True
        # else:
        #     self.meta['type'] = 'regular trial'

    def parse_aaa_promptfile(self, filename):
        """
        Read an AAA .txt (not US.txt or .param) file and save prompt, 
        recording date and time, and participant name into the meta dictionary.
        """
        with closing(open(filename, 'r', encoding="utf8")) as promptfile:
            lines = promptfile.read().splitlines()
            self.meta['prompt'] = lines[0]

            # The date used to be just a string, but needs to be more sturctured since
            # the spline export files have a different date format.
            self.meta['date_and_time'] = datetime.strptime(
                lines[1], '%d/%m/%Y %H:%M:%S')
            # TODO: hunt and remove uses of either date or date_and_time and use only one in the future.
            self.meta['date'] = self.meta['date_and_time']

            if len(lines) > 2 and lines[2].strip():
                self.meta['participant'] = lines[2].split(',')[0]
            else:
                _AAA_logger.info(
                    "Participant does not have an id in file %s.", filename)
                self.meta['participant'] = ""

            _AAA_logger.debug("Read prompt file %s.", filename)

    def add_modalities(self, wav_preload=True, ult_preload=False,
                      video_preload=False):
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
        _AAA_logger.info("Adding modalities to recording for %s.",
            self.meta['basename'])

        waveform = MonoAudio(
            parent=self,
            preload=wav_preload,
            timeOffset=0,
            filename=self.meta['ult_wav_file']
        )
        self.addModality(MonoAudio.__name__, waveform)
        _AAA_logger.debug(
            "Added MonoAudio to Recording representing %s.",
            self.meta['basename'])

        ult_meta = parse_ultrasound_meta_aaa(self.meta['ult_meta_file'])

        # We pop the timeoffset from the meta dict so that people will not
        # accidentally rely on setting that to alter the timeoffset of the
        # ultrasound data in the Recording. This throws KeyError if the meta
        # file didn't contain TimeInSecsOfFirstFrame.
        ult_time_offset = ult_meta.pop('TimeInSecsOfFirstFrame')

        ultrasound = RawUltrasound(
            parent=self,
            preload=ult_preload,
            timeOffset=ult_time_offset,
            filename=self.meta['ult_file'],
            meta=ult_meta
        )
        self.addModality(RawUltrasound.__name__, ultrasound)
        _AAA_logger.debug(
            "Added RawUltrasound to Recording representing %s.",
            self.meta['basename'])

        if self.meta['video_exists']:
            # This is the correct value for fps for a de-interlaced
            # video according to Alan, and he should know having
            # written AAA.
            video_meta = {
                'FramesPerSec': 59.94
            }

            video = LipVideo(
                parent=self,
                preload=video_preload,
                filename=self.meta['video_file'],
                meta=video_meta
            )
            self.addModality(LipVideo.__name__, video)
            _AAA_logger.debug(
                "Added LipVideo to Recording representing %s.",
                self.meta['basename'])
