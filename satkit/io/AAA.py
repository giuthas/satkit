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
from contextlib import closing
import csv
from datetime import datetime
import glob
import logging
import os
import os.path

# Numpy
import numpy as np
from satkit import recording

# Local packages
from satkit.recording import RawUltrasound, Recording, MonoAudio

_AAA_logger = logging.getLogger('satkit.AAA')

# this belongs in the thing that reads
# if data.excluded:
#     notice += ': Token excluded.'
#     _pd_logger.info(notice)


#
# The logic here is to do a as much as we can with minimal arguments.
# Therefore, generateRecordingList uses helpers to read all the meta
# and all the Data that it can without using any other arguments.
#
# Next step is to decorate that list with single file passes
# like the exclusion list and splines.
#

def generateRecordingList(directory):
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
    ultrasound meta: US.txt,
    ultrasound: .ult,
    audio waveform: .wav, and
    TextGrid: .textgrid.

    directory -- the path to the directory to be processed.
    Returns an array of Recording objects sorted by date and time
        of recording.
    """
    # this is equivalent with the following:
    # sorted(glob.glob(directory + '/.' +  '/*US.txt'))
    ult_meta_files = sorted(glob.glob(directory + '/*US.txt'))

    # this takes care of *.txt and *US.txt overlapping. Goal
    # here is to include also failed recordings with missing
    # ultrasound data in the list for completeness.
    ult_prompt_files = [prompt_file
                        for prompt_file in glob.glob(directory + '/*.txt')
                        if not prompt_file in ult_meta_files
                        ]
    ult_prompt_files = sorted(ult_prompt_files)

    # strip file extensions off of filepaths to get the base names
    base_names = [os.path.splitext(prompt_file)[0]
                  for prompt_file in ult_prompt_files]
    recordings = [
        generateUltrasoundRecording(base_name, directory)
        for base_name in base_names
    ]
    return sorted(recordings, key=lambda token: token.meta['date_and_time'])


def generateUltrasoundRecording(
        basename, directory="", wavPreload=True, ultPreload=False):
    """
    Generate an UltrasoundRecording with audio and raw ultrasound data.

    Arguments:
    basename -- name of the files to be read without type extensions but 
        with path.

    KeywordArguments:
    directory -- path to files
    wavPreload -- boolean indicating if the .wav file is to be read into 
        memory on initialising. Defaults to True.
    ultPreload -- boolean indicating if the .ult file is to be read into 
        memory on initialising. Defaults to False.

    Returns an AAA_UltrasoundRecording with data members MonoAudio and
    RawUltrasound.

    Throws KeyError if TimeInSecsOfFirstFrame is missing from the file.
    """

    recording = AAA_UltrasoundRecording(
        path=directory,
        basename=basename
    )

    ultMeta = parseUltrasoundMetaAAA(recording.meta['ult_meta_file'])

    waveform = MonoAudio(
        parent=recording,
        preload=wavPreload,
        timeOffset=0,
        filename=recording.meta['ult_wav_file']
    )
    recording.addModality(waveform)

    # We pop the timeoffset from the meta dict so that people will not
    # accidentally rely on setting that to alter the timeoffset of the
    # ultrasound data in the Recording. This throws KeyError if the meta
    # file didn't contain TimeInSecsOfFirstFrame.
    ult_timeOffSet = ultMeta.pop('TimeInSecsOfFirstFrame')

    ultrasound = RawUltrasound(
        parent=recording,
        preload=ultPreload,
        timeOffset=ult_timeOffSet,
        filename=recording.meta['ult_file'],
        meta=ultMeta
    )
    recording.addModality(ultrasound)

    return recording


def parseUltrasoundMetaAAA(filename):
    """
    Parse metadata from an AAA 'US.txt' file into a dictionary.

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
    with closing(open(filename, 'r')) as metafile:
        for line in metafile:
            (key, value_str) = line.split("=")
            try:
                value = int(value_str)
            except ValueError:
                value = float(value_str)
            meta[key] = value

        _AAA_logger.debug(
            "Read and parsed ultrasound metafile " + filename + ".")
    return meta


def set_file_exclusions_from_list(filename, recordings):
    """
    Read list of files (that is, recordings) to be excluded from processing
    and mark them as excluded in the array of recording objects.
    """
    if filename is not None:
        with closing(open(filename, 'r')) as csvfile:
            reader = csv.reader(csvfile, delimiter='\t')
            # Throw away the second field - it is a comment for human readers.
            exclusion_list = [row[0] for row in reader]
            _AAA_logger.info('Read exclusion list ' + filename + ' with ' +
                             str(len(exclusion_list)) + ' names.')
    else:
        exclusion_list = []

    # mark as excluded
    [recording.exclude() for recording in recordings if recording in exclusion_list]


def read_file_exclusion_list(filename):
    """
    Read list of files (that is, recordings) to be excluded from processing.
    """
    if filename is not None:
        with closing(open(filename, 'r')) as csvfile:
            reader = csv.reader(csvfile, delimiter='\t')
            # Throw away the second field - it is a comment for human readers.
            exclusion_list = [row[0] for row in reader]
            _AAA_logger.info('Read exclusion list ' + filename + ' with ' +
                             str(len(exclusion_list)) + ' names.')
    else:
        exclusion_list = []

    return exclusion_list


def parse_spline_line(line):
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
    with closing(open(filename, 'r')) as splinefile:
        splinefile.readline()  # Discard the headers on first line.
        table = [parse_spline_line(line) for line in splinefile.readlines()]

    _AAA_logger.info("Read file " + filename + ".")
    return table


def getSplinesForRecordings(recordingList, spline_file):
    # select the right recording here - we are accessing a database.
    # splines = retrieve_splines(token['spline_file'], token['prompt'])
    # splines = retrieve_splines('annd_sample/File003_splines.csv',
    #                            token['prompt'])
    if spline_file:
        splines = retrieve_splines(spline_file)
        for token in recordingList:
            table = [
                row for row in splines
                if row['date_and_time'] == token['date_and_time']]
            token['splines'] = table
            _AAA_logger.debug(
                token['prompt'] + ' has ' + str(len(table)) + 'splines.')

    return recordingList


class AAA_UltrasoundRecording(Recording):
    """
    Ultrasound recording exported from AAA.
    """

    def __init__(self, path=None, basename=""):
        super().__init__(path=path, basename=basename)

        if basename == None:
            _AAA_logger.critical("Critical error: File basename is None.")
        elif basename == "":
            _AAA_logger.critical("Critical error: File basename is empty.")

        _AAA_logger.debug(
            "Initialising a new recording with filename " + basename + ".")
        self.meta['base_name'] = basename

        # Prompt file should always exist and correspond to the base_name because
        # the base_name list is generated from the directory listing of prompt files.
        ult_prompt_file = basename + ".txt"
        self.meta['ult_prompt_file'] = ult_prompt_file
        self.parse_AAA_promptfile(ult_prompt_file)

        # (prompt, date_and_time, participant) = read_prompt(ult_prompt_file)
        # meta['prompt'] = prompt
        # meta['date_and_time'] = date_and_time
        # meta['participant'] = participant

        # Candidates for filenames. Existence tested below.
        ult_meta_file = os.path.join(basename + "US.txt")
        ult_wav_file = os.path.join(basename + ".wav")
        ult_file = os.path.join(basename + ".ult")

        # check if assumed files exist, and arrange to skip them if any do not
        if os.path.isfile(ult_meta_file):
            self.meta['ult_meta_file'] = ult_meta_file
            self.meta['ult_meta_exists'] = True
        else:
            notice = 'Note: ' + ult_meta_file + " does not exist."
            _AAA_logger.warning(notice)
            self.meta['ult_meta_exists'] = False
            self.meta['excluded'] = True

        if os.path.isfile(ult_wav_file):
            self.meta['ult_wav_file'] = ult_wav_file
            self.meta['ult_wav_exists'] = True
        else:
            notice = 'Note: ' + ult_wav_file + " does not exist."
            _AAA_logger.warning(notice)
            self.meta['ult_wav_exists'] = False
            self.meta['excluded'] = True

        if os.path.isfile(ult_file):
            self.meta['ult_file'] = ult_file
            self.meta['ult_exists'] = True
        else:
            notice = 'Note: ' + ult_file + " does not exist."
            _AAA_logger.warning(notice)
            self.meta['ult_exists'] = False
            self.meta['excluded'] = True

        # TODO this needs to be moved to a decorator function
        # if 'water swallow' in prompt:
        #     notice = 'Note: ' + base_names[i] + ' prompt is a water swallow.'
        #     _AAA_logger.info(notice)
        #     self.meta['type'] = 'water swallow'
        #     self.meta['excluded'] = True
        # elif 'bite plate' in prompt:
        #     notice = 'Note: ' + base_names[i] + ' prompt is a bite plate.'
        #     _AAA_logger.info(notice)
        #     self.meta['type'] = 'bite plate'
        #     self.meta['excluded'] = True
        # else:
        #     self.meta['type'] = 'regular trial'
        # store also the different variations of the
        # file name, checking for existence

    def parse_AAA_promptfile(self, filename):
        """
        Read an AAA .txt (not US.txt) file and save prompt, recording date and time,  
        and participant name into the meta dictionary.
        """
        with closing(open(filename, 'r')) as promptfile:
            lines = promptfile.read().splitlines()
            self.meta['prompt'] = lines[0]

            # The date used to be just a string, but needs to be more sturctured since
            # the spline export files have a different date format.
            self.meta['date'] = datetime.strptime(
                lines[1], '%d/%m/%Y %H:%M:%S')

            if len(lines) > 2 and lines[2].strip():
                self.meta['participant'] = lines[2].split(',')[0]
            else:
                _AAA_logger.info(
                    "Participant does not have an id in file " + filename + ".")
                self.meta['participant'] = ""

            _AAA_logger.debug("Read prompt file " + filename + ".")
