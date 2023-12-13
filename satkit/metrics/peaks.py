#
# Copyright (c) 2019-2023
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
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple, Union

import numpy as np

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from scipy import signal as scipy_signal

from satkit.data_structures import Recording
from satkit.constants import TimeseriesNormalisation


@dataclass
class PeakData:
    """Peaks, their times, and properties as returned by scipy's find_peaks."""
    peaks: np.ndarray
    peak_times: np.ndarray
    properties: dict


def time_series_peaks(
        data: np.ndarray,
        time: np.ndarray,
        time_lim: Tuple[float, float],
        normalise: TimeseriesNormalisation = 'NONE',
        number_of_ignored_frames: int = 10,
        distance: Optional[int] = 10,
        prominence: Optional[float] = 0.05):

    search_data = data[number_of_ignored_frames:]
    search_time = time[number_of_ignored_frames:]

    indeces = np.nonzero(
        (search_time > time_lim[0]) & (search_time < time_lim[1]))
    search_data = search_data[indeces]
    search_time = search_time[indeces]

    if normalise in (TimeseriesNormalisation.both, TimeseriesNormalisation.bottom):
        search_data = search_data - np.min(search_data)
    if normalise in [TimeseriesNormalisation.both, TimeseriesNormalisation.peak]:
        search_data = search_data/np.max(search_data)

    peaks, properties = scipy_signal.find_peaks(
        search_data, distance=distance, prominence=prominence)

    peak_times = search_time[peaks]

    return PeakData(peaks, peak_times, properties)


def save_peaks(
    filename: str,
    recordings: List[Recording]
):
    """
    Save peak data to .csv files.

    Save both numbers/recording for each recording and the peak times themselves
    do this for unthresholded and thresholded peaks.
    """
    peak_ns = []
    unthresholded_peak_ns = np.zeros((len(recordings), 2))
    thresholded_peak_ns = np.zeros((len(recordings), 2))

    whole_to_bottom = None
    bottom_to_whole = None
    whole_to_bottom_thresholded = None
    bottom_to_whole_thresholded = None
    for i, recording in enumerate(recordings):
        if 'utterance' not in recording.satgrid:
            continue
        id = recording.basename
        prompt = recording.meta_data.prompt

        l1 = recording.modalities['PD l1 on RawUltrasound']
        l1_bottom = recording.modalities['PD l1 bottom on RawUltrasound']

        audio = recording.modalities['MonoAudio']
        stimulus_onset = audio.go_signal
        ultra_time = l1.timevector - stimulus_onset

        end_time = 0
        for interval in recording.satgrid['utterance']:
            if interval.text:
                end_time = interval.next.begin
                break

        time_lim = (0, end_time)

        peak_data = time_series_peaks(
            l1.data, ultra_time, time_lim=time_lim,
            normalise='PEAK AND BOTTOM', number_of_ignored_frames=None,
            distance=None, prominence=None)
        bottom_peak_data = time_series_peaks(
            l1_bottom.data, ultra_time, time_lim=time_lim,
            normalise='PEAK AND BOTTOM', number_of_ignored_frames=None,
            distance=None, prominence=None)
        peak_data_thresholded = time_series_peaks(
            l1.data, ultra_time, time_lim=time_lim,
            normalise='PEAK AND BOTTOM')
        bottom_peak_data_thresholded = time_series_peaks(
            l1_bottom.data, ultra_time, time_lim=time_lim,
            normalise='PEAK AND BOTTOM')

        ns = {
            'id': id,
            'prompt': prompt,
            'l1': len(peak_data.peaks),
            'l1_bottom': len(bottom_peak_data.peaks),
            'l1_thresholded': len(peak_data_thresholded.peaks),
            'l1_bottom_thresholded': len(bottom_peak_data_thresholded.peaks)
        }
        peak_ns.append(ns)
        unthresholded_peak_ns[i, 0] = len(peak_data.peaks)
        unthresholded_peak_ns[i, 1] = len(bottom_peak_data.peaks)
        thresholded_peak_ns[i, 0] = len(peak_data_thresholded.peaks)
        thresholded_peak_ns[i, 1] = len(bottom_peak_data_thresholded.peaks)

        if whole_to_bottom is None:
            whole_to_bottom = get_nearest_neighbours(
                peak_data.peak_times, bottom_peak_data.peak_times)
            bottom_to_whole = get_nearest_neighbours(
                bottom_peak_data.peak_times, peak_data.peak_times)
            whole_to_bottom_thresholded = get_nearest_neighbours(
                peak_data_thresholded.peak_times, bottom_peak_data_thresholded.peak_times)
            bottom_to_whole_thresholded = get_nearest_neighbours(
                bottom_peak_data_thresholded.peak_times, peak_data_thresholded.peak_times)
        else:
            whole_to_bottom = np.append(whole_to_bottom, get_nearest_neighbours(
                peak_data.peak_times, bottom_peak_data.peak_times), axis=0)
            bottom_to_whole = np.append(bottom_to_whole, get_nearest_neighbours(
                bottom_peak_data.peak_times, peak_data.peak_times), axis=0)
            whole_to_bottom_thresholded = np.append(
                whole_to_bottom_thresholded,
                get_nearest_neighbours(
                    peak_data_thresholded.peak_times,
                    bottom_peak_data_thresholded.peak_times),
                axis=0)
            bottom_to_whole_thresholded = np.append(
                bottom_to_whole_thresholded,
                get_nearest_neighbours(
                    bottom_peak_data_thresholded.peak_times,
                    peak_data_thresholded.peak_times),
                axis=0)

    peak_n_file = filename + '_peak_n.csv'

    with open(peak_n_file, "w") as csv_file:
        writer = csv.DictWriter(csv_file, ns.keys(), delimiter=',')
        writer.writeheader()
        for line in peak_ns:
            writer.writerow(line)

    whole_to_bottom_file = filename + '_whole_to_bottom.csv'
    bottom_to_whole_file = filename + '_bottom_to_whole.csv'
    whole_to_bottom_thresholded_file = filename + '_whole_to_bottom_thresholded.csv'
    bottom_to_whole_thresholded_file = filename + '_bottom_to_whole_thresholded.csv'
    np.savetxt(whole_to_bottom_file, whole_to_bottom, fmt='%.8f',
               delimiter=',', header="whole,bottom", comments="")
    np.savetxt(bottom_to_whole_file, bottom_to_whole, fmt='%.8f',
               delimiter=',', header="bottom,whole", comments="")
    np.savetxt(
        whole_to_bottom_thresholded_file, whole_to_bottom_thresholded,
        fmt='%.8f', delimiter=',',
        header="whole_thresholded,bottom_thresholded", comments="")
    np.savetxt(
        bottom_to_whole_thresholded_file, bottom_to_whole_thresholded,
        fmt='%.8f', delimiter=',',
        header="bottom_thresholded,whole_thresholded", comments="")

    plot_peak_ns(unthresholded_peak_ns, thresholded_peak_ns)
    plot_peak_comparison(whole_to_bottom, bottom_to_whole,
                         whole_to_bottom_thresholded,
                         bottom_to_whole_thresholded)


def get_nearest_neighbours(array1: np.ndarray, array2: np.ndarray):
    neighbours = np.zeros((array1.size, 2))
    neighbours[:, 0] = array1
    for i, element in enumerate(array1):
        diff = np.abs(array2-element)
        neighbours[i, 1] = array2[np.argmin(diff)]

    return neighbours


def plot_peak_ns(unthresholded_peak_ns, thresholded_peak_ns):
    pp = PdfPages('pd_l1_peak_numbers.pdf')

    fig = plt.figure(tight_layout=True)
    gs = gridspec.GridSpec(1, 2)

    ax = fig.add_subplot(gs[0, 0])
    ax.scatter(unthresholded_peak_ns[:, 0], unthresholded_peak_ns[:, 1], s=2)
    ax.set_ylabel('Bottom of image')
    ax.set_xlabel('Whole image')
    ax.set_title('Number of all peaks')

    ax = fig.add_subplot(gs[0, 1])
    ax.scatter(thresholded_peak_ns[:, 0], thresholded_peak_ns[:, 1], s=2)
    ax.set_ylabel('Bottom of image')
    ax.set_xlabel('Whole image')
    ax.set_title('Number of thresholded peaks')

    fig.align_labels()  # same as fig.align_xlabels(); fig.align_ylabels()

    pp.savefig()
    pp.close()


def plot_peak_comparison(
        whole_to_bottom, bottom_to_whole, whole_to_bottom_thresholded,
        bottom_to_whole_thresholded):
    pp = PdfPages('pd_l1_peak_time_comparison.pdf')

    fig = plt.figure(tight_layout=True)
    gs = gridspec.GridSpec(2, 2)

    ax = fig.add_subplot(gs[0, 0])
    ax.scatter(whole_to_bottom[:, 0], whole_to_bottom[:, 1], s=2)
    ax.set_ylabel('Bottom of image')
    ax.set_xlabel('Whole image')
    ax.set_title('Time of all peaks')

    ax = fig.add_subplot(gs[0, 1])
    ax.scatter(
        whole_to_bottom_thresholded[:, 0],
        whole_to_bottom_thresholded[:, 1],
        s=2)
    ax.set_ylabel('Bottom of image')
    ax.set_xlabel('Whole image')
    ax.set_title('Time of thresholded peaks')

    ax = fig.add_subplot(gs[1, 0])
    ax.scatter(bottom_to_whole[:, 0], bottom_to_whole[:, 1], s=2)
    ax.set_xlabel('Bottom of image')
    ax.set_ylabel('Whole image')

    ax = fig.add_subplot(gs[1, 1])
    ax.scatter(
        bottom_to_whole_thresholded[:, 0],
        bottom_to_whole_thresholded[:, 1],
        s=2)
    ax.set_xlabel('Bottom of image')
    ax.set_ylabel('Whole image')

    fig.align_labels()  # same as fig.align_xlabels(); fig.align_ylabels()

    pp.savefig()
    pp.close()
