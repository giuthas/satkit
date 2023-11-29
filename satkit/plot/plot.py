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
"""SATKIT plotting functions."""

# Built in packages
import logging
from enum import Enum
from typing import List, Optional, Tuple, Union

# Efficient array operations
import numpy as np
from scipy import signal as scipy_signal
from scipy import interpolate

from icecream import ic

# Scientific plotting
from matplotlib.axes import Axes
from matplotlib.lines import Line2D

# Local packages
from satkit.gui.boundary_animation import AnimatableBoundary, BoundaryAnimator
from satkit.satgrid import SatTier

_plot_logger = logging.getLogger('satkit.plot')


class Normalisation(Enum):
    """
    An Enum for different kinds of plot normalisation in the y-direction.

    none: no normalisation
    peak: divide all data points y-values by the largest y-value
    bottom: deduct the lowest y-value from all data poitns y-values
    both: do first bottom normalisation and then peak normalisation.
    """
    none = 'NONE'
    peak = 'PEAK'
    bottom = 'BOTTOM'
    both = 'PEAK AND BOTTOM'


def plot_timeseries(axes: Axes,
                    data: np.ndarray,
                    time: np.ndarray,
                    xlim: Tuple[float, float],
                    ylim: Optional[Tuple[float, float]] = None,
                    normalise: Normalisation = 'NONE',
                    number_of_ignored_frames: int = 10,
                    ylabel: Optional[str] = None,
                    picker=None,
                    color: str = "deepskyblue",
                    linestyle: str = "-",
                    alpha: float = 1.0,
                    sampling_step: int = 1,
                    find_peaks: bool = False):
    """
    Plot a timeseries.

    The timeseries most likely comes from a Modality, but 
    that is left up to the caller. 

    Arguments:
    axis -- matplotlib axes to plot on.
    pd -- the timeseries - NOT the PD data object.
    time -- timestamps for the timeseries.
    xlim -- limits for the x-axis in seconds.

    Keyword arguments:
    peak_normalise -- if True, scale the data maximum to equal 1.
    peak_normalisation_offset -- how many values to ignore from 
        the beginning of data when calculating maximum. 
    ylabel -- label for this axes. 
    picker -- a picker tied to the plotted PD curve to facilitate
        annotation.
    color -- matplotlib color for the line.
    linestyle -- matplotlib linestyle.
    alpha -- alpha value for the line.

    Returns None.
    """
    plot_data = data[number_of_ignored_frames:]
    plot_time = time[number_of_ignored_frames:]

    _plot_logger.debug("Normalisation is %s.", normalise)
    if normalise in (Normalisation.both, Normalisation.bottom):
        plot_data = plot_data - np.min(plot_data)
    if normalise in [Normalisation.both, Normalisation.peak]:
        plot_data = plot_data/np.max(plot_data)

    if picker:
        axes.plot(
            plot_time[:: sampling_step],
            plot_data[:: sampling_step],
            color=color, lw=1, linestyle=linestyle, picker=picker, alpha=alpha)
    else:
        axes.plot(plot_time[::sampling_step], plot_data[::sampling_step],
                  color=color, lw=1, linestyle=linestyle, alpha=alpha)

    # The official fix for the above curve not showing up on the legend.
    timeseries = Line2D([], [], color=color, lw=1, linestyle=linestyle)

    if find_peaks:
        mark_gesture_peaks(axes, plot_data, plot_time)
        # mark_gesture_boundaries(axes, plot_data, plot_time)

    axes.set_xlim(xlim)

    if ylim:
        axes.set_ylim(ylim)
    elif normalise in [Normalisation.both]:
        axes.set_ylim([-0.05, 1.05])
    elif normalise in [Normalisation.peak]:
        axes.set_ylim([-0.05, 1.05])
        # axes.set_yscale('log')

    if ylabel:
        axes.set_ylabel(ylabel)

    return timeseries


def mark_gesture_peaks(axes, data, timevector) -> Line2D:
    peaks, _ = find_gesture_peaks(data)
    for peak in peaks:
        line = axes.axvline(
            x=timevector[peak],
            color="crimson",
            lw=1,
            linestyle=':')
    return line


def mark_gesture_boundaries(axes, data, timevector) -> Line2D:
    peaks, _ = find_gesture_peaks(-data)
    for peak in peaks:
        line = axes.axvline(
            x=timevector[peak],
            color="dodgerblue",
            lw=1,
            linestyle=':')
    return line


def find_gesture_peaks(data: np.ndarray):
    search_data = data - np.min(data)
    search_data = search_data/np.max(search_data)

    peaks, properties = scipy_signal.find_peaks(
        search_data)  # , distance=10, prominence=.05)
    return peaks, properties


def plot_satgrid_tier(axes: Axes,
                      tier: SatTier,
                      time_offset: float = 0,
                      draw_text: bool = True,
                      text_y: float = 500
                      ) -> Union[Line2D, List[BoundaryAnimator]]:
    """
    Plot a textgrid tier on the axis and return animator objects.

    This is used both for displaying tiers as part of the tier display 
    and for decorating other plots with either just the boundary lines 
    or both boundaries and the annotation text.

    Arguments:
    ax -- matplotlib axes to plot on.
    tier -- TextGrid Tier represented as a SatTier.

    Keyword arguments:
    stimulus_onset -- onset time of the stimulus in the recording in
        seconds. Default is 0s.
    draw_text -- boolean value indicating if each segment's text should
        be drawn on the plot. Default is True.
    draggable --
    text_y -- 

    Returns a line object for the segment line, so that it
    can be included in the legend.
    Also returns a list of BoundaryAnimators that 
    """
    text_settings = {'horizontalalignment': 'center',
                     'verticalalignment': 'center'}

    line = None
    prev_text = None
    text = None
    boundaries = []
    for segment in tier:
        line = axes.axvline(
            x=segment.begin - time_offset,
            color="dimgrey",
            lw=1,
            linestyle='--')
        if draw_text and segment.text:
            prev_text = text
            text = axes.text(segment.mid - time_offset,
                             text_y, segment.text,
                             text_settings, color="dimgrey")
            boundaries.append(AnimatableBoundary(axes, line, prev_text, text))
        else:
            prev_text = text
            text = None
            boundaries.append(AnimatableBoundary(axes, line, prev_text, text))
    return boundaries, line


def plot_wav(
        ax: Axes,
        waveform: np.ndarray,
        wav_time: np.ndarray,
        xlim: Tuple[float, float],
        picker=None) -> Line2D:
    """
    Plot a waveform.

    Parameters
    ----------
    ax : Axes
        Axes to plot on.
    waveform : np.ndarray
        Waveform to plot
    wav_time : np.ndarray
        Timevector for the waveform. Must of same shape and length
    xlim : Tuple[float, float]
        x-axis limits.
    picker : _type_, optional
        Picker for selecting points on the plotted line, by default None

    Returns
    -------
    Line2D
        The plotted line.
    """
    normalised_wav = waveform / np.amax(np.abs(waveform))

    line = None
    if picker:
        line = ax.plot(wav_time, normalised_wav,
                       color="k", lw=1, picker=picker)
    else:
        line = ax.plot(wav_time, normalised_wav, color="k", lw=1)

    ax.axvline(x=0, color="dimgrey", lw=1, linestyle=(0, (5, 10)))

    ax.set_xlim(xlim)
    ax.set_ylim((-1.1, 1.1))
    ax.set_ylabel("Wave")

    return line


def plot_spectrogram(
        ax: Axes,
        waveform: np.ndarray,
        sampling_frequency: float,
        xtent_on_x: Tuple[float, float],
        NFFT: int = 220,
        noverlap: int = 215,
        cmap: str = 'Greys',
        ylim: Tuple[float, float] = (0, 10000),
        ylabel: str = "Spectrogram",
        picker=None):
    normalised_wav = waveform / np.amax(np.abs(waveform))

    # xlim = [xlim[0]+time_offset, xlim[1]+time_offset]
    # the length of the windowing segments
    Pxx, freqs, bins, im = ax.specgram(
        normalised_wav, NFFT=NFFT, Fs=sampling_frequency, noverlap=noverlap,
        cmap=cmap, xextent=xtent_on_x, picker=picker)
    (bottom, top) = im.get_extent()[2:]
    im.set_extent((xtent_on_x[0]+bins[0], xtent_on_x[0]+bins[-1], bottom, top))

    ax.set_ylim(ylim)
    ax.set_ylabel(ylabel)

    return Pxx, freqs, bins, im


def plot_density(
        ax: Axes,
        frequencies: np.ndarray,
        x_values: Optional[np.ndarray] = None,
        ylim: Optional[Tuple[float, float]] = None,
        ylabel: str = "Densities)",
        picker=None):

    densities = frequencies/np.amax(frequencies)
    if not x_values:
        x_values = np.arange(len(densities))

    line = None
    if picker:
        line = ax.plot(x_values, densities, color="k", lw=1, picker=picker)
    else:
        line = ax.plot(x_values, densities, color="k", lw=1)

    if ylim:
        ax.set_ylim(ylim)
    ax.set_ylabel(ylabel)

    return line


def plot_spline(
        ax: Axes,
        data: np.ndarray,
        limits: Optional[tuple[int, int]] = None,
        display_line: bool = True,
        display_points: bool = False) -> None:
    """
    Plot a spline on the given axes.

    Parameters
    ----------
    ax : Axes
        matplotlib axes
    data : np.ndarray
        the spline Cartesian coordinates in axes order x-y, splinepoints.
    limits : Optional[tuple[int, int]], optional
        How many points to leave out from the (front, back) of the spline, by default None
    display_line : bool, optional
        should the interpolated spline line be drawn, by default True
    display_points : bool, optional
        should the spline control points be drawn, by default False
    """
    solid_data = data
    if limits:
        if limits[1] == 0:
            solid_data = data[:, limits[0]:]
        else:
            solid_data = data[:, limits[0]:-limits[1]]

    if display_line:
        if limits:
            interp_result = interpolate.splprep(data, s=0)
            tck = interp_result[0]
            interpolation_points = np.arange(0, 1.01, 0.01)
            interpolated_spline = interpolate.splev(interpolation_points, tck)
            ax.plot(interpolated_spline[0],
                    -interpolated_spline[1], color='orange', linewidth=1, alpha=.5)

        interp_result = interpolate.splprep(solid_data, s=0)
        tck = interp_result[0]
        interpolation_points = np.arange(0, 1.01, 0.01)
        interpolated_spline = interpolate.splev(interpolation_points, tck)
        ax.plot(interpolated_spline[0],
                -interpolated_spline[1], color='red', linewidth=1)
    if display_points:
        ax.plot(data[0, :], -data[1, :], 'ob', markersize=2)
