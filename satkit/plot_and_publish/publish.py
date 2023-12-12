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

# from icecream import ic

from satkit.data_structures import Recording, RecordingSession
from satkit.configuration import publish_params

from .plot import (Normalisation, plot_satgrid_tier,
                   plot_spectrogram, plot_timeseries, plot_wav)

_plot_logger = logging.getLogger('satkit.publish')


def make_figure(recording: Recording, pdf: PdfPages):
    plt.figure()
    plt.clf()

    # plt.plot()
    graph = plt.title('y vs x')
    plt.xlabel('x axis', fontsize=13)
    plt.ylabel('y axis', fontsize=13)
    pdf.savefig(plt.gcf())


def publish_pdf(recording_session: RecordingSession):
    with PdfPages('test.pdf') as pdf:
        for recording in recording_session.recordings:
            make_figure(recording, pdf)
