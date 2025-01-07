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

# Built in packages
import logging

# Numpy and scipy
import numpy as np
from scipy.signal import butter, filtfilt, sosfilt
from scipy.signal.windows import kaiser

_audio_logger = logging.getLogger('satkit.audio')


def high_pass_50(sampling_frequency):
    """Returns a high-pass filter with a 50Hz stop band. Used for
    filtering the mains frequency away from recorded sound."""
    _audio_logger.debug("Generating high-pass filter.")
    stop = 50/(sampling_frequency/2)  # 50 Hz stop band
    b, a = butter(10, stop, 'highpass')
    return (b, a)


def high_pass(sampling_frequency, stop_band):
    """Returns a high-pass filter with a stop band of sb. Used for
    filtering the mains frequency away from recorded sound."""
    _audio_logger.debug("Generating high-pass filter.")
    stop = stop_band/(sampling_frequency/2)
    b, a = butter(10, stop, 'highpass')
    return {'b': b, 'a': a}


def band_pass(sampling_frequency):
    """Generate a band pass filter for detecting a 1kHz signal."""
    _audio_logger.debug("Generating band-pass filter.")
    nyq = 0.5 * sampling_frequency
    low = 950.0 / nyq
    high = 1050.0 / nyq
    sos = butter(1, [low, high], btype='band', output='sos')
    return sos


class MainsFilter():
    """
    Class for containing a general mains filter.

    This exists so that the mains filter does not need to be regenerated every
    time audio is read.
    """
    mains_frequency: float = None
    mains_filter: dict = {'b': None, 'a': None}

    @staticmethod
    def generate_mains_filter(sampling_frequency: float,
                              mains_frequency: float):
        """
        Generate a filter for removing the mains frequency from audio.

        Parameters
        ----------
        sampling_frequency : float
            Sampling frequency of the audio data.
        mains_frequency : float
            Mains frequency of the recording location. In Europe usually 50Hz,
            in North America usually 60Hz.
        """
        MainsFilter.mains_frequency = mains_frequency
        MainsFilter.mains_filter = high_pass(
            sampling_frequency, mains_frequency)


def detect_beep_and_speech(frames, sampling_frequency, b, a, name):
    """
    Find a 1kHz 50ms beep at the beginning of a sound sample.

    This functions is for processing delayed naming data
    where the go-signal is a 1kHz 50ms beep. The algorithm assumes
    that the signal is the first properly detectable sound in
    the sample and also that it starts with a rising edge.
    The detection is based on locating the first negative
    valued half wave (the second half wave) and working backwards
    from that using zero crossings and wave duration to pinpoint
    the onset.

    Parameters:
    frames: the sound sample
    sampling_frequency: the sampling frequency of the sound sample
    b and a: high pass filter parameters to remove the electrical
        mains' interference
    name: name identifying the sample. Usually the filename.
1    """

    _audio_logger.debug(
        "Detecting beep onset and presence of speech in %s.", name)
    hp_signal = filtfilt(b, a, frames)
    sos = band_pass(sampling_frequency)
    bp_signal = sosfilt(sos, frames)
    bp_signal = sosfilt(sos, bp_signal[::-1])[::-1]
    signal_length = len(hp_signal)

    # 1 ms window
    window_length = int(0.001*sampling_frequency)
    half_window_length = int(window_length/2)

    # pad with zeros at both ends
    padded_signal = np.zeros(signal_length + window_length)
    padded_signal[half_window_length: half_window_length+signal_length] = \
        np.square(hp_signal)  # squared already for rms, r&m later
    padded_signal2 = np.zeros(signal_length + window_length)
    padded_signal2[half_window_length: half_window_length+signal_length] = \
        np.square(bp_signal)  # squared already for rms, r&m later

    # square windowed samples
    wind_signal = np.zeros((signal_length, window_length))
    bp_wind_signal = np.zeros((signal_length, window_length))
    for i in range(window_length):
        wind_signal[:, i] = padded_signal[i:i+signal_length]
        bp_wind_signal[:, i] = padded_signal2[i:i+signal_length]

    # kaiser windowed samples
    intensity_window = kaiser(window_length, 20)  # copied from praat
    # multiply each window slice with the window
    wind_signal = np.dot(wind_signal, np.diag(intensity_window))
    bp_wind_signal = np.dot(bp_wind_signal, np.diag(intensity_window))

    # The signal is already squared, need to only take mean and root.
    int_signal = 10*np.log(np.sqrt(np.mean(wind_signal, 1)))
    bp_int_signal = 10*np.log(np.sqrt(np.mean(bp_wind_signal, 1)))

    # Old int_time was used to almost correct the shift caused by windowing.
    # int_time = np.linspace(0, float(len(hp_signal) +
    # (window_length%2 - 1)/2.0)/fs, len(int_signal))
    int_time = np.linspace(
        0, float(len(hp_signal))/sampling_frequency, len(hp_signal))
    int_signal[int_time < 1] = -80

    # First form a rough estimate of where the beep is by detecting the first
    # big rise in the band passed signal.
    threshold_bp = .9*max(bp_int_signal) + .1*min(bp_int_signal)
    bp_spike_indeces = np.where(bp_int_signal > threshold_bp)
    # bp_beep = int_time[bp_spike_indeces[0]]

    # Search for the actual beep in the area from beginning of the recording to
    # 25 ms before and after where band passing thinks the beep begins.
    roi_beg = bp_spike_indeces[0][0] - int(0.025*sampling_frequency)
    roi_end = bp_spike_indeces[0][0] + int(0.025*sampling_frequency)

    # Find the first properly rising edge in the 50 ms window.
    threshold = .1*min(frames[0:roi_end])
    candidates = np.where(frames[roi_beg:roi_end] < threshold)[0]
    if not len(candidates) > 0:
        _audio_logger.error("Found no beep in %s.", name)
        return (0, False)
    beep_approx_index = roi_beg + candidates[0]
    # beep_approx = int_time[beep_approx_index]

    zero_crossings = np.where(
        np.diff(np.signbit(frames[beep_approx_index:roi_end])))[0]
    beep_index = beep_approx_index + \
        zero_crossings[0] + 1 - int(.001*sampling_frequency)
    beep = int_time[beep_index]

    # check if the energy before the beep begins is less
    # than the energy after the beep.
    split_point = beep_index + int(.075*sampling_frequency)
    if len(hp_signal) > split_point:
        ave_energy_pre_beep = np.sum(int_signal[:beep_index])/beep_index
        ave_energy_post_beep = np.sum(
            int_signal[split_point:])/(len(int_signal)-split_point)
        has_speech = ave_energy_pre_beep < ave_energy_post_beep
    else:
        # if the signal is very very short, there is no speech
        has_speech = False

    return (beep, has_speech)
