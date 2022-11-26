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
from typing import List, Optional, Tuple, Union

# Efficient array operations
import numpy as np
# Scientific plotting
from matplotlib.axes import Axes
from matplotlib.lines import Line2D
from satkit.data_structures.satgrid import SatTier
# Local packages
from satkit.gui.boundary_animation import AnimatableBoundary, BoundaryAnimator

_plot_logger = logging.getLogger('satkit.plot')



def plot_timeseries(axes: Axes, 
            data: np.ndarray, 
            time: np.ndarray, 
            xlim: Tuple[float, float], 
            ylim: Optional[Tuple[float, float]]=None, 
            label: str="PD on ultrasound",
            picker=None, 
            color: str="deepskyblue", 
            alpha: float=1.0):
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
    textgrid -- a textgrids module textgrid object.
    stimulus_onset -- onset time of the stimulus in the recording in
        seconds.
    picker -- a picker tied to the plotted PD curve to facilitate
        annotation.

    Returns None.
    """
    if picker:
        axes.plot(time, data, color=color, lw=1, picker=picker, alpha=alpha)
    else:
        axes.plot(time, data, color=color, lw=1, alpha=alpha)
    # The official fix for the above curve not showing up on the legend.
    timeseries = Line2D([], [], color=color, lw=1)

    go_line = axes.axvline(x=0, color="dimgrey", lw=1, linestyle=(0, (5, 10)))

    axes.set_xlim(xlim)
    if not ylim:
        axes.set_ylim((-50, 3050))
    else:
        axes.set_ylim(ylim)

    axes.set_ylabel(label)

    lines = [timeseries, go_line]

    return lines

# TODO: move this to the annotator as a one-liner
def legend(axis, timeseries, go_line=None, segment_line=None, location='upper_right'):
    if segment_line:
        axis.legend((timeseries, go_line, segment_line),
                  ('Pixel difference', 'Go-signal onset', 'Acoustic segments'),
                  loc=location)
    else:
        axis.legend((timeseries, go_line),
                  ('Pixel difference', 'Go-signal onset'),
                  loc=location)


def plot_satgrid_tier(axes: Axes, 
                    tier: SatTier, 
                    time_offset: float=0, 
                    draw_text: bool=True, 
                    text_y: float=500
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
        picker=None):
    normalised_wav = waveform / np.amax(np.abs(waveform))

    line = None
    if picker:
        line = ax.plot(wav_time, normalised_wav, color="k", lw=1, picker=picker)
    else:
        line = ax.plot(wav_time, normalised_wav, color="k", lw=1)

    ax.axvline(x=0, color="dimgrey", lw=1, linestyle=(0, (5, 10)))

    ax.set_xlim(xlim)
    ax.set_ylim((-1.05, 1.05))
    ax.set_ylabel("Wave")

    return line

