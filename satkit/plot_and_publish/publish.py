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
Functions for publishing results as images.

These are essentially plotting functions, but with emphasis more on composite
plots than atomic ones, and more on final results than graphs to be segmented
"""

from dataclasses import dataclass
from enum import Enum
import logging
import math
from typing import Optional

import numpy as np

from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

# from matplotlib.figure import Figure
# from matplotlib.axes import Axes
# from matplotlib.lines import Line2D

import pandas
import seaborn as sns

from icecream import ic

from satkit.data_structures import Recording, RecordingSession
from satkit.configuration import publish_params

from .plot import (plot_1d_modality, plot_satgrid_tier)

_plot_logger = logging.getLogger('satkit.publish')


@dataclass
class PublishParameters:
    plot_categories: tuple[str]
    within_plot_categories: tuple[float]
    legend_loc: str = "upper right"
    common_xlabel: Optional[str] = None
    common_ylabel: Optional[str] = None
    suptitle: Optional[str] = None
    horizontal_line: Optional[float] = None


class PeakStatistic(Enum):
    NUMBER_OF_PEAKS = 'number_of_peaks'
    NEAREST_NEIGHBOURS = 'nearest_neighbours'


class AggregationMethod(Enum):
    MEAN = 'mean'
    MEDIAN = 'median'
    MODE = 'mode'
    MSE = 'mse'
    STD = 'std'
    NONE = 'none'


class DistributionPlotParameters(PublishParameters):
    method: AggregationMethod


def publish_distribution_data_seaborn(
        data_frame: pandas.DataFrame,
        variable: str,
        plot_categories: str,
        within_plot_categories: str,
        pdf: PdfPages,
        plot_titles: Optional[list[str]] = None,
        category_titles: Optional[list[str]] = None,
        panel_height: float = 2,
        panel_aspect: float = 1.3,
        row_length: int = 2,
        common_xlabel: Optional[str] = None,
        common_ylabel: Optional[str] = None,
        suptitle: Optional[str] = None,
        ref_line_y: Optional[float] = None,
) -> None:
    # sns.set(font='serif', style=None, rc={
    #         'font.style': 'italic', 'text.usetex': True})
    grid = sns.catplot(
        data=data_frame, kind='violin',
        x=within_plot_categories, y=variable,
        col=plot_categories, col_wrap=2,
        height=panel_height, aspect=panel_aspect,
        cut=0, inner=None, native_scale=True
    )
    grid.map_dataframe(sns.swarmplot, data=data_frame,
                       x=within_plot_categories, y=variable,
                       size=2, native_scale=True, color='orange')

    if ref_line_y:
        grid.refline(y=ref_line_y, linestyle=':')

    if category_titles:
        grid.set_xticklabels(category_titles, step=1)

    # plot_categories = ["l$\infty$" if metric ==
    #                    "l_inf" else metric for metric in plot_categories]

    pdf.savefig(plt.gcf())


def publish_distribution_data(
        data: np.ndarray,
        plot_categories: tuple[str],
        within_plot_categories: tuple[float],
        pdf: PdfPages,
        figure_size: tuple[float, float] = None,
        subplot_layout: tuple[int, int] = None,
        legend_loc: str = "upper right",
        common_xlabel: Optional[str] = None,
        common_ylabel: Optional[str] = None,
        suptitle: Optional[str] = None,
        horizontal_line: Optional[float] = None,
) -> None:
    """

    Order of axes is assumed to be plot_categories, recordings, within plot
    categories. For example: norms, recordings, downsampling ratios (with
    original (==1) in position 0).

    Parameters
    ----------
    peak_number_ratios : _type_
        _description_
    values_of_p : tuple[str]
        _description_
    downsampling_ratios : tuple[int]
        _description_
    """
    if not figure_size:
        figure_size = (5, 4)

    if not subplot_layout:
        nrows = math.ceil(math.sqrt(len(plot_categories)))
        ncols = math.ceil(len(plot_categories) / nrows)
        subplot_layout = (nrows, ncols)

    figure, axes = plt.subplots(
        nrows=subplot_layout[0],
        ncols=subplot_layout[1],
        sharey=True, sharex=True,
        figsize=figure_size,
        gridspec_kw={'hspace': 0, 'wspace': 0}
    )

    plot_categories = ["l$\infty$" if metric ==
                       "l_inf" else metric for metric in plot_categories]

    for i, ax in enumerate(axes.flatten()):
        plot_parts = ax.violinplot(
            data[i, :, :], showextrema=True, showmedians=True)
        # for part in plot_parts['cmins']:
        #     part.set(linewidth=1)
        plot_parts['cmins'].set(lw=1)
        plot_parts['cmaxes'].set(lw=1)
        plot_parts['cbars'].set(lw=1)
        plot_parts['cmedians'].set(color='k', lw=2)

        if horizontal_line:
            ax.axhline(horizontal_line, color="black", linestyle="--", lw=1)

        if i in (4, 5):
            ax.set_xticks(np.arange(1, len(within_plot_categories) + 1),
                          labels=within_plot_categories)

        ax.legend(
            [plot_parts['cmins']], [plot_categories[i]],
            prop={'family': 'serif', 'style': 'italic'},
            loc=legend_loc,
            handlelength=0,
            handletextpad=0)

    if suptitle:
        figure.suptitle(suptitle)
    if common_ylabel:
        figure.text(0, 0.5, common_ylabel, va='center', rotation='vertical')
    if common_xlabel:
        figure.text(0.5, 0, common_xlabel, ha='center')

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
    # TODO: rename this function!
    figure = plt.figure(figsize=publish_params['figure size'])

    height_ratios = [3 for i in range(publish_params['subplot grid'][0])]
    height_ratios.append(1)
    gridspec = GridSpec(nrows=publish_params['subplot grid'][0]+1,
                        ncols=publish_params['subplot grid'][1],
                        hspace=0, wspace=0,
                        height_ratios=height_ratios)

    keys = list(publish_params['subplots'].keys())

    if publish_params['use go signal']:
        audio = recording['MonoAudio']
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

            modality = recording[publish_params['subplots'][key]]
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
