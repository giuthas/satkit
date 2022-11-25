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
from matplotlib.lines import Line2D
from satkit.data_structures.satgrid import SatTier
# Local packages
from satkit.gui.boundary_animation import AnimatableBoundary, BoundaryAnimator

_plot_logger = logging.getLogger('satkit.plot')



def plot_timeseries(axis, 
            data: np.ndarray, 
            time: np.ndarray, 
            label: Optional[str],
            xlim: Tuple[float, float], 
            ylim: Optional[Tuple[float, float]]=None, 
            tier: Optional[SatTier]=None, 
            other_axis=None,
            stimulus_onset: float=0,
            picker=None, 
            color: str="deepskyblue", 
            alpha: float=1.0):
    """
    Plot a timeseries.

    The timeseries most likely comes from a Modality, but 
    that is left up to the caller. 
    
    If tier is specified, will call 
    plot_satgrid_tier to decorate the current axis with boundaries 
    of that tier. No annotation lables are currently drawn.

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

    # The PD curve and the official fix for it not showing up on the legend.
    if picker:
        axis.plot(time, data, color=color, lw=1, picker=picker, alpha=alpha)
    else:
        axis.plot(time, data, color=color, lw=1, alpha=alpha)
    pd_curve = Line2D([], [], color=color, lw=1)

    go_line = axis.axvline(x=0, color="dimgrey", lw=1, linestyle=(0, (5, 10)))

    segment_line = None
    boundaries = None
    if tier:
        segment_line, boundaries = plot_satgrid_tier(
            axis, tier, other_axes=other_axis, stimulus_onset=stimulus_onset, draw_text=False)

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

def plot_satgrid_tier(main_axis, 
                    tier: SatTier, 
                    other_axes=None, 
                    stimulus_onset: float=0, 
                    draw_text: bool=True, 
                    draggable: bool=True, 
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
    data_axes -- 
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
    axes = []
    if not other_axes:
        axes = [main_axis]
    else:
        axes = [main_axis]
        axes.extend(other_axes)

    text_settings = {'horizontalalignment': 'center',
                     'verticalalignment': 'center'}

    line = None
    prev_text = None
    text = None
    animators = []
    for segment in tier:
        for ax in axes:
            line = ax.axvline(
                x=segment.begin - stimulus_onset, 
                color="dimgrey", 
                lw=1,
                linestyle='--')
        if draw_text and segment.text:
            prev_text = text
            text = main_axis.text(segment.mid - stimulus_onset, 
                            text_y, segment.text,
                            text_settings, color="dimgrey")
        if draggable:
            boundary = AnimatableBoundary(line, prev_text, text)
            animator = BoundaryAnimator(boundary, other_axes, 
                                        segment, stimulus_onset)
            animator.connect()
            animators.append(animator)
    return line, animators
    

def plot_wav(
        ax, waveform, wav_time, xlim, tier=None, time_offset=0,
        picker=None, draw_legend=False):
    normalised_wav = waveform / np.amax(np.abs(waveform))
    if picker:
        ax.plot(wav_time, normalised_wav, color="k", lw=1, picker=picker)
    else:
        ax.plot(wav_time, normalised_wav, color="k", lw=1)

    ax.axvline(x=0, color="dimgrey", lw=1, linestyle=(0, (5, 10)))

    segment_line = None
    boundaries = None
    if tier:
        segment_line, boundaries = plot_satgrid_tier(
            ax, tier, time_offset, draw_text=False)

    if draw_legend:
        wave_curve = Line2D([], [], color="k", lw=1)
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
    # ax.set_xlabel("Time (s), go-signal at 0 s.")

    return boundaries

