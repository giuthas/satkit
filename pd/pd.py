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

from contextlib import closing

# Built in packages
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
import scipy.io as sio
import scipy.io.wavfile as sio_wavfile
from scipy.signal import butter, filtfilt, kaiser, sosfilt

# Scientific plotting
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

pd_logger = logging.getLogger('pd')    

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


def high_pass(fs):
    stop = (50/(fs/2)) # 50 Hz stop band    
    b, a = butter(10, stop, 'highpass')
    return(b, a)


def band_pass(fs):
    nyq = 0.5 * fs
    low = 950.0 / nyq
    high = 1050.0 / nyq
    sos = butter(1, [low, high], btype='band', output='sos')
    return(sos)


def beep_detect(frames, fs, b, a, name):
    hp_signal = filtfilt(b, a, frames)
    sos = band_pass(fs)
    bp_signal = sosfilt(sos, frames)
    bp_signal = sosfilt(sos, bp_signal[::-1])[::-1]
    n = len(hp_signal)

    # 1 ms window
    window_length = int(0.001*fs)
    half_window_length = int(window_length/2)

    # pad with zeros at both ends
    padded_signal = np.zeros(n + window_length)
    padded_signal[half_window_length : half_window_length+n] = \
        np.square(hp_signal) # squared already for rms, r&m later
    padded_signal2 = np.zeros(n + window_length)
    padded_signal2[half_window_length : half_window_length+n] = \
        np.square(bp_signal) # squared already for rms, r&m later
    
    # square windowed samples
    wind_signal = np.zeros((n, window_length)) 
    bp_wind_signal = np.zeros((n, window_length)) 
    for i in range(window_length):
        wind_signal[:,i] = padded_signal[i:i+n]
        bp_wind_signal[:,i] = padded_signal2[i:i+n]

    # kaiser windowed samples
    intensity_window = kaiser(window_length, 20) # copied from praat
    # multiply each window slice with the window 
    wind_signal = np.dot(wind_signal,np.diag(intensity_window)) 
    bp_wind_signal = np.dot(bp_wind_signal,np.diag(intensity_window)) 

    # The signal is already squared, need to only take mean and root.
    int_signal = 10*np.log(np.sqrt(np.mean(wind_signal, 1)))
    bp_int_signal = 10*np.log(np.sqrt(np.mean(bp_wind_signal, 1)))
    
    # Old int_time was used to almost correct the shift caused by windowing. 
    #int_time = np.linspace(0, float(len(hp_signal) + 
    # (window_length%2 - 1)/2.0)/fs, len(int_signal))
    int_time = np.linspace(0, float(len(hp_signal))/fs, len(hp_signal))
    int_signal[int_time < 1] = -80

    # First form a rough estimate of where the beep is by detecting the first 
    # big rise in the band passed signal.
    threshold_bp = .9*max(bp_int_signal) + .1*min(bp_int_signal)
    bp_spike_indeces = np.where(bp_int_signal > threshold_bp)
    bp_beep = int_time[bp_spike_indeces[0]]

    # Search for the actual beep in the area from beginning of the recording to 
    # 25 ms before and after where band passing thinks the beep begins.
    roi_beg = bp_spike_indeces[0][0] - int(0.025*fs)
    roi_end = bp_spike_indeces[0][0] + int(0.025*fs)

    # Find the first properly rising edge in the 50 ms window.
    threshold = .1*min(frames[0:roi_end])
    candidates = np.where(frames[roi_beg:roi_end] < threshold)[0]
    beep_approx_index = roi_beg + candidates[0]
    beep_approx = int_time[beep_approx_index]

    zero_crossings = np.where(np.diff(np.signbit(frames[beep_approx_index:roi_end])))[0]
    beep_index = beep_approx_index + zero_crossings[0] + 1 - int(.001*fs)
    beep = int_time[beep_index]

    # check if the energy before the beep begins is less 
    # than the energy after the beep.
    split_point = beep_index + int(.075*fs)
    if len(hp_signal) > split_point:
        ave_energy_pre_beep = np.sum(int_signal[:beep_index])/beep_index
        ave_speech_energy = np.sum(int_signal[split_point:])/(len(int_signal)-split_point)
        has_speech = ave_energy_pre_beep < ave_speech_energy

    else:
        # if the signal is very very short, there is no speech
        has_speech = False

    return (beep, has_speech)


def read_wav(filename):
    samplerate, frames = sio_wavfile.read(filename)
    #duration = frames.shape[0] / samplerate
    b, a = high_pass(samplerate)
        
    beep_time, has_speech = beep_detect(frames, samplerate, b, a, filename)

    return(frames, beep_time, has_speech, samplerate)


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

    # this is equivalent with the following: sorted(glob.glob(directory + '/.' +  '/*US.txt'))
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
        ult_meta_file = os.path.join(directory, base_names[i] + "US.txt")
        ult_wav_file = os.path.join(directory, base_names[i] + ".wav")
        ult_file = os.path.join(directory, base_names[i] + ".ult")

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

    (ult_wav_frames, beep_uti, has_speech, ult_wav_fs) = read_wav(token['ult_wav_file'])

    # Yes, uses a function that is supposed to be hidden. Planning on
    # making this function the actual interface.
    meta = parse_ult_meta(token['ult_meta_file'])
    ult_fps = meta['FramesPerSec']
    ult_NumVectors = meta['NumVectors']
    ult_PixPerVector = meta['PixPerVector']
    t_first_frame = meta['TimeInSecsOfFirstFrame']

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
    ultra_time = ultra_time + t_first_frame + .5/ult_fps

    ult_wav_time = np.linspace(0, len(ult_wav_frames), 
                               len(ult_wav_frames), endpoint=False)/ult_wav_fs
        
    data = {}
    data['pd'] = ultra_d
    data['sbpd'] = slw_pd
    data['ultra_time'] = ultra_time
    data['beep_uti'] = beep_uti

    return data
        

