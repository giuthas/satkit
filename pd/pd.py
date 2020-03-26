#
# Copyright (c) 2019-2020 Pertti Palo.
#
# This file is part of Pixel Difference toolkit 
# (see https://github.com/giuthas/pd/).
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

# Built in packages
from contextlib import closing
import csv
import glob
import json
import logging
import os
import os.path
import pickle
import re
import struct
import sys
import time

# Numpy and scipy
import numpy as np
import scipy.io.wavfile as sio_wavfile

# Scientific plotting
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# local modules
import pd.audio as pd_audio


pd_logger = logging.getLogger('pd.pd')    

def save2pickle(data, filename):
    with closing(open(filename, 'bw')) as outfile:
        pickle.dump(data, outfile)


def load_pickled_data(filename):
    """
    Loads a (token_metadata_list, data) tuple from a .pickle file and
    returns the tuple.

    """
    data = None
    with closing(open(filename, 'br')) as infile:
        data = pickle.load(infile)

    return data


def save2json(data, filename):
    """
    THIS FUNCTION HAS NOT BEEN IMPLEMENTED YET.
    """
    # Can possibly be implemented with something like the example below
    # (see also
    # https://stackoverflow.com/questions/26646362/numpy-array-is-not-json-serializable)
    # but to be used as a save-load pair, this will also need Decoder to interpret
    # json to numpy.
    #
    # class NumpyEncoder(json.JSONEncoder):
    #     def default(self, obj):
    #         if isinstance(obj, np.ndarray):
    #             return obj.tolist()
    #         return json.JSONEncoder.default(self, obj)
        
    # a = np.array([[1, 2, 3], [4, 5, 6]])
    # print(a.shape)
    # json_dump = json.dumps({'a': a, 'aa': [2, (2, 3, 4), a], 'bb': [2]}, cls=NumpyEncoder)
    # print(json_dump)

    with closing(open(filename, 'w')) as outfile:
        json.dump(data, outfile)


def load_json_data(filename):
    """
    THIS FUNCTION HAS NOT BEEN IMPLEMENTED YET.
    """
    data = None
    with closing(open(filename, 'r')) as infile:
        data = json.load(infile)

    return data


def write_csv(meta, filename):
    # Finally dump all the metadata into a csv-formated file.
    with closing(open(filename, 'w')) as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=meta[0].keys())

        writer.writeheader()
        map(writer.writerow, meta)



def save_prompt_freq(prompt_freqs):
    with closing(open('prompt_freqs.csv', 'w')) as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['prompt', 'frequency'])
        for prompt in sorted(prompt_freqs.keys()):
            writer.writerow([prompt, prompt_freqs[prompt]])


def read_prompt(filename):
    with closing(open(filename, 'r')) as promptfile:
        lines = promptfile.read().splitlines()
        prompt = lines[0]
        date = lines[1]
        # could also do datetime as below, but there doesn't seem to be any reason to so.
        #date = datetime.strptime(lines[1], '%d/%m/%Y %H:%M:%S')
        participant = lines[2].split(',')[0]

        return(prompt, date, participant)


def read_file_exclusion_list(filename):
    if filename is not None:
        with closing(open(filename, 'r')) as csvfile:
            reader = csv.reader(csvfile, delimiter='\t')
            # Throw away the second field - it is a comment for human readers.
            exclusion_list = [row[0] for row in reader]
            pd_logger.info('Read exclusion list ' + filename + ' with ' +
                           str(len(exclusion_list)) + ' names.')
    else:
        exclusion_list = []

    return exclusion_list


def parse_ult_meta(filename):
    """Return all metadata from AAA txt as dictionary."""
    with closing(open(filename, 'r')) as metafile:
        meta = {}
        for line in metafile:
            (key, value_str) = line.split("=")
            try:
                value = int(value_str)
            except ValueError:
                value = float(value_str)
            meta[key] = value

        return meta


def get_token_list_from_dir(directory, exclusion_list_name):

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

    base_names = [os.path.splitext(prompt_file)[0] for prompt_file in ult_prompt_files]
    meta = [{'base_name': base_name} for base_name in base_names] 

    for i in range(0, len(base_names)):
        # Prompt file should always exist and correspond to the base_name because 
        # the base_name list is generated from the directory listing of prompt files.
        meta[i]['ult_prompt_file'] = ult_prompt_files[i]
        (prompt, date, participant) = read_prompt(ult_prompt_files[i])
        meta[i]['prompt'] = prompt
        meta[i]['date'] = date
        meta[i]['participant'] = participant

        if meta[i]['base_name'] in file_exclusion_list:
            notice = meta[i]['base_name'] + " is in the exclusion list."
            pd_logger.info(notice)
            meta[i]['excluded'] = True
        else:
            meta[i]['excluded'] = False

        # Candidates for filenames. Existence tested below.
        ult_meta_file = os.path.join(base_names[i] + "US.txt")
        ult_wav_file = os.path.join(base_names[i] + ".wav")
        ult_file = os.path.join(base_names[i] + ".ult")

        if os.path.isfile(ult_meta_file):
            meta[i]['ult_meta_file'] = ult_meta_file
            meta[i]['ult_meta_exists'] = True
        else: 
            notice = 'Note: ' + ult_meta_file + " does not exist."
            pd_logger.warning(notice)
            meta[i]['ult_meta_exists'] = False
            meta[i]['excluded'] = True
            
        if os.path.isfile(ult_wav_file):
            meta[i]['ult_wav_file'] = ult_wav_file
            meta[i]['ult_wav_exists'] = True
        else:
            notice = 'Note: ' + ult_wav_file + " does not exist."
            pd_logger.warning(notice)
            meta[i]['ult_wav_exists'] = False
            meta[i]['excluded'] = True
            
        if os.path.isfile(ult_file):
            meta[i]['ult_file'] = ult_file
            meta[i]['ult_exists'] = True
        else:
            notice = 'Note: ' + ult_file + " does not exist."
            pd_logger.warning(notice)
            meta[i]['ult_exists'] = False
            meta[i]['excluded'] = True        

        if 'water swallow' in prompt:
            notice = 'Note: ' + base_names[i] + ' prompt is a water swallow.'
            pd_logger.info(notice)
            meta[i]['type'] = 'water swallow'
            meta[i]['excluded'] = True        
        elif 'bite plate' in prompt:
            notice = 'Note: ' + base_names[i] + ' prompt is a bite plate.'
            pd_logger.info(notice)
            meta[i]['type'] = 'bite plate'
            meta[i]['excluded'] = True        
        else:
            meta[i]['type'] = 'regular trial'


    meta = sorted(meta, key=lambda token: token['date'])

    return meta


def pd(token):
    if token['excluded']:
        pd_logger.info("PD: " + token['base_name'] + " " + token['prompt'] + '. Token excluded.')
        return None
    else:
        pd_logger.info("PD: " + token['base_name'] + " " + token['prompt'] + '. Token processed.')

    (ult_wav_fs, ult_wav_frames) = sio_wavfile.read(token['ult_wav_file'])
    # setup the high-pass filter for removing the mains frequency from the recorded sound.
    b, a = pd_audio.high_pass_50(ult_wav_fs)
    beep_uti, has_speech = pd_audio.detect_beep_and_speech(ult_wav_frames,
                                                           ult_wav_fs,
                                                           b, a,
                                                           token['ult_wav_file'])
    
    meta = parse_ult_meta(token['ult_meta_file'])
    ult_fps = meta['FramesPerSec']
    ult_NumVectors = meta['NumVectors']
    ult_PixPerVector = meta['PixPerVector']
    ult_TimeInSecsOfFirstFrame = meta['TimeInSecsOfFirstFrame']

    with closing(open(token['ult_file'], 'rb')) as ult_file:
        ult_data = ult_file.read()
        ultra = np.fromstring(ult_data, dtype=np.uint8)
        ultra = ultra.astype("float32")
        
        ult_no_frames = int(len(ultra)/(ult_NumVectors*ult_PixPerVector))
        # reshape into vectors containing a frame each
        ultra = ultra.reshape((ult_no_frames, ult_NumVectors, ult_PixPerVector))
            
        ultra_diff = np.diff(ultra, axis=0)
        ultra_diff = np.square(ultra_diff)
        slw_pd = np.sum(ultra_diff, axis=2)
        ultra_d = np.sqrt(np.sum(slw_pd, axis=1))
            
    ultra_time = np.linspace(0, len(ultra_d), len(ultra_d), endpoint=False)/ult_fps
    ultra_time = ultra_time + ult_TimeInSecsOfFirstFrame + .5/ult_fps

    ult_wav_time = np.linspace(0, len(ult_wav_frames), 
                               len(ult_wav_frames), endpoint=False)/ult_wav_fs
        
    data = {}
    data['pd'] = ultra_d
    data['sbpd'] = slw_pd
    data['ultra_time'] = ultra_time
    data['beep_uti'] = beep_uti

    return data
        

