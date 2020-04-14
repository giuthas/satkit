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
import logging

# Numpy and scipy
import numpy as np
from scipy.signal import butter, filtfilt, kaiser, sosfilt


_audio_logger = logging.getLogger('sap.audio')    


def high_pass_50(fs):
    """Returns a high-pass filter with a 50Hz stop band. Used for
    filtering the mains frequency away from recorded sound.""" 
    _audio_logger.debug("Generating high-pass filter.")
    stop = (50/(fs/2)) # 50 Hz stop band    
    b, a = butter(10, stop, 'highpass')
    return(b, a)


def band_pass(fs):
    _audio_logger.debug("Generating band-pass filter.")
    nyq = 0.5 * fs
    low = 950.0 / nyq
    high = 1050.0 / nyq
    sos = butter(1, [low, high], btype='band', output='sos')
    return(sos)


def detect_beep_and_speech(frames, fs, b, a, name):

    _audio_logger.debug("Detecting beep onset and presence of speech in " + name + ".")
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


