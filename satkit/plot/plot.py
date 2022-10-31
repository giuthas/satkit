#
# Copyright (c) 2019-2022 Pertti Palo, Scott Moisik, Matthew Faytak, and Motoki Saito.
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
import sys

# Scientific plotting
import matplotlib.lines as mlines
# Efficient array operations
import numpy as np
# Local packages
from satkit.gui.annotation_boundary import AnnotationBoundary

_plot_logger = logging.getLogger('satkit.plot')



def plot_pd(axis, pd, time, xlim, ylim=None, textgrid=None, stimulus_onset=0,
            picker=None, color="deepskyblue", alpha=1.0):
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
    if picker:
        axis.plot(time, pd, color=color, lw=1, picker=picker, alpha=alpha)
    else:
        axis.plot(time, pd, color=color, lw=1, alpha=alpha)
    pd_curve = mlines.Line2D([], [], color=color, lw=1)

    go_line = axis.axvline(x=0, color="dimgrey", lw=1, linestyle=(0, (5, 10)))

    segment_line = None
    boundaries = None
    if textgrid:
        segment_line, boundaries = plot_textgrid_lines(axis, textgrid, stimulus_onset)

    axis.set_xlim(xlim)
    if not ylim:
        axis.set_ylim((-50, 3050))
    else:
        axis.set_ylim(ylim)

    if segment_line:
        axis.legend((pd_curve, go_line, segment_line),
                  ('Pixel difference', 'Go-signal onset', 'Acoustic segments'),
                  loc='upper right')
    else:
        axis.legend((pd_curve, go_line),
                  ('Pixel difference', 'Go-signal onset'),
                  loc='upper right')
    axis.set_ylabel("PD on ultrasound")

    return boundaries

def plot_textgrid_lines(ax, textgrid, stimulus_onset=0, draw_text=True, draggable=True, text_y=500):
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
    if 'segment' in textgrid:
        segments = textgrid['segment']
    elif 'segments' in textgrid:
        segments = textgrid['segments']
    elif 'Segments' in textgrid:
        segments = textgrid['Segments']
    else:
        _plot_logger.critical("Could not guess the name of the segment tier. Exiting.")
        sys.exit()

    # TODO: convert this to draw boundaries and text in two separate passes so that 
    # all boundaries can be made editable

    last_segment = None
    lines = []
    for segment in segments:
        line = ax.axvline(
            x=segment.xmin - stimulus_onset, 
            color="dimgrey", 
            lw=1,
            linestyle='--')
        lines.append(line)
        last_segment = segment
        if draw_text:
            ax.text(segment.mid - stimulus_onset, text_y, segment.text,
                    text_settings, color="dimgrey")
    if last_segment:
        last_line = ax.axvline(x=last_segment.xmax - stimulus_onset,
                        color="dimgrey", lw=1, linestyle='--')
        lines.append(last_line)

    boundaries = []
    for line in lines:
        if draggable:
            boundary = AnnotationBoundary(line)
            boundary.connect()
            boundaries.append(boundary)
    return last_line, boundaries

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
    boundaries = None
    if textgrid:
        segment_line, boundaries = plot_textgrid_lines(
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

    return boundaries
