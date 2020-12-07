#
# Copyright (c) 2019-2020 Pertti Palo, Scott Moisik, and Matthew Faytak.
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
from pathlib import Path
import logging

# Efficient vector operations
import numpy as np

# Scientific plotting
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

_plot_logger = logging.getLogger('satkit.pd.plot')


#####
# Subplot functions
#####

def plot_pd(ax, pd, ultra_time, xlim):
    ax.plot(ultra_time, pd['pd'], color="b", lw=1)

    ax.axvline(x=0, color="k", lw=1)
    ax.set_xlim(xlim)
    ax.set_ylim((0,2000))
    ax.set_ylabel("PD")

    
def plot_pd_peak_normalised(ax, pd, ultra_time, xlim):
    ax.plot(ultra_time, pd['pd']/np.max(pd['pd'][1:]), color="k", lw=1)

    ax.axvline(x=0, color="k", lw=1)
    ax.set_xlim(xlim)
    ax.set_ylim((0,1.1))
    ax.set_ylabel("PD")

    
def plot_wav(ax, pd, wav_time, xlim):
    normalised_wav = pd['ultra_wav_frames']/np.amax(np.abs(pd['ultra_wav_frames']))
    ax.plot(wav_time, normalised_wav, color="b", lw=1)
    ax.set_xlim(xlim)
    ax.set_ylim((-1.05,1.05))
    ax.set_ylabel("Waveform")
    ax.set_xlabel("Time (s), go-signal at 0 s.")

    
#####
# Combined plots
#####

def draw_pd(meta, pd, figure_dir):
    base_name = Path(meta['base_name'])      
    filename = base_name.with_suffix('.pdf').name
    filename = figure_dir.joinpath(filename)
    
    with PdfPages(str(filename)) as pdf:
        fig = plt.figure(figsize=(9, 4))

        ax1 = plt.subplot2grid((4,1),(0,0), rowspan=3)
        plt.title(meta['prompt'].split()[1])
        plt.grid(True, 'major', 'x')
        ax1.axes.xaxis.set_ticklabels([])
        ax3 = plt.subplot2grid((4,1),(3,0))
        plt.grid(True, 'major', 'x')
        xlim = (-1., 1.)

        ultra_time = pd['ultra_time'] - pd['beep_uti']
        wav_time = pd['ultra_wav_time'] - pd['beep_uti']
        
        plot_pd(ax1, pd, ultra_time, xlim)
        plot_wav(ax3, pd, wav_time, xlim)

        fig.align_ylabels()        
        pdf.savefig()  # saves the current figure into a pdf page
        plt.close()
        _plot_logger.info("Drew PD plot in " + str(filename) + ".")



#####
# Iteration over tokens
#####

def ISSP2020_plots(meta_list, data, figure_dir):
    figure_dir = Path(figure_dir)
    if not figure_dir.is_dir():
        if figure_dir.exists():
            _plot_logger.critical('Name conflict: ' + figure_dir +
                                  ' exists and is not a directory.')
        else:
            figure_dir.mkdir()
    
    for (meta, datum) in zip(meta_list, data):
        draw_pd(meta, datum, figure_dir)

    
    
#
# Used for verifying test runs at the moment. Wrap later into it's own thing.
#
def draw_spaghetti(meta, data):
    filename = 'spaghetti_plot.pdf'
    with PdfPages(filename) as pdf:
        plt.figure(figsize=(7, 7))
        #ax = plt.subplot2grid((2,1),(1,0))
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
