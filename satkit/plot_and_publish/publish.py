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

import logging
from typing import Optional

import numpy as np

from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

# from matplotlib.figure import Figure
# from matplotlib.axes import Axes
# from matplotlib.lines import Line2D

# from icecream import ic

from satkit.data_structures import Recording, RecordingSession
from satkit.configuration import publish_params

from .plot import (plot_1d_modality, plot_satgrid_tier)

_plot_logger = logging.getLogger('satkit.publish')


def publish_downsampling_data(
        peak_number_ratios,
        metrics: tuple[str],
        downsampling_ratios: tuple[int],
        frequencies: tuple[float],
        pdf: PdfPages,
        suptitle: str,
        hline: Optional[float] = None,
) -> None:
    """

    Order of axes is assumed to be norms, recordings, downsampling ratios (with
    original (==1) in position 0)

    Parameters
    ----------
    peak_number_ratios : _type_
        _description_
    values_of_p : tuple[str]
        _description_
    downsampling_ratios : tuple[int]
        _description_
    """
    # figure = plt.figure(figsize=(10, 8))
    # # height_ratios = [3 for i in range(publish_params['subplot grid'][0])]
    # # height_ratios.append(1)
    # gridspec = GridSpec(nrows=3,
    #                     ncols=2,
    #                     # hspace=0, wspace=0,
    #                     # height_ratios=height_ratios
    #                     )
    figure, axes = plt.subplots(
        nrows=3,
        ncols=2,
        sharey=True,
        figsize=(10, 8),
        gridspec_kw={'hspace': 0, 'wspace': 0}
    )

    for i, ax in enumerate(axes.flatten()):
        plot_parts = ax.violinplot(
            peak_number_ratios[i, :, :], showextrema=True, showmedians=True)
        # for part in plot_parts['cmins']:
        #     part.set(linewidth=1)
        plot_parts['cmins'].set(lw=1)
        plot_parts['cmaxes'].set(lw=1)
        plot_parts['cbars'].set(lw=1)
        plot_parts['cmedians'].set(color='k', lw=2)

        if hline:
            ax.axhline(hline, color="black", linestyle="--", lw=1)
            # x = range(len(downsampling_ratios)+1)
            # hlines = np.ones(len(downsampling_ratios)+1) * hline
            # # , linestyle="--")
            # ax.scatter(x, hlines, marker='o', color="orange", s=30, zorder=3)

        if i in (4, 5):
            ax.set_xticks(np.arange(1, len(frequencies) + 1),
                          labels=frequencies)
            ax.set_xlabel("Data sampling frequency")

        ax.legend(
            [plot_parts['cmins']], [metrics[i]],
            loc='upper right',
            handlelength=0,
            handletextpad=0)

    figure.suptitle(suptitle)
    # figure.text(0.5, 0.04, 'Time (s), go-signal at 0 s.',
    #             ha='center', va='center', fontsize=10)

    plt.tight_layout()

    pdf.savefig(plt.gcf())


def make_figure(recording: Recording, pdf: PdfPages):
    """
    Create a figure from the recording and write it out to the pdf.

    Settings will have been read from satkit_publish_parameters.yaml in the
    configuration folder unless another setting file has been specified either
    on the commandline or in configuration/configuration.yaml.

    Parameters
    ----------
    recording : Recording
        The Recording to draw. 
    pdf : PdfPages
        A PdfPages instance to draw into.
    """
    figure = plt.figure(figsize=publish_params['figure size'])

    height_ratios = [3 for i in range(publish_params['subplot grid'][0])]
    height_ratios.append(1)
    gridspec = GridSpec(nrows=publish_params['subplot grid'][0]+1,
                        ncols=publish_params['subplot grid'][1],
                        hspace=0, wspace=0,
                        height_ratios=height_ratios)

    keys = list(publish_params['subplots'].keys())

    if publish_params['use go signal']:
        audio = recording.modalities['MonoAudio']
        time_offset = audio.go_signal
    else:
        time_offset = 0

    for i, grid in enumerate(gridspec):
        ax = plt.subplot(grid,)

        if i < len(keys):
            key = keys[i]
            ax.tick_params(
                axis='x',          # changes apply to the x-axis
                which='both',      # both major and minor ticks are affected
                bottom=False,      # ticks along the bottom edge are off
                top=False,         # ticks along the top edge are off
                labelbottom=False)  # labels along the bottom edge are off
            ax.tick_params(
                axis='y',         # changes apply to the x-axis
                which='both',     # both major and minor ticks are affected
                labelsize=8
            )
            if 'yticks' in publish_params:
                ax.set_yticks(publish_params['yticks'])
                ax.set_yticklabels(publish_params['yticklabels'])

            modality = recording.modalities[publish_params['subplots'][key]]
            line = plot_1d_modality(
                ax, modality, time_offset, publish_params['xlim'],
                normalise=publish_params['normalise'])

            ax.legend(
                [line], [modality.metadata.metric],
                loc='upper left',
                handlelength=publish_params["legend"]["handlelength"],
                handletextpad=publish_params["legend"]["handletextpad"])

            if publish_params['plotted tier'] in recording.satgrid:
                tier = recording.satgrid[publish_params['plotted tier']]

                plot_satgrid_tier(
                    ax, tier, time_offset=time_offset,
                    draw_text=False)

            if i % 2 != 0:
                ax.yaxis.set_label_position("right")
                ax.yaxis.tick_right()
        else:
            if publish_params['plotted tier'] in recording.satgrid:
                tier = recording.satgrid[publish_params['plotted tier']]

                ax.set_xlim(publish_params['xlim'])
                ax.tick_params(
                    axis='y',         # changes apply to the x-axis
                    which='both',     # both major and minor ticks are affected
                    left=False,       # ticks along the bottom edge are off
                    right=False,      # ticks along the top edge are off
                    labelleft=False)  # labels along the bottom edge are off
                ax.tick_params(
                    axis='x',         # changes apply to the x-axis
                    which='both',     # both major and minor ticks are affected
                    labelsize=8
                )
                if 'xticks' in publish_params:
                    ax.set_xticks(publish_params['xticks'])
                    ax.set_xticklabels(publish_params['xticklabels'])

                plot_satgrid_tier(
                    ax, tier, time_offset=time_offset,
                    draw_text=True, text_y=.45)

    figure.suptitle(f"{recording.basename} {recording.meta_data.prompt}")
    figure.text(0.5, 0.04, 'Time (s), go-signal at 0 s.',
                ha='center', va='center', fontsize=10)
    plt.xlabel(' ', fontsize=10)

    plt.tight_layout()

    pdf.savefig(plt.gcf())


def publish_pdf(recording_session: RecordingSession):
    """
    Draw all Recordings in the RecordingSession into a pdf file.

    The filename is read from configuration (likely satkit_publish_config.yaml
    or similar specified in the main config file.)

    Excluded Recordings are skipped.

    Parameters
    ----------
    recording_session : RecordingSession
        The RecordingSession containing the Recordings.
    """
    with PdfPages(publish_params['output file']) as pdf:
        for recording in recording_session.recordings:
            if not recording.excluded:
                make_figure(recording, pdf)
