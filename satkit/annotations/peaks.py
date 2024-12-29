#
# Copyright (c) 2019-2024
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
"""
Generating and operating on peak annotations. 

Currently, contains also some legacy code that is not in use, but may provide a
useful basis for writing future functionality.
"""

import csv
import logging
from dataclasses import dataclass
import math

import numpy as np
import pandas

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from scipy import signal as scipy_signal

from satkit.utility_functions import normalise_timeseries
from satkit.configuration import (
    PeakDetectionParams, TimeseriesNormalisation)
from satkit.data_structures import Modality, PointAnnotations, Recording
from satkit.constants import (
    DEFAULT_ENCODING, AnnotationType, IntervalBoundary, IntervalCategory
)
from satkit.metrics import PD

_logger = logging.getLogger('satkit.peak_detection')


def add_peaks(
    modality: Modality,
    peak_parameters: PeakDetectionParams = None,
    release_data_memory: bool = False,
) -> None:
    """
    Add peak annotation to a modality.

    Parameters
    ----------
    modality : Modality
        The annotated Modality. Assumed to be a 1D timeseries.
    peak_parameters : dict, optional
        _description_, by default None
    release_data_memory : bool, optional
        Should the Modality's data memory be released after adding the
        annotations, by default False

    Raises
    ------
    NotImplementedError
        If IntervalBoundary is not either BEGIN or END
    """

    # TODO: if easily possible move this decision to a where we loop over
    # recordings
    recording = modality.recording
    if recording.excluded:
        _logger.info(
            "Recording %s excluded from processing. Not adding peaks.",
            recording.basename)
        return

    if peak_parameters.distance_in_seconds:
        distance = math.ceil(
            peak_parameters.distance_in_seconds *
            modality.sampling_rate)
        peak_parameters.find_peaks_args.distance = distance

    annotations = find_gesture_peaks(
        modality.data,
        modality.timevector,
        peak_parameters)
    modality.add_point_annotations(annotations)

    if peak_parameters.time_min and recording.satgrid:
        tier_name = peak_parameters.time_min.tier
        tier = recording.satgrid[tier_name]

        interval_category = peak_parameters.time_min.interval
        interval = tier.get_interval_by_category(
            interval_category, peak_parameters.time_min.label)

        interval_boundary = peak_parameters.time_min.boundary
        if interval_boundary is IntervalBoundary.BEGIN:
            time_min = interval.begin
        elif interval_boundary is IntervalBoundary.END:
            time_min = interval.end
        else:
            raise NotImplementedError(
                f"Unknown interval boundary type: {interval_boundary}")

        if peak_parameters.time_min.offset:
            time_min += peak_parameters.time_min.offset

        annotations.apply_lower_time_limit(time_min)

    if peak_parameters.time_max and recording.satgrid:
        time_max = None
        tier_name = peak_parameters.time_max.tier
        tier = recording.satgrid[tier_name]

        interval_category = peak_parameters.time_max.interval
        interval = tier.get_interval_by_category(
            interval_category, peak_parameters.time_max.label)
        if interval is None:
            interval = tier.get_interval_by_category(
                IntervalCategory.LAST_NON_EMPTY)

        interval_boundary = peak_parameters.time_max.boundary
        if interval_boundary is IntervalBoundary.BEGIN:
            time_max = interval.begin
        elif interval_boundary is IntervalBoundary.END:
            time_max = interval.end
        else:
            raise NotImplementedError(
                f"Unknown interval boundary type: {interval_boundary}")

        if time_max is not None:
            if peak_parameters.time_max.offset:
                time_max += peak_parameters.time_max.offset
            annotations.apply_upper_time_limit(time_max)

    if release_data_memory:
        modality.data = None

    _logger.debug(
        "Added %s annotations to Modality %s.",
        AnnotationType.PEAKS, modality.name)


def find_gesture_peaks(
        data: np.ndarray,
        timevector: np.ndarray,
        peak_params: PeakDetectionParams = None,
) -> PointAnnotations:
    """
    Find peaks in the data with `scipy_signal.find_peaks`.

    Parameters
    ----------
    data : np.ndarray
        The timeseries data. Should be a 1D array.
    timevector : np.ndarray
        Timevector corresponding to the data.
    peak_params : PeakDetectionParams, optional
        An object containing normalisation and parameters to pass to
        `scipy_signal.find_peaks`, by default None. 

    Returns
    -------
    PointAnnotations
        The gesture peaks asa PointAnnotations object.
    """
    normalisation = peak_params.normalisation
    search_data = data[peak_params.number_of_ignored_frames:]
    search_data = normalise_timeseries(
        search_data, normalisation=normalisation)

    if peak_params.find_peaks_args:
        peak_indeces, properties = scipy_signal.find_peaks(
            search_data, **peak_params.find_peaks_args.model_dump()
        )
    else:
        peak_indeces, properties = scipy_signal.find_peaks(search_data)

    peak_indeces = peak_indeces + peak_params.number_of_ignored_frames

    peak_times = timevector[peak_indeces]

    annotations = PointAnnotations(
        annotation_type=AnnotationType.PEAKS,
        indeces=peak_indeces,
        times=peak_times,
        generating_parameters=peak_params,
        properties=properties)
    return annotations

def _setup_peak_extraction_variables(
        recordings: list[Recording],
        metrics: tuple[str],
) -> tuple[list[Recording], list[str], ]:
    """
    Local helper function to capture some boilerplate setup code.
    """
    exclude = ("water swallow", "bite plate")
    recordings = [
        recording for recording in recordings
        if not any(prompt in recording.meta_data.prompt for prompt in exclude)
    ]

    modality_params = PD.get_names_and_meta(
        modality="RawUltrasound",
        norms=list(metrics),
    )
    reference_names = list(modality_params.keys())
    return recordings, reference_names


def annotations_to_dataframe(
        # annotation_statistic:
        recordings: list[Recording],
        modality_name: list[str],
        metrics: tuple[str],
        downsampling_ratios: tuple[int],
        annotations: dict[str, tuple[str]] = None
) -> pandas.DataFrame:
    recordings, reference_names = _setup_peak_extraction_variables(
        recordings, metrics)

    average_prominences = np.zeros(
        [len(recordings), len(metrics), 1+len(downsampling_ratios)])

    annotation_dicts = []

    for i, recording in enumerate(recordings):
        for j, metric in enumerate(metrics):
            modality = recording[reference_names[j]]
            peaks = modality.annotations[AnnotationType.PEAKS]
            annotation_dicts.extend(
                [
                    {
                        'metric': metric,
                        'downsampling_ratio': 1,
                        'prominence': prominence
                    }
                    for prominence in peaks.properties['prominences']
                ]
            )
            average_prominences[i][j][0] = np.mean(
                peaks.properties['prominences'])

    for i, recording in enumerate(recordings):
        downsampled_names = [key for key in recording.keys()
                             if 'PD' in key and 'downsampled' in key]
        for j, metric in enumerate(metrics):
            p_norm_names = [name for name in downsampled_names
                            if metric in name]

            for k, ratio in enumerate(downsampling_ratios):
                name = [name for name in p_norm_names
                        if int(name[-1]) == ratio]
                name = name[0]
                modality = recording[name]
                peaks = modality.annotations[AnnotationType.PEAKS]
                annotation_dicts.extend(
                    [
                        {
                            'metric': metric,
                            'downsampling_ratio': ratio,
                            'prominence': prominence
                        }
                        for prominence in peaks.properties['prominences']
                    ]
                )
    dataframe = pandas.DataFrame(annotation_dicts)

    dataframe['metric'] = pandas.Categorical(dataframe['metric'])
    categories = dataframe['metric'].unique()
    categories = ["l$\infty$" if metric ==
                  "l_inf" else metric for metric in categories]
    dataframe['metric'] = dataframe['metric'].cat.rename_categories(categories)

    values = dataframe['downsampling_ratio'].unique().sort()
    dataframe['downsampling_ratio'] = pandas.Categorical(
        dataframe['downsampling_ratio'], categories=values, ordered=True)
    return dataframe


def prominences_in_downsampling(
        recordings: list[Recording],
        metrics: tuple[str],
        downsampling_ratios: tuple[int]
) -> np.ndarray:
    recordings, reference_names = _setup_peak_extraction_variables(
        recordings, metrics)

    average_prominences = np.zeros(
        [len(recordings), len(metrics), 1+len(downsampling_ratios)])

    for i, recording in enumerate(recordings):
        for j, p in enumerate(metrics):
            modality = recording[reference_names[j]]
            peaks = modality.annotations[AnnotationType.PEAKS]
            average_prominences[i][j][0] = np.mean(
                peaks.properties['prominences'])

    for i, recording in enumerate(recordings):
        downsampled_names = [key for key in recording.keys()
                             if 'PD' in key and 'downsampled' in key]
        for j, p in enumerate(metrics):
            p_norm_names = [name for name in downsampled_names
                            if p in name]

            for k, ratio in enumerate(downsampling_ratios):
                name = [name for name in p_norm_names
                        if int(name[-1]) == ratio]
                name = name[0]
                modality = recording[name]
                peaks = modality.annotations[AnnotationType.PEAKS]
                average_prominences[i][j][k+1] = np.mean(
                    peaks.properties['prominences'])

    average_prominences = np.moveaxis(
        average_prominences, (0, 1, 2), (1, 0, 2))
    _logger.debug("average_prominences.shape = %s",
                  str(average_prominences.shape))
    return average_prominences


def nearest_neighbours_in_downsampling(
        recordings: list[Recording],
        metrics: tuple[str],
        downsampling_ratios: tuple[int]
) -> np.ndarray:
    recordings, reference_names = _setup_peak_extraction_variables(
        recordings, metrics)

    average_distances = np.zeros(
        [len(recordings), len(metrics), 1+len(downsampling_ratios)])

    for i, recording in enumerate(recordings):
        downsampled_names = [key for key in recording.keys()
                             if 'PD' in key and 'downsampled' in key]
        for j, p in enumerate(metrics):
            reference_name = [name for name in reference_names
                              if p in name]
            reference_name = reference_name[0]
            reference_modality = recording[reference_name]
            reference_peaks = reference_modality.annotations[
                AnnotationType.PEAKS]

            p_norm_names = [name for name in downsampled_names
                            if p in name]

            for k, ratio in enumerate(downsampling_ratios):
                name = [name for name in p_norm_names
                        if int(name[-1]) == ratio]
                name = name[0]
                modality = recording[name]
                peaks = modality.annotations[AnnotationType.PEAKS]
                neighbours = get_nearest_neighbours(
                    reference_peaks.times, peaks.times)
                distances = np.abs(np.diff(neighbours, axis=1))
                average_distances[i][j][k+1] = np.mean(distances)

    average_distances = np.moveaxis(
        average_distances, (0, 1, 2), (1, 0, 2))
    _logger.debug("average_distances.shape = %s",
                  str(average_distances.shape))
    return average_distances


def count_number_of_peaks(
        recordings: list[Recording],
        metrics: tuple[str],
        downsampling_ratios: tuple[int]
) -> np.ndarray:
    exclusion = ("water swallow", "bite plate")
    recordings = [
        recording for recording in recordings
        if not any(prompt in recording.meta_data.prompt for prompt in exclusion)
    ]

    peak_numbers = np.zeros(
        [len(recordings), len(metrics), 1+len(downsampling_ratios)])

    modality_params = PD.get_names_and_meta(
        modality="RawUltrasound",
        norms=list(metrics),
    )
    modality_names = list(modality_params.keys())

    for i, recording in enumerate(recordings):
        for j, p in enumerate(metrics):
            modality = recording[modality_names[j]]
            peaks = modality.annotations[AnnotationType.PEAKS]
            peak_numbers[i][j][0] = len(peaks.indeces)

    for i, recording in enumerate(recordings):
        modality_names = [key for key in recording.keys()
                          if 'PD' in key and 'downsampled' in key]
        for j, p in enumerate(metrics):
            p_norm_names = [name for name in modality_names
                            if p in name]
            for k, ratio in enumerate(downsampling_ratios):
                name = [name for name in p_norm_names
                        if int(name[-1]) == ratio]
                name = name[0]
                modality = recording[name]
                peaks = modality.annotations[AnnotationType.PEAKS]
                peak_numbers[i][j][k+1] = len(peaks.indeces)

    return peak_numbers


def get_nearest_neighbours(
        array1: np.ndarray, array2: np.ndarray) -> np.ndarray:
    """
    Get an array of nearest neighbours of elements of array1 in array2.

    Parameters
    ----------
    array1 : np.ndarray
        The first 1D array.
    array2 : np.ndarray
        The second 1D array where we search for the nearest neighbours.

    Returns
    -------
    np.ndarray
        An array containing each element of array1 paired with its nearest
        neighbour from array2.
    """
    neighbours = np.zeros((array1.size, 2))
    neighbours[:, 0] = array1
    for i, element in enumerate(array1):
        diff = np.abs(array2-element)
        neighbours[i, 1] = array2[np.argmin(diff)]

    return neighbours


@dataclass
class PeakData:
    """Peaks, their times, and properties as returned by `scipy.find_peaks`."""
    peaks: np.ndarray
    peak_times: np.ndarray
    properties: dict


def time_series_peaks(
        data: np.ndarray,
        time: np.ndarray,
        time_lim: tuple[float, float],
        normalise: TimeseriesNormalisation | None,
        number_of_ignored_frames: int | None = 10,
        distance: int | None= 10,
        prominence: float | None = 0.05):
    if number_of_ignored_frames:
        search_data = data[number_of_ignored_frames:]
        search_time = time[number_of_ignored_frames:]
    else:
        search_data = data
        search_time = time

    indeces = np.nonzero(
        (search_time > time_lim[0]) & (search_time < time_lim[1]))
    search_data = search_data[indeces]
    search_time = search_time[indeces]

    search_data = normalise_timeseries(search_data, normalisation=normalise)

    peaks, properties = scipy_signal.find_peaks(
        search_data, distance=distance, prominence=prominence)

    peak_times = search_time[peaks]

    return PeakData(peaks, peak_times, properties)


def save_peaks(
    filename: str,
    recordings: list[Recording]
):
    """
    Save peak data to .csv files.

    Save both numbers/recording for each recording and the peak times
    themselves do this for unthresholded and thresholded peaks.
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
        basename = recording.basename
        prompt = recording.meta_data.prompt

        l1 = recording['PD l1 on RawUltrasound']
        l1_bottom = recording['PD l1 bottom on RawUltrasound']

        audio = recording['MonoAudio']
        if audio.go_signal is None:
            stimulus_onset = 0
        else:
            stimulus_onset = audio.go_signal
        ultra_time = l1.timevector - stimulus_onset

        end_time = 0
        for interval in recording.satgrid['utterance']:
            if interval.label:
                end_time = interval.end
                break

        time_lim = (0, end_time)

        peak_data = time_series_peaks(
            l1.data, ultra_time, time_lim=time_lim,
            normalise='PEAK AND BOTTOM',
            number_of_ignored_frames=None,
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
            'id': basename,
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
                peak_data_thresholded.peak_times,
                bottom_peak_data_thresholded.peak_times)
            bottom_to_whole_thresholded = get_nearest_neighbours(
                bottom_peak_data_thresholded.peak_times,
                peak_data_thresholded.peak_times)
        else:
            whole_to_bottom = np.append(
                whole_to_bottom, get_nearest_neighbours(
                    peak_data.peak_times, bottom_peak_data.peak_times), axis=0)
            bottom_to_whole = np.append(
                bottom_to_whole, get_nearest_neighbours(
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

    with open(peak_n_file, "w", encoding=DEFAULT_ENCODING) as csv_file:
        writer = csv.DictWriter(csv_file, ns.keys(), delimiter=',')
        writer.writeheader()
        for line in peak_ns:
            writer.writerow(line)

    whole_to_bottom_file = filename + '_whole_to_bottom.csv'
    bottom_to_whole_file = filename + '_bottom_to_whole.csv'
    whole_to_bottom_thresholded_file = (
            filename + '_whole_to_bottom_thresholded.csv')
    bottom_to_whole_thresholded_file = (
            filename + '_bottom_to_whole_thresholded.csv')
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
