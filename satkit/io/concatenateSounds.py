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
import logging
import sys
import warnings

# Numerical arrays and more
import numpy as np

# wav file handling
import scipy.io.wavfile as sio_wavfile

# Praat textgrids
import textgrids

_concat_logger = logging.getLogger('satkit.concat')


def concatenateSounds(recordings,
                      dirname,
                      modality='MonoAudio',
                      speaker_id=None):
    """
    Calculate PD on dataModality and add it to recording.

    Positional arguments:
    recording -- a Recording object
    modality -- the type of the Modality to be processed. The access will 
        be by recording.modalities[modality.__name__]

    Keyword arguments:
    preload -- boolean indicating if PD should be calculated on creation 
        (preloaded) or only on access.
    releaseDataMemor -- boolean indicatin if the data attribute of the 
        data modality should be set to None after access. Only set this 
        to False, if you know that you have enough memory to hold all 
        of the data in RAM.
    """
    if(len(recordings) < 1):
        warnings.warn(
            "Didn't find any sound files to concatanate in "+dirname+".")
        warnings.warn("Exiting.")
        sys.exit()

    if speaker_id is None:
        speaker_id = dirname

    # if(len(prompt_files) < 1):
    #     print("Didn't find any prompt files.")
    #     exit()
    # else:
        # ensure one to one correspondence between wavs and prompts
    #     prompt_files = [os.path.join(dirname, filename) + '.txt'
    #                     for filename in filenames]

    # uti_files = [os.path.join(dirname, filename) + '.ult'
    #              for filename in filenames]

    cursor = 0.0

    # find params from first recording
    fs = recordings[0].modalities['MonoAudio'].meta['wav_fs']

    # TODO: Instead of this do the usual exclusion file commandline option
    # na_file = os.path.join(dirname, 'na_list.txt')
    # if os.path.isfile(na_file):
    #     na_list = [line.rstrip('\n') for line in open(na_file)]
    # else:
    #     na_list = []
    #     print("Didn't find na_list.txt. Proceeding anyhow.")

    outwave = dirname + ".wav"
    outfav = dirname + ".txt"
    outcsv = dirname + ".csv"
    outtextgrid = dirname + ".TextGrid"

    # initialise table with the speaker_id and name repeated and other fields empty
    table = [{'id': 'n/a',
              'speaker': speaker_id,
              'sliceBegin': 'n/a',
              'begin': 'n/a',
              'end': 'n/a',
              'word': 'n/a'}
             for i in range(len(recordings))]

    data = None
    for (i, recording) in enumerate(recordings):
        # TODO: do we need to do exclusions here?
        # if filenames[i] in na_list:
        #     print('Skipping' + recording.meta['basename'] + ': Token is in na_list.txt.')
        #     continue
        # elif not os.path.isfile(uti_files[i]):
        #     print('Skipping ' + filenames[i] +
        #           '. Token has no ultrasound data.')
        #     continue

        # if prompt == 'water swallow' or line == 'BITE PLANE':
        #     print('Skipping' + prompt_files[i] + line)
        #     continue
        # else:
        table[i]['word'] = recording.meta['prompt']

        if fs != recording.modalities['MonoAudio'].meta['wav_fs']:
            print('Mismatched sample rates in sound files.')
            print('Exiting.')
            sys.exit()

        duration = recording.modalities['MonoAudio'].timevector[-1]

        # this rather than full path to avoid upsetting praat/FAV
        table[i]['id'] = recording.meta['basename']

        table[i]['sliceBegin'] = cursor

        # give fav the stuff from 1.5s after the audio recording begins
        table[i]['begin'] = cursor + 1.5

        cursor += duration
        table[i]['end'] = round(cursor, 3)

        if data is None:
            data = recording.modalities['MonoAudio'].data
        else:
            data = np.concatenate(data, recording.modalities['MonoAudio'].data)

    sio_wavfile.write(outwave, fs, data)
    # Weed out the skipped ones before writing the data out.
    table = [token for token in table if token['id'] != 'n/a']
    write_fav_input(table, outfav)
    write_results(table, outcsv)
    write_textgrid(table, outtextgrid)
    # pp.pprint(table)


def write_fav_input(table, filename):
    """
    Write a .csv file to be used as input to FAV.

    The file saved here along with the concatenated .wav are needed for 
    running the FAV forced aligner.

    Arguments:
    table -- list of dicts containing the metadata
    filename -- name of the file to be written
    """
    with closing(open(filename, 'w')) as csvfile:
        fieldnames = ['id', 'speaker', 'begin', 'end', 'word']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames,
                                delimiter='\t', quoting=csv.QUOTE_NONE,
                                extrasaction='ignore')

        map(writer.writerow, table)

    print("Wrote file " + filename + " for FAVE align.")


def write_results(table, filename):
    """
    Save the metadata for later chopping up the concatanated .wav.

    This file is richer than the corresponding one for FAV input and should
    be the one read for later analysis instead of that one.

    Arguments:
    table -- list of dicts containing the metadata
    filename -- name of the file to be written
    """
    with closing(open(filename, 'w')) as csvfile:
        fieldnames = ['id', 'speaker', 'sliceBegin',
                      'beep', 'begin', 'end', 'word']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames,
                                quoting=csv.QUOTE_NONNUMERIC)

        writer.writeheader()
        map(writer.writerow, table)

    print("Wrote file " + filename + " for R/Python.")


def write_textgrid(table, outtextgrid):
    print("didn't know how to write a textgrid yet.")
    print(table)
    print(outtextgrid)
