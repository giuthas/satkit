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
    Returns an array of Recording objects sorted by date-time 
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
    return [generateRecording(base_name) for base_name in base_names]


def generateRecording(base_name):

    # this wil do almost all of the testing and such below
    # recording = Recording(path=path, basename=base_name)

    # except when it comes to handling Data:
    # ultrasound = RawUltrasound(
    #     parent=recording,
    #     preload=False,
    #     timeOffset=timeOffset,
    #     filename=recording.meta['ult_file'],
    #     meta=meta
    # )
    # recording.addModality(ultrasound)

    # waveform = MonoAudio(
    #     parent=recording,
    #     preload=True,
    #     timeOffset=0,
    #     filename=recording.meta['ult_wav_file']
    # )
    # recording.addModality(waveform)

    meta = {}
    # Prompt file should always exist and correspond to the base_name because
    # the base_name list is generated from the directory listing of prompt files.
    ult_prompt_file = base_name + ".txt"

    # (prompt, date_and_time, participant) = read_prompt(ult_prompt_file)
    # meta['prompt'] = prompt
    # meta['date_and_time'] = date_and_time
    # meta['participant'] = participant

    # Candidates for filenames. Existence tested below.
    ult_meta_file = os.path.join(base_name + "US.txt")
    ult_wav_file = os.path.join(base_name + ".wav")
    ult_file = os.path.join(base_name + ".ult")
    textgrid = os.path.join(base_name + ".TextGrid")

    # check if assumed files exist, and arrange to skip them if any do not
    if os.path.isfile(ult_meta_file):
        meta['ult_meta_file'] = ult_meta_file
        meta['ult_meta_exists'] = True
    else:
        notice = 'Note: ' + ult_meta_file + " does not exist."
        _AAA_logger.warning(notice)
        meta['ult_meta_exists'] = False
        meta['excluded'] = True

    if os.path.isfile(ult_wav_file):
        meta['ult_wav_file'] = ult_wav_file
        meta['ult_wav_exists'] = True
    else:
        notice = 'Note: ' + ult_wav_file + " does not exist."
        _AAA_logger.warning(notice)
        meta['ult_wav_exists'] = False
        meta['excluded'] = True

    if os.path.isfile(ult_file):
        meta['ult_file'] = ult_file
        meta['ult_exists'] = True
    else:
        notice = 'Note: ' + ult_file + " does not exist."
        _AAA_logger.warning(notice)
        meta['ult_exists'] = False
        meta['excluded'] = True

    if os.path.isfile(textgrid):
        # needs work: following line should actually be done, not just excluded to get this through the compiler.
        #meta['textgrid'] = read_textgrid(textgrid)
        meta['textgrid_exists'] = True
    else:
        notice = 'Note: ' + textgrid + " does not exist."
        _AAA_logger.warning(notice)
        meta['textgrid_exists'] = False
        meta['excluded'] = True


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


class AAA_UltrasoundRecording(Recording):
    """
    Ultrasound recording exported from AAA.
    """

    def __init__(self, path, basename, textgrid):
        super().__init__(path=path, basename=basename, textgrid=textgrid)

        if basename == None:
            _AAA_logger.critical("Critical error: File basename is None.")
        elif basename == "":
            _AAA_logger.critical("Critical error: File basename is empty.")
        else:
            _AAA_logger.debug(
                "Initialising a new recording with filename " + basename + ".")
            self.meta['base_name'] = basename

            # Prompt file should always exist and correspond to the base_name because
            # the base_name list is generated from the directory listing of prompt files.
            self.meta['ult_prompt_file'] = basename + '.txt'
            # (prompt, date, participant) = self.parse_AAA_promptfile(
            #     self.meta['ult_prompt_file'])
            # self.meta['prompt'] = prompt
            # self.meta['date'] = date
            # self.meta['participant'] = participant

            if self.excluded:
                notice = basename + " is in the exclusion list."
                _AAA_logger.info(notice)

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

            self.parse_AAA_promptfile(basename)

# Needs work: this was moved from elsewhere and is waiting reimplementation.
    def setMetaForRawUltra(self, token):
        self.parse_AAA_meta(token['ult_meta_file'])
        ult_fps = self.meta['FramesPerSec']
        ult_NumVectors = self.meta['NumVectors']
        ult_PixPerVector = self.meta['PixPerVector']
        ult_TimeInSecsOfFirstFrame = self.meta['TimeInSecsOfFirstFrame']

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

    def parse_AAA_meta(self, filename):
        """
        Parse metadata from an AAA 'US.txt' file into the meta dictionary.
        """
        with closing(open(filename, 'r')) as metafile:
            for line in metafile:
                (key, value_str) = line.split("=")
                try:
                    value = int(value_str)
                except ValueError:
                    value = float(value_str)
                self.meta[key] = value

            _AAA_logger.debug(
                "Read and parsed ultrasound metafile " + filename + ".")


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


def get_recording_list(directory, exclusion_list_name=None, spline_file=None):
    """
    Prepare a list of files to be processed based on directory
    contents and possible exclusion list. File existence is tested for,
    and if crucial files are missing from a given recording it will be
    excluded.

    The function returns a list of metadata dictionaries sorted by
    time and date of recording.
    """
    # directory handling:
    # add a config file for listing the directories and subdirectories where things are
    # default into everything being in the given dir if no config is present
    #
    # like so:
    # ult_directory = os.path.join(directory, ult_subdirectory)

    # File exclusion list is provided by the user.
    file_exclusion_list = read_file_exclusion_list(exclusion_list_name)

    # this is equivalent with the following:
    # sorted(glob.glob(directory + '/.' +  '/*US.txt'))
    ult_meta_files = sorted(glob.glob(directory + '/*US.txt'))

    # this takes care of *.txt and *US.txt overlapping.
    ult_prompt_files = [prompt_file
                        for prompt_file in glob.glob(directory + '/*.txt')
                        if not prompt_file in ult_meta_files
                        ]
    ult_prompt_files = sorted(ult_prompt_files)

    # strip file extensions off of filepaths to get the base names
    base_names = [os.path.splitext(prompt_file)[0]
                  for prompt_file in ult_prompt_files]
    meta = [{} for base_name in base_names]

    # iterate over file base names and check for required files
    for i, base_name in enumerate(base_names):
        # Prompt file should always exist and correspond to the base_name because
        # the base_name list is generated from the directory listing of prompt files.
        meta[i]['ult_prompt_file'] = ult_prompt_files[i]
        # (prompt, date_and_time, participant) = read_prompt(ult_prompt_files[i])
        # meta[i]['prompt'] = prompt
        # meta[i]['date_and_time'] = date_and_time
        # meta[i]['participant'] = participant

        if base_name in file_exclusion_list:
            notice = base_name + " is in the exclusion list."
            _AAA_logger.info(notice)
            meta[i]['excluded'] = True
        else:
            meta[i]['excluded'] = False

        # Candidates for filenames. Existence tested below.
        ult_meta_file = os.path.join(base_name + "US.txt")
        ult_wav_file = os.path.join(base_name + ".wav")
        ult_file = os.path.join(base_name + ".ult")
        textgrid = os.path.join(base_name + ".TextGrid")
        #spline_file = os.path.join(base_name + "_splines.csv")

        # check if assumed files exist, and arrange to skip them if any do not
        if os.path.isfile(ult_meta_file):
            meta[i]['ult_meta_file'] = ult_meta_file
            meta[i]['ult_meta_exists'] = True
        else:
            notice = 'Note: ' + ult_meta_file + " does not exist."
            _AAA_logger.warning(notice)
            meta[i]['ult_meta_exists'] = False
            meta[i]['excluded'] = True

        if os.path.isfile(ult_wav_file):
            meta[i]['ult_wav_file'] = ult_wav_file
            meta[i]['ult_wav_exists'] = True
        else:
            notice = 'Note: ' + ult_wav_file + " does not exist."
            _AAA_logger.warning(notice)
            meta[i]['ult_wav_exists'] = False
            meta[i]['excluded'] = True

        if os.path.isfile(ult_file):
            meta[i]['ult_file'] = ult_file
            meta[i]['ult_exists'] = True
        else:
            notice = 'Note: ' + ult_file + " does not exist."
            _AAA_logger.warning(notice)
            meta[i]['ult_exists'] = False
            meta[i]['excluded'] = True

        if os.path.isfile(textgrid):
            # needs work: following line should actually be done, not just excluded to get this through the compiler.
            #meta[i]['textgrid'] = read_textgrid(textgrid)
            meta[i]['textgrid_exists'] = True
        else:
            notice = 'Note: ' + textgrid + " does not exist."
            _AAA_logger.warning(notice)
            meta[i]['textgrid_exists'] = False
            meta[i]['excluded'] = True

        # if os.path.isfile(spline_file):
        #     meta[i]['spline_file'] = spline_file
        #     meta[i]['splines_exist'] = True
        # else:
        #     notice = 'Note: ' + spline_file + " does not exist."
        #     _AAA_logger.warning(notice)
        #     meta[i]['splines_exist'] = False
        #     meta[i]['excluded'] = True

        # TODO this needs to be moved to a decorator function
        # if 'water swallow' in prompt:
        #     notice = 'Note: ' + base_names[i] + ' prompt is a water swallow.'
        #     _AAA_logger.info(notice)
        #     meta[i]['type'] = 'water swallow'
        #     meta[i]['excluded'] = True
        # elif 'bite plate' in prompt:
        #     notice = 'Note: ' + base_names[i] + ' prompt is a bite plate.'
        #     _AAA_logger.info(notice)
        #     meta[i]['type'] = 'bite plate'
        #     meta[i]['excluded'] = True
        # else:
        #     meta[i]['type'] = 'regular trial'

    # select the right recording here - we are accessing a database.
    # splines = retrieve_splines(token['spline_file'], token['prompt'])
    # splines = retrieve_splines('annd_sample/File003_splines.csv',
    #                            token['prompt'])
    if spline_file:
        splines = retrieve_splines(spline_file)
        for token in meta:
            table = [
                row for row in splines
                if row['date_and_time'] == token['date_and_time']]
            token['splines'] = table
            _AAA_logger.debug(
                token['prompt'] + ' has ' + str(len(table)) + 'splines.')

    meta = sorted(meta, key=lambda token: token['date_and_time'])

    return meta
