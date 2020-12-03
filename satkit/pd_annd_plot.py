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
import logging
import os.path

# Scientific plotting
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

_plot_logger = logging.getLogger('satkit.pd.plot')

def plot_signals_trace(beep, beep2, int_time, int_signal, hp_signal, bp_signal, int_signal2):
    fig = plt.figure()
    ax0 = fig.add_subplot(211)
    ax1 = fig.add_subplot(212)
    ax0.plot(int_time, int_signal)
    ax0.plot(int_time, int_signal2)
    y = [20, -200]
    ax0.plot([beep, beep], y, color="g")
    ax0.plot([beep2, beep2], y, color="r")
    ax1.plot(int_time, hp_signal)
    ax1.plot(int_time, bp_signal)
    ax1.plot([beep, beep], [-1, 1], color="g")
    ax1.plot([beep2, beep2], [-1, 1], color="r")
    plt.show()


# Wrapper for plotting, which also cals plt.show().
def plot_and_show(beep, ultra_d, ultra_time, uti_wav, uti_wav_time, beep_uti, center, name):
    plot_signals(beep, ultra_d, ultra_time, uti_wav, uti_wav_time, beep_uti, center, name)
    plt.show()


# To be used in silent plotting or called for plotting when calling plt.show() separately.
def plot_signals(beep, ultra_d, ultra_time, uti_wav, uti_wav_time, beep_uti, center, name):
    fig = plt.figure(figsize=(12, 10))
    
    ax1 = plt.subplot2grid((6,1),(2,0), rowspan=2)
    ax2 = plt.subplot2grid((6,1),(4,0))

    ultra_time = ultra_time - beep_uti
    uti_wav_time = uti_wav_time - beep_uti

    xlim = (-.2, 1)
#    xlim = (-4, 6)

    ax1.plot(ultra_time, ultra_d)
    ax1.axvline(x=0, color="r")
    if center:
        ax1.set_xlim(xlim)
    ax1.set_ylabel("Pixel Difference")

    ax2.plot(uti_wav_time, uti_wav)
    ax2.axvline(x=0, color="r")
    if center:
        ax2.set_xlim(xlim)
    ax3.set_ylabel("Waveform")
    ax3.set_xlabel("Time (s)")

    plt.suptitle(name, fontsize=24)
    #plt.tight_layout()


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
    


def moving_average(a, n=3) :
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n



    # change this into a internal function inside one that loops over tokens in meta and data
    # also create a figures or output directory to put the pics in
    # fetch the right tokens in and run once to see files are produced right
    # then expand output as follows
    # needs to do pd + wav, annd + wav, pd+annd+wav in separate files for each token


def ISSP2020_plots(metalist, datalist, figure_dir):
    for i in range(len(metalist)):
        meta = metalist[i]
        data = datalist[i]
        basename = os.path.basename(meta['ult_prompt_file'])
        basename = os.path.splitext(basename)[0]
        draw_annd_pd(meta, data, basename, figure_dir)
        draw_annd(meta, data, basename, figure_dir)
        draw_pd(meta, data, basename, figure_dir)


def ultrafest2020_plots(metalist, datalist, figure_dir):
    for i in range(len(metalist)):
        meta = metalist[i]
        data = datalist[i]
        basename = os.path.basename(meta['ult_prompt_file'])
        basename = os.path.splitext(basename)[0]
        draw_annd_pd(meta, data, basename, figure_dir)
        draw_annd(meta, data, basename, figure_dir)
        draw_pd(meta, data, basename, figure_dir)

        
def plot_pd(ax, pd, ultra_time, xlim):
    # ax.plot(ultra_time, pd['pd'], color="b", lw=1)
    # ax.plot(ultra_time, pd['l1']/100, color="r", lw=1)
    # ax.plot(ultra_time, pd['l3']*5, color="g", lw=1)
    # ax.plot(ultra_time, pd['l10']*20, color="k", lw=1)
    # ax.plot(ultra_time, pd['l_inf']*20, color="k", lw=1, linestyle='--')

    ax.plot(ultra_time, pd['pd']/np.max(pd['pd'][1:]), color="b", lw=1)
    ax.plot(ultra_time, pd['l1']/np.max(pd['l1'][1:]), color="r", lw=1)
    ax.plot(ultra_time, pd['l3']/np.max(pd['l3'][1:]), color="g", lw=1)
    ax.plot(ultra_time, pd['l10']/np.max(pd['l10'][1:]), color="k", lw=1)
    ax.plot(ultra_time, pd['l_inf']/np.max(pd['l_inf'][1:]), color="k", lw=1, linestyle='--')

    ax.axvline(x=0, color="k", lw=1)
    ax.set_xlim(xlim)
    ax.set_ylim((0,1.1))
#    ax.set_ylim((0,4520))
    ax.set_ylabel("PD")


def plot_annd(ax, annd, annd_time, xlim):
    # last annd seems to be shit so leave it out
    ax.plot(annd_time[:-1], annd['annd'][:-1], color="b", lw=1, alpha=.5)
    ax.plot(annd_time[3:-4], moving_average(annd['annd'][:-1], n=7), color="b", lw=1)
    ax.plot(annd_time[:-1], annd['mnnd'][:-1], color="g", lw=1, alpha=.5)
    ax.plot(annd_time[3:-4], moving_average(annd['mnnd'][:-1], n=7), color="g", lw=1)
    ax.plot(annd_time[:-1], annd['spline_md'][:-1], color="r", lw=1, alpha=.5)
    ax.plot(annd_time[3:-4], moving_average(annd['spline_md'][:-1], n=7), color="r", lw=1)
    ax.axvline(x=0, color="k", lw=1)
    ax.set_xlim(xlim)
    ax.set_ylim((0,2.05))
    ax.set_ylabel("ANND")

    
def plot_wav(ax, pd, wav_time, xlim):
        ax.plot(wav_time, pd['ultra_wav_frames']/np.amax(np.abs(pd['ultra_wav_frames'])), color="b", lw=1)
        #ax.axvline(x=0, color="k", lw=1)
        ax.set_xlim(xlim)
        ax.set_ylabel("Waveform")
        ax.set_xlabel("Time (s), go-signal at 0 s.")

        
#
# Ultrafest 2020 poster plotting 
#
def draw_annd_pd(meta, data, basename, figure_dir):
    filename = os.path.join(figure_dir, (basename + '_annd_pd.pdf'))

    with PdfPages(filename) as pdf:
        fig = plt.figure(figsize=(9, 6))

        ax1 = plt.subplot2grid((7,1),(0,0), rowspan=3)
        plt.title(meta['prompt'])
        plt.grid(True, 'major', 'x')
        ax1.axes.xaxis.set_ticklabels([])
        ax2 = plt.subplot2grid((7,1),(3,0), rowspan=3)
        plt.grid(True, 'major', 'x')
        ax2.axes.xaxis.set_ticklabels([])
        ax3 = plt.subplot2grid((7,1),(6,0))
        plt.grid(True, 'major', 'x')
        xlim = (-.05, 1.9)

        pd = data['pd']
        annd = data['annd']
        ultra_time = pd['ultra_time'] - pd['beep_uti']
        annd_time = annd['annd_time'] - pd['beep_uti']
        wav_time = pd['ultra_wav_time'] - pd['beep_uti']
        
        plot_pd(ax1, pd, ultra_time, xlim)
        plot_annd(ax2, annd, annd_time, xlim)
        plot_wav(ax3, pd, wav_time, xlim)

        fig.align_ylabels()        
        pdf.savefig()  # saves the current figure into a pdf page
        plt.close()
        _plot_logger.info("Drew PD and ANND plot in " + filename + ".")

        
def draw_annd(meta, data, basename, figure_dir):
    filename = os.path.join(figure_dir, (basename + '_annd.pdf'))

    with PdfPages(filename) as pdf:
        fig = plt.figure(figsize=(9, 4))

        ax2 = plt.subplot2grid((4,1),(0,0), rowspan=3)
        plt.title(meta['prompt'])
        plt.grid(True, 'major', 'x')
        ax2.axes.xaxis.set_ticklabels([])
        ax3 = plt.subplot2grid((4,1),(3,0))
        plt.grid(True, 'major', 'x')
        xlim = (-.05, 1)

        pd = data['pd']
        annd = data['annd']
        ultra_time = pd['ultra_time'] - pd['beep_uti']
        annd_time = annd['annd_time'] - pd['beep_uti']
        wav_time = pd['ultra_wav_time'] - pd['beep_uti']
        
        plot_annd(ax2, annd, annd_time, xlim)
        plot_wav(ax3, pd, wav_time, xlim)

        fig.align_ylabels()        
        pdf.savefig()  # saves the current figure into a pdf page
        plt.close()
        _plot_logger.info("Drew ANND plot in " + filename + ".")


def draw_pd(meta, data, basename, figure_dir):
    filename = os.path.join(figure_dir, (basename + 'pd.pdf'))

    with PdfPages(filename) as pdf:
        fig = plt.figure(figsize=(9, 4))

        ax1 = plt.subplot2grid((4,1),(0,0), rowspan=3)
        plt.title(meta['prompt'])
        plt.grid(True, 'major', 'x')
        ax1.axes.xaxis.set_ticklabels([])
        ax3 = plt.subplot2grid((4,1),(3,0))
        plt.grid(True, 'major', 'x')
        xlim = (-1.5, 1.5)

        pd = data['pd']
        ultra_time = pd['ultra_time'] - pd['beep_uti']
        wav_time = pd['ultra_wav_time'] - pd['beep_uti']
        
        plot_pd(ax1, pd, ultra_time, xlim)
        plot_wav(ax3, pd, wav_time, xlim)

        fig.align_ylabels()        
        pdf.savefig()  # saves the current figure into a pdf page
        plt.close()
        _plot_logger.info("Drew PD plot in " + filename + ".")



#
# ISSP 2020 abstract plot
#
def draw_ISSP_2020(meta, data):
    
    filename = 'spaghetti_plot.pdf'
    with PdfPages(filename) as pdf:
        plt.figure(figsize=(9, 6))
        ax1 = plt.subplot2grid((7,1),(0,0), rowspan=3)
        plt.grid(True, 'major', 'x')
        ax2 = plt.subplot2grid((7,1),(3,0), rowspan=3)
        plt.grid(True, 'major', 'x')
        ax3 = plt.subplot2grid((7,1),(6,0))
        plt.grid(True, 'major', 'x')
        xlim = (-.05, 1)


        pd = data[0][0]
        annd = data[1][0]
        ultra_time = pd['ultra_time'] - pd['beep_uti']
        annd_time = annd['annd_time'] - pd['beep_uti']
        wav_time = pd['ultra_wav_time'] - pd['beep_uti']
        
        ax1.plot(ultra_time, pd['pd'], color="b", lw=1)
        ax1.axvline(x=0, color="k", lw=1)
        ax1.set_xlim(xlim)
        ax1.set_ylim((0,3000))
        ax1.set_ylabel("PD")

        # last annd seems to be shit so leave it out
        ax2.plot(annd_time[:-1], annd['annd'][:-1], color="b", lw=1, alpha=.15)
        ax2.plot(annd_time[3:-4], moving_average(annd['annd'][:-1], n=7), color="b", lw=1)
        ax2.axvline(x=0, color="k", lw=1)
        ax2.set_xlim(xlim)
        ax2.set_ylim((0,1.45))
        ax2.set_ylabel("ANND")

        ax3.plot(wav_time, pd['ultra_wav_frames']/np.amax(np.abs(pd['ultra_wav_frames'])), color="b", lw=1)
        #ax3.axvline(x=0, color="k", lw=1)
        ax3.set_xlim(xlim)
        ax3.set_ylabel("Waveform")
        ax3.set_xlabel("Time (s), go-signal at 0 s.")

        plt.tight_layout()
        pdf.savefig()  # saves the current figure into a pdf page
        plt.close()
        _plot_logger.info("Drew spaghetti plot in " + filename + ".")

