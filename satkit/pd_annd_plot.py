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
import logging
import os.path
from pathlib import Path

# Efficient array operations
import numpy as np

# Scientific plotting
import matplotlib.lines as mlines
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# Praat textgrids
import textgrids


_plot_logger = logging.getLogger('satkit.pd.plot')


#####
# Helper functions
#####

def moving_average(a, n=3):
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n


#####
# Subplot functions
#####

def plot_textgrid_lines(ax, textgrid, stimulus_onset=0, draw_text=True):
    """
    Plot vertical lines for the segments in the textgrid.

    Arguments:
    ax -- matplotlib axes to plot on.
    textgrid -- a textgrids module textgrid object containing a tier
        called 'segment'.

    Keyword arguments:
    stimulus_onset -- onset time of the stimulus in the recording in
        seconds. Default is 0s.
    draw_text -- boolean value indicating if each segment's text should
        be drawn on the plot. Default is True.

    Returns a line object for the segment line, so that it
    can be included in the legend.

    Throws a KeyError if a tier called 'segment' is not present in the
    textgrid.
    """
    text_settings = {'horizontalalignment': 'center',
                     'verticalalignment': 'center'}
    for segment in textgrid['segment']:
        if segment.text == "":
            continue
        elif segment.text == "beep":
            continue
        else:
            segment_line = ax.axvline(
                x=segment.xmin - stimulus_onset, color="dimgrey", lw=1,
                linestyle='--')
            ax.axvline(x=segment.xmax - stimulus_onset,
                       color="dimgrey", lw=1, linestyle='--')
            if draw_text:
                ax.text(segment.mid - stimulus_onset, 500, segment.text,
                        text_settings, color="dimgrey")
    return segment_line


def plot_pd(ax, pd, time, xlim, textgrid=None, stimulus_onset=0,
            picker=None):
    """
    Plot a Recordings PD timeseries.

    Arguments:
    ax -- matplotlib axes to plot on.
    pd -- the timeseries - NOT the PD data object.
    time -- timestamps for the timeseries.
    xlim -- limits for the x-axis in seconds.

    Keyword arguments:
    textgrid -- a textgrids module textgrid object.
    stimulus_onset -- onset time of the stimulus in the recording in
        seconds.
    picker -- a picker tied to the plotted PD curve to facilitate
        annotation.

    Returns None.
    """

    # The PD curve and the official fix for it not showing up on the legend.
    ax.plot(time, pd, color="deepskyblue", lw=1, picker=picker)
    pd_curve = mlines.Line2D([], [], color="deepskyblue", lw=1)

    go_line = ax.axvline(x=0, color="dimgrey", lw=1, linestyle=(0, (5, 10)))

    segment_line = None
    if textgrid:
        segment_line = plot_textgrid_lines(ax, textgrid, stimulus_onset)

    ax.set_xlim(xlim)
    ax.set_ylim((-50, 3550))
    if segment_line:
        ax.legend((pd_curve, go_line, segment_line),
                  ('Pixel difference', 'Go-signal onset', 'Acoustic segments'),
                  loc='upper right')
    else:
        ax.legend((pd_curve, go_line),
                  ('Pixel difference', 'Go-signal onset'),
                  loc='upper right')
    ax.set_ylabel("PD on ultrasound")


def plot_pd_vid(ax, pd, time, xlim, textgrid=None, stimulus_onset=0,
                picker=None, draw_legend=False):
    """
    Plot a Recordings PD timeseries.

    Arguments:
    ax -- matplotlib axes to plot on.
    pd -- the timeseries - NOT the PD data object.
    time -- timestamps for the timeseries.
    xlim -- limits for the x-axis in seconds.

    Keyword arguments:
    textgrid -- a textgrids module textgrid object.
    stimulus_onset -- onset time of the stimulus in the recording in
        seconds.
    picker -- a picker tied to the plotted PD curve to facilitate
        annotation.

    Returns None.
    """

    # The PD curve and the official fix for it not showing up on the legend.
    ax.plot(time, pd, color="deepskyblue", lw=1, picker=picker)
    ax.plot(time[1::2], pd[1::2], color="deepskyblue",
            lw=1, picker=picker, linestyle=':')
    ax.plot(time[0::2], pd[0::2], color="deepskyblue",
            lw=1, picker=picker, linestyle=':')
    # ax.plot(time, pd, color="deepskyblue", lw=1, picker=picker)
    pd_curve = mlines.Line2D([], [], color="deepskyblue", lw=1)

    go_line = ax.axvline(x=0, color="dimgrey", lw=1, linestyle=(0, (5, 10)))

    segment_line = None
    if textgrid:
        segment_line = plot_textgrid_lines(ax, textgrid, stimulus_onset)

    ax.set_xlim(xlim)

    # Before 1.0 implement a way - peak normalisation for example - for doing this better than by hard coded values.
    # ex2 day3
    ax.set_ylim((3550, 4150))
    # ex2 day2b
    # ax.set_ylim((3950, 5050))
    if draw_legend and segment_line:
        ax.legend((pd_curve, go_line, segment_line),
                  ('Pixel difference', 'Go-signal onset', 'Acoustic segments'),
                  loc='upper right')
    elif draw_legend:
        ax.legend((pd_curve, go_line),
                  ('Pixel difference', 'Go-signal onset'),
                  loc='upper right')
    ax.set_ylabel("PD on lip video\ntime step = 2")


def plot_pd_vid_rgb(ax, pd, time, xlim, textgrid=None, stimulus_onset=0,
                    picker=None):
    """
    Plot a Recordings PD timeseries.

    Arguments:
    ax -- matplotlib axes to plot on.
    pd -- the timeseries - NOT the PD data object.
    time -- timestamps for the timeseries.
    xlim -- limits for the x-axis in seconds.

    Keyword arguments:
    textgrid -- a textgrids module textgrid object.
    stimulus_onset -- onset time of the stimulus in the recording in
        seconds.
    picker -- a picker tied to the plotted PD curve to facilitate
        annotation.

    Returns None.
    """

    # The PD curve and the official fix for it not showing up on the legend.
    ax.plot(time, pd[:, 0], color="r", lw=1, picker=picker)
    ax.plot(time[1::2], pd[1::2, 0], color="r",
            lw=1, picker=picker, linestyle='--')
    ax.plot(time[0::2], pd[0::2, 0], color="r",
            lw=1, picker=picker, linestyle='--')

    ax.plot(time, pd[:, 1], color="g", lw=1, picker=picker)
    ax.plot(time[1::2], pd[1::2, 1], color="g",
            lw=1, picker=picker, linestyle='--')
    ax.plot(time[0::2], pd[0::2, 1], color="g",
            lw=1, picker=picker, linestyle='--')

    ax.plot(time, pd[:, 2]-650, color="deepskyblue", lw=1, picker=picker)
    ax.plot(time[1::2], pd[1::2, 2]-650, color="deepskyblue",
            lw=1, picker=picker, linestyle='--')
    ax.plot(time[0::2], pd[0::2, 2]-650, color="deepskyblue",
            lw=1, picker=picker, linestyle='--')
    # ax.plot(time, pd, color="deepskyblue", lw=1, picker=picker)
    pd_curve = mlines.Line2D([], [], color="deepskyblue", lw=1)

    go_line = ax.axvline(x=0, color="dimgrey", lw=1, linestyle=(0, (5, 10)))

    segment_line = None
    if textgrid:
        segment_line = plot_textgrid_lines(ax, textgrid, stimulus_onset)

    ax.set_xlim(xlim)
    ax.set_ylim((1750, 2200))
    if segment_line:
        ax.legend((pd_curve, go_line, segment_line),
                  ('Pixel difference', 'Go-signal onset', 'Acoustic segments'),
                  loc='upper right')
    else:
        ax.legend((pd_curve, go_line),
                  ('Pixel difference', 'Go-signal onset'),
                  loc='upper right')
    ax.set_ylabel("PD on lip video\nSeparate rgb channels")


def plot_l1(ax, pd, ultra_time, xlim, textgrid=None, time_offset=0,
            picker=None):

    # The PD curve and the official fix for it not showing up on the legend.
    ax.plot(ultra_time, pd['l1']/np.max(pd['l1'][1:]),
            color="deepskyblue", lw=1, picker=picker)
    ax.plot(ultra_time, pd['pd']/np.max(pd['pd'][1:]), color="g", lw=1)
    pd_curve = mlines.Line2D([], [], color="deepskyblue", lw=1)

    go_line = ax.axvline(x=0, color="dimgrey", lw=1, linestyle=(0, (5, 10)))

    segment_line = None
    if textgrid:
        segment_line = plot_textgrid_lines(ax, textgrid, time_offset)

    ax.set_xlim(xlim)
    # ax.set_ylim((-50,3050))
    if segment_line:
        ax.legend(
            (pd_curve, go_line, segment_line),
            ('Pixel difference: l1 norm', 'Go-signal onset',
             'Acoustic segments'),
            loc='upper right')
    else:
        ax.legend((pd_curve, go_line), ('Pixel difference: l1 norm',
                                        'Go-signal onset'), loc='upper right')
    ax.set_ylabel("PD: l1")


def plot_pd_peak_normalised(
        ax, pd, ultra_time, xlim, textgrid=None, time_offset=0):

    ax.plot(ultra_time, pd['pd']/np.max(pd['pd'][1:]),
            color="deepskyblue", lw=1, label='Pixel difference')
    pd_curve = mlines.Line2D([], [], color="deepskyblue", lw=1)

    go_line = ax.axvline(x=0, color="dimgrey", lw=1, linestyle=(0, (5, 10)))
    # ax.axvline(x=0, color="g", lw=1)

    segment_line = None
    if textgrid:
        segment_line = plot_textgrid_lines(ax, textgrid, time_offset)

    ax.set_xlim(xlim)
    ax.set_ylim((0, 1.1))
    if segment_line:
        ax.legend((pd_curve, go_line, segment_line),
                  ('Pixel difference', 'Go-signal onset', 'Acoustic segments'),
                  loc='upper right')
    else:
        ax.legend((pd_curve, go_line),
                  ('Pixel difference', 'Go-signal onset'),
                  loc='upper right')
    ax.set_ylabel("Peak normalised PD")


def plot_pd_norms(
        ax, pd, ultra_time, xlim, textgrid=None, time_offset=0,
        draw_legend=False):
    ax.plot(ultra_time, pd['l1']/np.max(pd['l1'][1:]), color="black", lw=1)
    ax.plot(ultra_time, pd['pd']/np.max(pd['pd'][1:]), color="dimgrey", lw=1)
    ax.plot(ultra_time, pd['l3']/np.max(pd['l3'][1:]), color="grey", lw=1)
    ax.plot(ultra_time, pd['l4']/np.max(pd['l4'][1:]), color="darkgrey", lw=1)
    ax.plot(ultra_time, pd['l5']/np.max(pd['l5'][1:]), color="silver", lw=1)
    ax.plot(
        ultra_time, pd['l10'] / np.max(pd['l10'][1:]),
        color="lightgrey", lw=1)
    ax.plot(
        ultra_time, pd['l_inf'] / np.max(pd['l_inf'][1:]),
        color="k", lw=1, linestyle='--')

    go_line = ax.axvline(x=0, color="dimgrey", lw=1, linestyle=(0, (5, 10)))

    segment_line = None
    if textgrid:
        segment_line = plot_textgrid_lines(ax, textgrid, time_offset)

    if draw_legend:
        pd_curve = mlines.Line2D([], [], color="dimgrey", lw=1)
    if draw_legend and segment_line:
        ax.legend((pd_curve, go_line, segment_line),
                  ('Pixel difference', 'Go-signal onset', 'Acoustic segments'),
                  loc='upper right')
    elif draw_legend:
        ax.legend((pd_curve, go_line),
                  ('Pixel difference', 'Go-signal onset'),
                  loc='upper right')

    ax.set_xlim(xlim)
    ax.set_ylim((0, 1.1))
    ax.set_ylabel("PD")


def plot_annd_mpbpd(
        ax, annd, mpbpd, annd_time, xlim, textgrid=None, time_offset=0,
        picker=None, plot_raw=True):
    half_window = 2
    smooth_length = 2*half_window+1

    # last annd seems to be broken so leave it out
    # ax.plot(annd_time[:-1], annd['annd'][:-1], color="deepskyblue", lw=1, alpha=.5)
    ave_annd = moving_average(annd[:-1], n=smooth_length)
    ax.plot(annd_time[half_window:-(half_window+1)], ave_annd/np.max(ave_annd),
            color="orange", lw=1, label='Average Nearest Neighbour Distance')

    ave_mpbpd = moving_average(mpbpd[:-1], n=smooth_length)

    if plot_raw:
        ax.plot(annd_time[:-1], mpbpd[:-1]/np.max(ave_mpbpd),
                color="seagreen", lw=1, alpha=.4)

    if picker:
        ax.plot(
            annd_time[half_window: -(half_window + 1)],
            ave_mpbpd / np.max(ave_mpbpd),
            color="seagreen", lw=1, label='Median Point-by-point Distance',
            picker=picker)
    else:
        ax.plot(
            annd_time[half_window: -(half_window + 1)],
            ave_mpbpd / np.max(ave_mpbpd),
            color="seagreen", lw=1, label='Median Point-by-point Distance')

    ax.axvline(x=0, color="dimgrey", lw=1, linestyle=(0, (5, 10)))

    if textgrid:
        plot_textgrid_lines(ax, textgrid, time_offset)

    ax.set_xlim(xlim)
    ax.set_ylim((-0.05, 1.05))
    ax.legend(loc='upper right')
    ax.set_ylabel("Peak normalised\nspline metrics")


def plot_annd(
        ax, annd, annd_time, xlim, textgrid=None, time_offset=0, picker=None,
        plot_raw=True):
    half_window = 2
    smooth_length = 2*half_window+1

    # last annd seems to be broken so leave it out
    ave_annd = moving_average(annd['annd'][:-1], n=smooth_length)

    if plot_raw:
        ax.plot(annd_time[:-1], annd['annd'][:-1]/np.max(ave_annd),
                color="orange", lw=1, alpha=.5)

    ax.plot(annd_time[half_window:-(half_window+1)], ave_annd/np.max(ave_annd),
            color="orange", lw=1, label='Average Nearest Neighbour Distance')

    ax.axvline(x=0, color="dimgrey", lw=1, linestyle=(0, (5, 10)))

    if textgrid:
        plot_textgrid_lines(ax, textgrid, time_offset)

    ax.set_xlim(xlim)
    ax.set_ylim((-0.05, 1.05))
    ax.legend(loc='upper right')
    ax.set_ylabel("Peak normalised ANND")


def plot_mpbpd(
        ax, mpbpd, annd_time, xlim, textgrid=None, time_offset=0, picker=None,
        plot_raw=True):
    half_window = 2
    smooth_length = 2*half_window+1

    ave_mpbpd = moving_average(mpbpd[:-1], n=smooth_length)
    if plot_raw:
        ax.plot(annd_time[:-1], mpbpd[:-1]/np.max(ave_mpbpd),
                color="seagreen", lw=1, alpha=.4)

    if picker:
        ax.plot(
            annd_time[half_window: -(half_window + 1)],
            ave_mpbpd / np.max(ave_mpbpd),
            color="seagreen", lw=1, label='Median Point-by-point Distance',
            picker=picker)
    else:
        ax.plot(
            annd_time[half_window: -(half_window + 1)],
            ave_mpbpd / np.max(ave_mpbpd),
            color="seagreen", lw=1, label='Median Point-by-point Distance')

    ax.axvline(x=0, color="dimgrey", lw=1, linestyle=(0, (5, 10)))

    if textgrid:
        plot_textgrid_lines(ax, textgrid, time_offset)

    ax.set_xlim(xlim)
    ax.set_ylim((-0.05, 1.05))
    ax.legend(loc='upper right')
    ax.set_ylabel("Peak normalised MPBPD")


def plot_spline_metrics(
        ax, annd, annd_time, xlim, textgrid=None, time_offset=0):
    # last annd seems to be shit so leave it out
    half_window = 2
    smooth_length = 2*half_window+1

    # ax.plot(annd_time[:-1], annd['annd'][:-1], color="deepskyblue", lw=1, alpha=.5)
    ave_annd = moving_average(annd['annd'][:-1], n=smooth_length)
    ax.plot(annd_time[half_window:-(half_window+1)], ave_annd/np.max(ave_annd),
            color="black", lw=1)

    # ax.plot(annd_time[:-1], annd['mnnd'][:-1], color="g", lw=1, alpha=.5)
    ave_mnnd = moving_average(annd['mnnd'][:-1], n=smooth_length)
    ax.plot(annd_time[half_window:-(half_window+1)], ave_mnnd/np.max(ave_mnnd),
            color="dimgrey", lw=1, linestyle=':')

    ave_mpbpd = moving_average(annd['mpbpd'][:-1], n=smooth_length)
    ax.plot(
        annd_time[: -1],
        annd['mpbpd'][: -1] / np.max(ave_mpbpd),
        color="g", lw=1, alpha=.5)
    ax.plot(
        annd_time[half_window: -(half_window + 1)],
        ave_mpbpd / np.max(ave_mpbpd),
        color="grey", lw=1, linestyle='--')

    # ax.plot(annd_time[:-1], annd['spline_d'][:-1], color="k", lw=1, alpha=.5)
    ave_spline_d = moving_average(annd['spline_d'][:-1], n=smooth_length)
    ax.plot(annd_time[half_window: -(half_window + 1)],
            ave_spline_d / np.max(ave_spline_d),
            color="darkgrey", lw=1, linestyle='-.')

    ave_spline_l1 = moving_average(annd['spline_l1'][:-1], n=smooth_length)
    # ax.plot(annd_time[:-1], annd['spline_l1'][:-1]/np.max(ave_spline_l1),
    #        color="seagreen", lw=1, alpha=.5)
    ax.plot(annd_time[half_window: -(half_window + 1)],
            ave_spline_l1 / np.max(ave_spline_l1),
            color="seagreen", lw=1, linestyle='-.')

    ax.axvline(x=0, color="dimgrey", lw=1, linestyle=(0, (5, 10)))

    if textgrid:
        plot_textgrid_lines(ax, textgrid, time_offset)

    ax.set_xlim(xlim)
    ax.set_ylim((0, 1.05))
    ax.set_ylabel("Peak normalised spline metrics")


def plot_annd_options(ax, annd, annd_time, xlim, textgrid=None, time_offset=0):
    # last annd seems to be shit so leave it out
    ax.plot(annd_time[:-1], annd['annd'][:-1],
            color="deepskyblue", lw=1, alpha=.5)
    ax.plot(
        annd_time[3: -4],
        moving_average(annd['annd'][: -1],
                       n=7),
        color="deepskyblue", lw=1)
    ax.plot(annd_time[:-1], annd['mnnd'][:-1], color="g", lw=1, alpha=.5)
    ax.plot(
        annd_time[3: -4],
        moving_average(annd['mnnd'][: -1],
                       n=7),
        color="g", lw=1)
    ax.plot(annd_time[:-1], annd['mpbpd'][:-1], color="r", lw=1, alpha=.5)
    ax.plot(
        annd_time[3: -4],
        moving_average(annd['mpbpd'][: -1],
                       n=7),
        color="r", lw=1)
    ax.plot(annd_time[:-1], annd['spline_d'][:-1], color="k", lw=1, alpha=.5)
    ax.plot(
        annd_time[3: -4],
        moving_average(annd['spline_d'][: -1],
                       n=7),
        color="k", lw=1)

    ax.axvline(x=0, color="dimgrey", lw=1, linestyle=(0, (5, 10)))

    if textgrid:
        plot_textgrid_lines(ax, textgrid, time_offset)

    ax.axvline(x=0, color="k", lw=1)
    ax.set_xlim(xlim)
    ax.set_ylim((0, 2.05))
    ax.set_ylabel("ANND")


def plot_wav(
        ax, waveform, wav_time, xlim, textgrid=None, time_offset=0,
        picker=None, draw_legend=False):
    normalised_wav = waveform / \
        np.amax(np.abs(waveform))
    if picker:
        ax.plot(wav_time, normalised_wav, color="k", lw=1, picker=picker)
    else:
        ax.plot(wav_time, normalised_wav, color="k", lw=1)

    ax.axvline(x=0, color="dimgrey", lw=1, linestyle=(0, (5, 10)))

    segment_line = None
    if textgrid:
        segment_line = plot_textgrid_lines(
            ax, textgrid, time_offset, draw_text=False)

    if draw_legend:
        wave_curve = mlines.Line2D([], [], color="k", lw=1)
    if draw_legend and segment_line:
        ax.legend((wave_curve, segment_line),
                  ('Waveform', 'Acoustic segments'),
                  loc='upper right')
    elif draw_legend:
        ax.legend((wave_curve,),
                  ('Waveform',),
                  loc='upper right')

    ax.set_xlim(xlim)
    ax.set_ylim((-1.05, 1.05))
    ax.set_ylabel("Wave")
    ax.set_xlabel("Time (s), go-signal at 0 s.")


#####
# Combined plots
#####

def draw_pd(recording, figure_dir, xlim=(-.05, 1.25)):
    filename = recording.meta['basename'] + '_pd.pdf'
    filename = figure_dir.joinpath(filename)

    with PdfPages(str(filename)) as pdf:
        fig = plt.figure(figsize=(9, 4))

        ax1 = plt.subplot2grid((4, 1), (0, 0), rowspan=3)

        # Before 1.0 Selecting the title should be done elsewhere.
        # This breaks often with format of the prompt changing from session to session.
        plt.title(recording.meta['prompt'].split()[1])

        # plt.grid(True, 'major', 'x')
        ax1.axes.xaxis.set_ticklabels([])
        ax3 = plt.subplot2grid((4, 1), (3, 0))
        # plt.grid(True, 'major', 'x')

        audio = recording.modalities['MonoAudio']
        stimulus_onset = audio.meta['stimulus_onset']
        wav = audio.data
        wav_time = (audio.timevector - stimulus_onset)

        pd = recording.modalities['PD on RawUltrasound']
        ultra_time = pd.timevector - stimulus_onset

        textgrid = recording.textgrid

        plot_pd(ax1, pd.data['pd'], ultra_time, xlim,
                textgrid, stimulus_onset)
        plot_wav(ax3, wav, wav_time, xlim, textgrid, stimulus_onset)

        fig.align_ylabels()
        pdf.savefig()  # saves the current figure into a pdf page
        plt.close()
        _plot_logger.info("Drew PD plot in " + str(filename) + ".")


def draw_pd_ult_and_vid(recording, figure_dir, xlim=(-.05, 1.25)):
    filename = recording.meta['basename'] + '_pd_ult_and_vid.pdf'
    filename = figure_dir.joinpath(filename)

    with PdfPages(str(filename)) as pdf:
        # Before 1.0: Plot sizes should be adjustable by some sort of setup file or argument.
        # Same goes for title and at least y-labels.
        fig = plt.figure(figsize=(9, 7))
        # These are the values for CAW 2021 2-page paper
        #fig = plt.figure(figsize=(7, 5.5))

        ax1 = plt.subplot2grid((7, 1), (0, 0), rowspan=3)

        # Before 1.0 Selecting the title should be done elsewhere.
        # This breaks often with format of the prompt changing from session to session.
        plt.title(
            recording.meta['basename'] + ': ' + recording.meta['prompt'].split()[0])

        # plt.grid(True, 'major', 'x')
        ax1.axes.xaxis.set_ticklabels([])
        ax2 = plt.subplot2grid((7, 1), (3, 0), rowspan=3)
        # plt.grid(True, 'major', 'x')
        ax2.axes.xaxis.set_ticklabels([])
        ax3 = plt.subplot2grid((7, 1), (6, 0))
        # plt.grid(True, 'major', 'x')

        audio = recording.modalities['MonoAudio']
        stimulus_onset = audio.meta['stimulus_onset']
        wav = audio.data
        wav_time = (audio.timevector - stimulus_onset)

        ult_pd = recording.modalities['PD on RawUltrasound']
        ultra_time = ult_pd.timevector - stimulus_onset

        vid_pd = recording.modalities['PD on LipVideo']
        video_time = vid_pd.timevector - stimulus_onset

        textgrid = recording.textgrid

        plot_pd(ax1, ult_pd.data['pd'], ultra_time, xlim,
                textgrid, stimulus_onset)
        plot_pd_vid(ax2, vid_pd.data['pd'], video_time, xlim,
                    textgrid, stimulus_onset)
        plot_wav(ax3, wav, wav_time, xlim, textgrid, stimulus_onset)

        fig.align_ylabels()
        pdf.savefig()  # saves the current figure into a pdf page
        plt.close()
        _plot_logger.info("Drew PD plot in " + str(filename) + ".")


def draw_annd(recording, figure_dir, xlim=(-.05, 1.25)):
    filename = recording.meta['basename'] + '_annd.pdf'
    filename = figure_dir.joinpath(filename)

    with PdfPages(str(filename)) as pdf:
        fig = plt.figure(figsize=(9, 4))

        ax2 = plt.subplot2grid((4, 1), (0, 0), rowspan=3)
        plt.title(recording.meta['prompt'].split()[0])
        # plt.grid(True, 'major', 'x')
        ax2.axes.xaxis.set_ticklabels([])
        ax3 = plt.subplot2grid((4, 1), (3, 0))
        # plt.grid(True, 'major', 'x')

        audio = recording.modalities['MonoAudio']
        stimulus_onset = audio.meta['stimulus_onset']
        wav = audio.data
        wav_time = (audio.timevector - stimulus_onset)

        annd = recording.modalities['ANND on Splines']
        annd_time = annd.timevector - stimulus_onset

        textgrid = recording.textgrid

        plot_annd(ax2, annd.data['annd'], annd_time, xlim,
                  textgrid, stimulus_onset)
        plot_wav(ax3, wav, wav_time, xlim,
                 textgrid, stimulus_onset)

        fig.align_ylabels()
        pdf.savefig()  # saves the current figure into a pdf page
        plt.close()
        _plot_logger.info("Drew ANND plot in " + str(filename) + ".")


def draw_annd_pd(recording, figure_dir, xlim=(-.05, 1.25)):
    filename = recording.meta['basename'] + '_annd_pd.pdf'
    filename = figure_dir.joinpath(filename)

    with PdfPages(str(filename)) as pdf:
        fig = plt.figure(figsize=(9, 6))

        ax1 = plt.subplot2grid((7, 1), (0, 0), rowspan=3)
        plt.title(recording.meta['prompt'].split()[0])
        # plt.grid(True, 'major', 'x')
        ax1.axes.xaxis.set_ticklabels([])
        ax2 = plt.subplot2grid((7, 1), (3, 0), rowspan=3)
        # plt.grid(True, 'major', 'x')
        ax2.axes.xaxis.set_ticklabels([])
        ax3 = plt.subplot2grid((7, 1), (6, 0))
        # plt.grid(True, 'major', 'x')

        audio = recording.modalities['MonoAudio']
        stimulus_onset = audio.meta['stimulus_onset']
        wav = audio.data
        wav_time = (audio.timevector - stimulus_onset)

        ult_pd = recording.modalities['PD on RawUltrasound']
        ultra_time = ult_pd.timevector - stimulus_onset

        annd = recording.modalities['ANND on Splines']
        annd_time = annd.timevector - stimulus_onset

        textgrid = recording.textgrid

        plot_pd(ax1, ult_pd.data['pd'], ultra_time, xlim,
                textgrid, stimulus_onset)
        plot_annd(ax2, annd.data['annd'], annd_time, xlim,
                  textgrid, stimulus_onset)
        plot_wav(ax3, wav, wav_time, xlim,
                 textgrid, stimulus_onset)

        fig.align_ylabels()
        pdf.savefig()  # saves the current figure into a pdf page
        plt.close()
        _plot_logger.info("Drew PD and ANND plot in " + str(filename) + ".")


def draw_mpbpd_pd(recording, figure_dir, xlim=(-.05, 1.25)):
    filename = recording.meta['basename'] + '_mpbpd_pd.pdf'
    filename = figure_dir.joinpath(filename)

    with PdfPages(str(filename)) as pdf:
        fig = plt.figure(figsize=(9, 6))

        ax1 = plt.subplot2grid((7, 1), (0, 0), rowspan=3)
        plt.title(recording.meta['prompt'].split()[0])
        # plt.grid(True, 'major', 'x')
        ax1.axes.xaxis.set_ticklabels([])
        ax2 = plt.subplot2grid((7, 1), (3, 0), rowspan=3)
        # plt.grid(True, 'major', 'x')
        ax2.axes.xaxis.set_ticklabels([])
        ax3 = plt.subplot2grid((7, 1), (6, 0))
        # plt.grid(True, 'major', 'x')

        audio = recording.modalities['MonoAudio']
        stimulus_onset = audio.meta['stimulus_onset']
        wav = audio.data
        wav_time = (audio.timevector - stimulus_onset)

        ult_pd = recording.modalities['PD on RawUltrasound']
        ultra_time = ult_pd.timevector - stimulus_onset

        annd = recording.modalities['ANND on Splines']
        annd_time = annd.timevector - stimulus_onset

        textgrid = recording.textgrid

        plot_pd(ax1, ult_pd.data['pd'], ultra_time, xlim,
                textgrid, stimulus_onset)
        plot_mpbpd(ax2, annd.data['mpbpd'], annd_time, xlim,
                   textgrid, stimulus_onset)
        plot_wav(ax3, wav, wav_time, xlim,
                 textgrid, stimulus_onset)

        fig.align_ylabels()
        pdf.savefig()  # saves the current figure into a pdf page
        plt.close()
        _plot_logger.info("Drew PD and SPBPD plot in " + str(filename) + ".")


def draw_annd_mpbpd_pd(recording, figure_dir, xlim=(-.05, 1.25)):
    filename = recording.meta['basename'] + '_annd_mpbpd_pd.pdf'
    filename = figure_dir.joinpath(filename)

    with PdfPages(str(filename)) as pdf:
        fig = plt.figure(figsize=(9, 6))

        ax1 = plt.subplot2grid((7, 1), (0, 0), rowspan=3)
        plt.title(recording.meta['prompt'].split()[0])
        # plt.grid(True, 'major', 'x')
        ax1.axes.xaxis.set_ticklabels([])
        ax2 = plt.subplot2grid((7, 1), (3, 0), rowspan=3)
        # plt.grid(True, 'major', 'x')
        ax2.axes.xaxis.set_ticklabels([])
        ax3 = plt.subplot2grid((7, 1), (6, 0))
        # plt.grid(True, 'major', 'x')

        audio = recording.modalities['MonoAudio']
        stimulus_onset = audio.meta['stimulus_onset']
        wav = audio.data
        wav_time = (audio.timevector - stimulus_onset)

        ult_pd = recording.modalities['PD on RawUltrasound']
        ultra_time = ult_pd.timevector - stimulus_onset

        annd = recording.modalities['ANND on Splines']
        annd_time = annd.timevector - stimulus_onset

        textgrid = recording.textgrid

        plot_pd(ax1, ult_pd.data['pd'], ultra_time, xlim,
                textgrid, stimulus_onset)
        plot_annd_mpbpd(
            ax2, annd.data['annd'],
            annd.data['mpbpd'],
            annd_time, xlim, textgrid, stimulus_onset, plot_raw=False)
        plot_wav(ax3, wav, wav_time, xlim,
                 textgrid, stimulus_onset)

        fig.align_ylabels()
        pdf.savefig()  # saves the current figure into a pdf page
        plt.close()
        _plot_logger.info("Drew MPBPD and ANND plot in " + str(filename) + ".")


#####
# Iteration over recordings
#####

def CAW_2021_plots(recordings, figure_dir):
    figure_dir = Path(figure_dir)
    if not figure_dir.is_dir():
        if figure_dir.exists():
            _plot_logger.critical('Name conflict: ' + figure_dir +
                                  ' exists and is not a directory.')
        else:
            figure_dir.mkdir()

    for recording in recordings:
        if not recording.excluded:
            draw_pd_ult_and_vid(recording, figure_dir, xlim=(-.05, .85))


def ISSP2020_plots(recordings, figure_dir):
    figure_dir = Path(figure_dir)
    if not figure_dir.is_dir():
        if figure_dir.exists():
            _plot_logger.critical('Name conflict: ' + figure_dir +
                                  ' exists and is not a directory.')
        else:
            figure_dir.mkdir()

    for recording in recordings:
        # draw_mpbpd_pd(recording, figure_dir, xlim=(-.05, 1.5))
        # draw_annd_mpbpd_pd(recording, figure_dir, xlim=(-.05, 1.5))
        # draw_annd_pd(recording, figure_dir, xlim=(-.05, 1.5))
        # draw_annd(recording, figure_dir, xlim=(-.05, 1.5))
        draw_pd(recording, figure_dir, xlim=(-.05, 1.5))


#
# ISSP 2020 abstract plot
#
def draw_ISSP_2020(meta, data):

    filename = 'spaghetti_plot.pdf'
    with PdfPages(filename) as pdf:
        plt.figure(figsize=(9, 6))
        ax1 = plt.subplot2grid((7, 1), (0, 0), rowspan=3)
        plt.grid(True, 'major', 'x')
        ax2 = plt.subplot2grid((7, 1), (3, 0), rowspan=3)
        plt.grid(True, 'major', 'x')
        ax3 = plt.subplot2grid((7, 1), (6, 0))
        plt.grid(True, 'major', 'x')
        xlim = (-.05, 1)

        pd = data[0][0]
        annd = data[1][0]
        ultra_time = pd['ultra_time'] - pd['beep_uti']
        annd_time = annd['annd_time'] - pd['beep_uti']
        wav_time = pd['ultra_wav_time'] - pd['beep_uti']

        ax1.plot(ultra_time, pd['pd'], color="deepskyblue", lw=1)
        ax1.axvline(x=0, color="k", lw=1)
        ax1.set_xlim(xlim)
        ax1.set_ylim((0, 3000))
        ax1.set_ylabel("PD")

        # last annd seems to be shit so leave it out
        ax2.plot(annd_time[:-1], annd['annd'][:-1],
                 color="deepskyblue", lw=1, alpha=.15)
        ax2.plot(
            annd_time[3: -4],
            moving_average(annd['annd'][: -1],
                           n=7),
            color="deepskyblue", lw=1)
        ax2.axvline(x=0, color="k", lw=1)
        ax2.set_xlim(xlim)
        ax2.set_ylim((0, 1.45))
        ax2.set_ylabel("ANND")

        ax3.plot(
            wav_time, pd['ultra_wav_frames'] / np.amax(
                np.abs(pd['ultra_wav_frames'])),
            color="deepskyblue", lw=1)
        # ax3.axvline(x=0, color="k", lw=1)
        ax3.set_xlim(xlim)
        ax3.set_ylabel("Waveform")
        ax3.set_xlabel("Time (s), go-signal at 0 s.")

        plt.tight_layout()
        pdf.savefig()  # saves the current figure into a pdf page
        plt.close()
        _plot_logger.info("Drew spaghetti plot in " + filename + ".")


#
# Used for verifying test runs at the moment. Wrap later into it's own thing.
#
def draw_spaghetti(meta, data):
    filename = 'spaghetti_plot.pdf'
    with PdfPages(filename) as pdf:
        plt.figure(figsize=(7, 7))
        # ax = plt.subplot2grid((2,1),(1,0))
        ax = plt.axes()
        xlim = (-.2, 1)

        for i in range(len(data)):
            ultra_time = data[i]['ultra_time'] - data[i]['beep_uti']

            ax.plot(ultra_time, data[i]['pd'], color="b", lw=1, alpha=.2)
            ax.axvline(x=0, color="r", lw=1)
            ax.set_xlim(xlim)
            ax.set_ylabel("Pixel Difference")
            ax.set_xlabel("Time (s), go-signal at 0 s.")

        plt.tight_layout()
        pdf.savefig()  # saves the current figure into a pdf page
        plt.close()
        _plot_logger.info("Drew spaghetti plot in " + filename + ".")
