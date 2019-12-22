from contextlib import closing
from datetime import datetime

import csv
import glob
import os
import pprint
import re
import wave
import struct
import sys
import time
import numpy as np
import matplotlib.pyplot as plt
import scipy.io as sio
from scipy.signal import butter, filtfilt, kaiser, sosfilt
from scikits.audiolab import Sndfile, Format

from matplotlib.backends.backend_pdf import PdfPages


def plot_signals_trace(beep, beep2, int_time, int_signal, hp_signal, bp_signal, int_signal2):
    fig = plt.figure()
    ax0 = fig.add_subplot(211)
    ax1 = fig.add_subplot(212)
    ax0.plot(int_time, int_signal)
    ax0.plot(int_time, int_signal2)
    y = [20, -200]
    ax0.plot([beep, beep], y, color="g")
    ax0.plot([beep2, beep2], y, color="r")
    ax1.plot(int_time, hp_signal)
    ax1.plot(int_time, bp_signal)
    ax1.plot([beep, beep], [-1, 1], color="g")
    ax1.plot([beep2, beep2], [-1, 1], color="r")
    plt.show()


# Wrapper for plotting, which also cals plt.show().
def plot_and_show(beep, ultra_d, ultra_time, uti_wav, uti_wav_time, beep_uti, center, name):
    plot_signals(beep, ultra_d, ultra_time, uti_wav, uti_wav_time, beep_uti, center, name)
    plt.show()


# To be used in silent plotting or called for plotting when calling plt.show() separately.
def plot_signals(beep, ultra_d, ultra_time, uti_wav, uti_wav_time, beep_uti, center, name):
    fig = plt.figure(figsize=(12, 10))
    
    ax1 = plt.subplot2grid((6,1),(2,0), rowspan=2)
    ax2 = plt.subplot2grid((6,1),(4,0))

    ultra_time = ultra_time - beep_uti
    uti_wav_time = uti_wav_time - beep_uti

    xlim = (-.2, 1)
#    xlim = (-4, 6)

    ax1.plot(ultra_time, ultra_d)
    ax1.axvline(x=0, color="r")
    if center:
        ax1.set_xlim(xlim)
    ax1.set_ylabel("Pixel Difference")

    ax2.plot(uti_wav_time, uti_wav)
    ax2.axvline(x=0, color="r")
    if center:
        ax2.set_xlim(xlim)
    ax3.set_ylabel("Waveform")
    ax3.set_xlabel("Time (s)")

    plt.suptitle(name, fontsize=24)
    #plt.tight_layout()


#
# Used for verifying test runs at the moment. Wrap later into it's own thing.
#
def draw_spaghetti(meta, data):
    with PdfPages('spaghetti_plot.pdf') as pdf:
        plt.figure(figsize=(7, 7))
        #ax = plt.subplot2grid((2,1),(1,0))
        ax = plt.axes()
        xlim = (-.2, 1)

        for i in xrange(len(data)):
            ultra_time = data[i]['ultra_time'] - data[i]['beep_uti']

            ax.plot(ultra_time, data[i]['pd'], color="b", lw=1, alpha=.2)
            ax.axvline(x=0, color="r", lw=1)
            ax.set_xlim(xlim)
            ax.set_ylabel("Pixel Difference")
            ax.set_xlabel("Time (s), go-signal at 0 s.")

        plt.tight_layout()
        pdf.savefig()  # saves the current figure into a pdf page
        plt.close()
    


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
        date = datetime.strptime(lines[1], '%d/%m/%Y %H:%M:%S')
        participant = lines[2].split(',')[0]

        return(prompt, date, participant)


def read_file_exclusion_list(filename):
    if filename is not None:
        with closing(open(filename, 'rb')) as csvfile:
            reader = csv.reader(csvfile, delimiter='\t')
            # Throw away the second field - it is a comment for human readers.
            exclusion_list = [row[0] for row in reader]
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

    # pad with zeros at both ends
    padded_signal = np.zeros(n + window_length)
    padded_signal[window_length/2 : window_length/2+n] = \
        np.square(hp_signal) # squared already for rms, r&m later
    padded_signal2 = np.zeros(n + window_length)
    padded_signal2[window_length/2 : window_length/2+n] = \
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

    # Test section
    #plot_signals(beep, bp_beep[0], int_time, int_signal, hp_signal, bp_signal, bp_int_signal)


    # An even fancier version could let the user point to the beep etc.
    # But not necessarily a good idea as it's more likely that the threshold 
    # values just need adjusting in general than for one token.

#
# Commented out cause not needed for the Ultrafest 2017 data.
#
    #if not has_speech:
    #    print "Token ", name, " did not seem to have any speech in it."
    #    plot_signals_trace(beep, bp_beep[0], int_time, int_signal, hp_signal, bp_signal, bp_int_signal)
    #    answer = raw_input("Exclude the token (y/n):")
    #    if answer == "n":
    #        print "Warning: Including the token, but there will probably" 
    #        print "be problems in later processing stages."
    #        has_speech = True

    return (beep, has_speech)


def read_wav(filename):
    with closing(Sndfile(filename, 'r')) as w:
        uti_wav_fs = w.samplerate
        b_uti, a_uti = high_pass(uti_wav_fs)
        
        channels = w.channels
        format = w.format
        
        n_frames = w.nframes
        duration = n_frames / float(uti_wav_fs)
        uti_wav_frames = w.read_frames(n_frames)
        
        beep_uti, has_speech = beep_detect(uti_wav_frames, uti_wav_fs, b_uti, a_uti, filename)

        return(uti_wav_frames, beep_uti, has_speech, uti_wav_fs)


def read_uti_meta(filename):
    with closing(open(filename, 'r')) as metafile:
        meta = {}
        for line in metafile:
            (key, value_str) = line.split("=")
            try:
                value = int(value_str)
            except ValueError:
                value = float(value_str)
            meta[key] = value

        return(meta["FramesPerSec"], meta["NumVectors"], meta["PixPerVector"], meta["TimeInSecsOfFirstFrame"])


def get_token_list_from_dir(directory, exclusion_list_name):
    file_exclusion_list = read_file_exclusion_list(exclusion_list_name)

    uti_meta_files = sorted(glob.glob(directory + '/*US.txt'))
    uti_prompt_files = [prompt_file 
                        for prompt_file in glob.glob(directory + '/*.txt') 
                        if not prompt_file in uti_meta_files
                        ]
    uti_prompt_files = sorted(uti_prompt_files)
    wav_files = sorted(glob.glob(directory + '/*.wav')) 
    uti_files = sorted(glob.glob(directory + '/*.ult'))


    filenames = [filename.split('.')[-2].split('/').pop() 
                 for filename in uti_prompt_files]    

    meta = [{'filename': filename} for filename in filenames] 
    for i in xrange(0, len(filenames)):
        meta[i]['uti_meta_file'] = uti_meta_files[i]
        meta[i]['uti_prompt_file'] = uti_prompt_files[i]
        meta[i]['uti_wav_file'] = wav_files[i]
        meta[i]['uti_file'] = uti_files[i]
        (meta[i]['prompt'], meta[i]['date'], meta[i]['participant']) = read_prompt(uti_prompt_files[i])

    meta = sorted(meta, key=lambda token: token['date'])
    meta = [token 
            for token in meta 
            if not ('water swallow' in token['prompt'] or 'bite plate' in token['prompt'])
            ]

    data = [{} for token in meta]
    for i in xrange(0,len(meta)):
        print i, meta[i]
        if meta[i]['filename'] in file_exclusion_list:
            print meta[i]['filename'], "/", uti_files[i], "is in the exclusion list."
            meta[i]['exclusion'] = True
        else:
            meta[i]['exclusion'] = False

    return meta


def pd(token):
    (uti_wav_frames, beep_uti, has_speech, uti_wav_fs) = read_wav(token['uti_wav_file'])
    (uti_fps, uti_NumVectors, uti_PixPerVector, t_first_frame) = read_uti_meta(token['uti_meta_file'])

    with closing(open(token['uti_file'], 'rb')) as uti_file:
        uti_data = uti_file.read()
        ultra = np.fromstring(uti_data, dtype=np.uint8)
        ultra = ultra.astype("float32")
        
        uti_no_frames = len(ultra)/(uti_NumVectors*uti_PixPerVector)
        # reshape into vectors containing a frame each
        ultra = ultra.reshape((uti_no_frames, uti_NumVectors, uti_PixPerVector))
            
        ultra_diff = np.diff(ultra, axis=0)
        ultra_diff = np.square(ultra_diff)
        slw_pd = np.sum(ultra_diff, axis=2)
        ultra_d = np.sqrt(np.sum(slw_pd, axis=1))
            
    print "UTI:", token['filename'], token['prompt']

    ultra_time = np.linspace(0, len(ultra_d), len(ultra_d), endpoint=False)/uti_fps
    ultra_time = ultra_time + t_first_frame + .5/uti_fps

    uti_wav_time = np.linspace(0, len(uti_wav_frames), 
                               len(uti_wav_frames), endpoint=False)/uti_wav_fs
        
    data = {}
    data['pd'] = ultra_d
    data['ultra_time'] = ultra_time
    data['beep_uti'] = beep_uti

    return data
        

