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

import numpy as np

from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt

# from matplotlib.figure import Figure
# from matplotlib.axes import Axes
# from matplotlib.lines import Line2D

from icecream import ic

from satkit.data_structures import Recording, RecordingSession
from satkit.configuration import publish_params

from .plot import (plot_satgrid_tier,
                   plot_spectrogram, plot_timeseries, plot_wav, plot_1d_modality)

_plot_logger = logging.getLogger('satkit.publish')


def make_figure(recording: Recording, pdf: PdfPages):

    figure, axes = plt.subplots(nrows=publish_params['subplot grid'][0],
                                ncols=publish_params['subplot grid'][1],
                                layout='constrained')
    # plt.clf()

    keys = publish_params['subplots'].keys()
    ic(keys)

    if publish_params['use go signal']:
        audio = recording.modalities['MonoAudio']
        time_offset = audio.go_signal
    else:
        time_offset = 0

    for key, ax in zip(keys, axes.flat):

        modality = recording.modalities[publish_params['subplots'][key]]
        plot_1d_modality(ax, modality, time_offset, publish_params['xlim'],
                         normalise=publish_params['normalise'])
        ax.set_title(publish_params['subplots'][key])

    # main_grid_spec = figure.add_gridspec(
    #     nrows=publish_params['subplot grid'][1],
    #     ncols=publish_params['subplot grid'][0],
    #     hspace=0,
    #     wspace=0)  # ,
    # height_ratios=height_ratios)

    # data_grid_spec = main_grid_spec[0].subgridspec(
    #     nro_data_modalities, 1, hspace=0, wspace=0)
    # data_axes.append(figure.add_subplot(data_grid_spec[0]))
    # for i in range(1, nro_data_modalities):
    #     data_axes.append(
    #         figure.add_subplot(
    #             data_grid_spec[i],
    #             sharex=data_axes[0]))

    figure.suptitle(f"{recording.basename} {recording.meta_data.prompt}")
    plt.xlabel('Time (s), go-signal at 0 s.)', fontsize=13)
    plt.ylabel('y axis', fontsize=13)
    pdf.savefig(plt.gcf())


def publish_pdf(recording_session: RecordingSession):
    with PdfPages('test.pdf') as pdf:
        for recording in recording_session.recordings:
            make_figure(recording, pdf)
