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

def moving_average(a, n=3) :
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n


#####
# Subplot functions
#####

def plot_pd(ax, pd, ultra_time, xlim, textgrid = None, time_offset = 0, picker=None):
    text_settings = {'horizontalalignment': 'center',
                     'verticalalignment': 'center'}

    # The PD curve and the official fix for it not showing up on the legend.
    ax.plot(ultra_time, pd['pd'], color="deepskyblue", lw=1, picker=picker)
    pd_curve = mlines.Line2D([], [], color="deepskyblue", lw=1)

    go_line = ax.axvline(x=0, color="dimgrey", lw=1, linestyle=(0, (5, 10)))

    if textgrid:
        for segment in textgrid['segment']:
            if segment.text == "":
                continue
            elif segment.text == "beep":
                continue
            else:
                segment_line = ax.axvline(x = segment.xmin+time_offset,
                                          color="dimgrey", lw=1, linestyle='--')
                ax.axvline(x = segment.xmax+time_offset,
                           color="dimgrey", lw=1, linestyle='--')
                ax.text(segment.mid+time_offset, 500, segment.text, text_settings,
                        color="dimgrey")
            
    ax.set_xlim(xlim)
    ax.set_ylim((-50,3050))
    ax.legend((pd_curve, go_line, segment_line),
              ('Pixel difference', 'Go-signal onset', 'Acoustic segments'),
              loc='upper right')
    ax.set_ylabel("PD")

    
def plot_l1(ax, pd, ultra_time, xlim, textgrid = None, time_offset = 0, picker=None):
    text_settings = {'horizontalalignment': 'center',
                     'verticalalignment': 'center'}

    # The PD curve and the official fix for it not showing up on the legend.
    ax.plot(ultra_time, pd['l1']/np.max(pd['l1'][1:]), color="deepskyblue", lw=1, picker=picker)
    ax.plot(ultra_time, pd['pd']/np.max(pd['pd'][1:]), color="g", lw=1)
    pd_curve = mlines.Line2D([], [], color="deepskyblue", lw=1)

    go_line = ax.axvline(x=0, color="dimgrey", lw=1, linestyle=(0, (5, 10)))

    if textgrid:
        for segment in textgrid['segment']:
            if segment.text == "":
                continue
            elif segment.text == "beep":
                continue
            else:
                segment_line = ax.axvline(x = segment.xmin+time_offset,
                                          color="dimgrey", lw=1, linestyle='--')
                ax.axvline(x = segment.xmax+time_offset,
                           color="dimgrey", lw=1, linestyle='--')
                ax.text(segment.mid+time_offset, 500, segment.text, text_settings,
                        color="dimgrey")
            
    ax.set_xlim(xlim)
    # ax.set_ylim((-50,3050))
    ax.legend((pd_curve, go_line, segment_line),
              ('Pixel difference: l1 norm', 'Go-signal onset', 'Acoustic segments'),
              loc='upper right')
    ax.set_ylabel("PD")

    
def plot_pd_peak_normalised(ax, pd, ultra_time, xlim, textgrid = None, time_offset = 0):
    text_settings = {'horizontalalignment': 'center',
                     'verticalalignment': 'center'}
    
    ax.plot(ultra_time, pd['pd']/np.max(pd['pd'][1:]),
            color="deepskyblue", lw=1, label='Pixel difference')

    go_line = ax.axvline(x=0, color="dimgrey", lw=1, linestyle=(0, (5, 10)))
    # ax.axvline(x=0, color="g", lw=1)

    if textgrid:
        for segment in textgrid['segment']:
            if segment.text == "":
                continue
            elif segment.text == "beep":
                continue
            else:
                ax.axvline(x = segment.xmin+time_offset, color="dimgrey", lw=1,
                           linestyle='--')
                ax.axvline(x = segment.xmax+time_offset, color="dimgrey", lw=1,
                           linestyle='--')
                ax.text(segment.mid+time_offset, 500, segment.text, text_settings,
                        color="dimgrey")
            
    ax.set_xlim(xlim)
    ax.set_ylim((0,1.1))
    ax.legend(loc='upper right') 
    ax.set_ylabel("Peak normalised PD")

    
def plot_pd_norms(ax, pd, ultra_time, xlim, textgrid = None, time_offset = 0):
    ax.plot(ultra_time, pd['l1']/np.max(pd['l1'][1:]), color="black", lw=1)
    ax.plot(ultra_time, pd['pd']/np.max(pd['pd'][1:]), color="dimgrey", lw=1)
    ax.plot(ultra_time, pd['l3']/np.max(pd['l3'][1:]), color="grey", lw=1)
    ax.plot(ultra_time, pd['l4']/np.max(pd['l4'][1:]), color="darkgrey", lw=1)
    ax.plot(ultra_time, pd['l5']/np.max(pd['l5'][1:]), color="silver", lw=1)
    ax.plot(ultra_time, pd['l10']/np.max(pd['l10'][1:]), color="lightgrey", lw=1)
    ax.plot(ultra_time, pd['l_inf']/np.max(pd['l_inf'][1:]), color="k", lw=1, linestyle='--')

    go_line = ax.axvline(x=0, color="dimgrey", lw=1, linestyle=(0, (5, 10)))

    ax.set_xlim(xlim)
    ax.set_ylim((0,1.1))
    ax.set_ylabel("PD")


def plot_annd_mpbpd(ax, annd, annd_time, xlim, textgrid = None, time_offset = 0, picker=None,
              plot_raw=True):
    half_window = 2
    smooth_length = 2*half_window+1

    # last annd seems to be broken so leave it out    
    # ax.plot(annd_time[:-1], annd['annd'][:-1], color="deepskyblue", lw=1, alpha=.5)
    ave_annd = moving_average(annd['annd'][:-1], n=smooth_length)
    ax.plot(annd_time[half_window:-(half_window+1)], ave_annd/np.max(ave_annd),
            color="orange", lw=1, label='Average Nearest Neighbour Distance')

    ave_mpbpd = moving_average(annd['mpbpd'][:-1], n=smooth_length)

    if plot_raw:
        ax.plot(annd_time[:-1], annd['mpbpd'][:-1]/np.max(ave_mpbpd),
                color="seagreen", lw=1, alpha=.4)

    if picker:
        ax.plot(annd_time[half_window:-(half_window+1)], ave_mpbpd/np.max(ave_mpbpd),
                color="seagreen", lw=1, label='Median Point-by-point Distance',
                picker=picker)
    else:
        ax.plot(annd_time[half_window:-(half_window+1)], ave_mpbpd/np.max(ave_mpbpd),
                color="seagreen", lw=1, label='Median Point-by-point Distance')

    go_line = ax.axvline(x=0, color="dimgrey", lw=1, linestyle=(0, (5, 10)))

    if textgrid:
        for segment in textgrid['segment']:
            if segment.text == "":
                continue
            elif segment.text == "beep":
                continue
            else:
                ax.axvline(x = segment.xmin+time_offset, color="dimgrey", lw=1, linestyle='--')
                ax.axvline(x = segment.xmax+time_offset, color="dimgrey", lw=1, linestyle='--')

    ax.set_xlim(xlim)
    ax.set_ylim((-0.05,1.05))
    ax.legend(loc='upper right')
    ax.set_ylabel("Peak normalised\nspline metrics")

    
def plot_annd(ax, annd, annd_time, xlim, textgrid = None, time_offset = 0, picker=None,
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

    go_line = ax.axvline(x=0, color="dimgrey", lw=1, linestyle=(0, (5, 10)))

    if textgrid:
        for segment in textgrid['segment']:
            if segment.text == "":
                continue
            elif segment.text == "beep":
                continue
            else:
                ax.axvline(x = segment.xmin+time_offset, color="dimgrey", lw=1, linestyle='--')
                ax.axvline(x = segment.xmax+time_offset, color="dimgrey", lw=1, linestyle='--')

    ax.set_xlim(xlim)
    ax.set_ylim((-0.05,1.05))
    ax.legend(loc='upper right')
    ax.set_ylabel("Peak normalised ANND")

    
def plot_mpbpd(ax, annd, annd_time, xlim, textgrid = None, time_offset = 0, picker=None,
               plot_raw=True):
    half_window = 2
    smooth_length = 2*half_window+1

    ave_mpbpd = moving_average(annd['mpbpd'][:-1], n=smooth_length)
    if plot_raw:
        ax.plot(annd_time[:-1], annd['mpbpd'][:-1]/np.max(ave_mpbpd),
                color="seagreen", lw=1, alpha=.4)

    if picker:
        ax.plot(annd_time[half_window:-(half_window+1)], ave_mpbpd/np.max(ave_mpbpd),
                color="seagreen", lw=1, label='Median Point-by-point Distance',
                picker=picker)
    else:
        ax.plot(annd_time[half_window:-(half_window+1)], ave_mpbpd/np.max(ave_mpbpd),
                color="seagreen", lw=1, label='Median Point-by-point Distance')

    go_line = ax.axvline(x=0, color="dimgrey", lw=1, linestyle=(0, (5, 10)))

    if textgrid:
        for segment in textgrid['segment']:
            if segment.text == "":
                continue
            elif segment.text == "beep":
                continue
            else:
                ax.axvline(x = segment.xmin+time_offset, color="dimgrey", lw=1, linestyle='--')
                ax.axvline(x = segment.xmax+time_offset, color="dimgrey", lw=1, linestyle='--')

    ax.set_xlim(xlim)
    ax.set_ylim((-0.05,1.05))
    ax.legend(loc='upper right')
    ax.set_ylabel("Peak normalised MPBPD")

    
def plot_spline_metrics(ax, annd, annd_time, xlim, textgrid = None, time_offset = 0):
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
    ax.plot(annd_time[:-1], annd['mpbpd'][:-1]/np.max(ave_mpbpd), color="g", lw=1, alpha=.5)
    ax.plot(annd_time[half_window:-(half_window+1)], ave_mpbpd/np.max(ave_mpbpd),
            color="grey", lw=1, linestyle='--')

    # ax.plot(annd_time[:-1], annd['spline_d'][:-1], color="k", lw=1, alpha=.5)
    ave_spline_d = moving_average(annd['spline_d'][:-1], n=smooth_length)
    ax.plot(annd_time[half_window:-(half_window+1)], ave_spline_d/np.max(ave_spline_d),
            color="darkgrey", lw=1, linestyle='-.')

    ave_spline_l1 = moving_average(annd['spline_l1'][:-1], n=smooth_length)
    #ax.plot(annd_time[:-1], annd['spline_l1'][:-1]/np.max(ave_spline_l1),
    #        color="seagreen", lw=1, alpha=.5)
    ax.plot(annd_time[half_window:-(half_window+1)], ave_spline_l1/np.max(ave_spline_l1),
            color="seagreen", lw=1, linestyle='-.')

    if textgrid:
        for segment in textgrid['segment']:
            if segment.text == "":
                continue
            elif segment.text == "beep":
                continue
            else:
                ax.axvline(x = segment.xmin+time_offset, color="dimgrey", lw=1, linestyle='--')
                ax.axvline(x = segment.xmax+time_offset, color="dimgrey", lw=1, linestyle='--')

    go_line = ax.axvline(x=0, color="dimgrey", lw=1, linestyle=(0, (5, 10)))
    ax.set_xlim(xlim)
    ax.set_ylim((0,1.05))
    ax.set_ylabel("Peak normalised spline metrics")

    
def plot_annd_options(ax, annd, annd_time, xlim, textgrid = None, time_offset = 0):
    # last annd seems to be shit so leave it out
    ax.plot(annd_time[:-1], annd['annd'][:-1], color="deepskyblue", lw=1, alpha=.5)
    ax.plot(annd_time[3:-4], moving_average(annd['annd'][:-1], n=7), color="deepskyblue", lw=1)
    ax.plot(annd_time[:-1], annd['mnnd'][:-1], color="g", lw=1, alpha=.5)
    ax.plot(annd_time[3:-4], moving_average(annd['mnnd'][:-1], n=7), color="g", lw=1)
    ax.plot(annd_time[:-1], annd['mpbpd'][:-1], color="r", lw=1, alpha=.5)
    ax.plot(annd_time[3:-4], moving_average(annd['mpbpd'][:-1], n=7), color="r", lw=1)
    ax.plot(annd_time[:-1], annd['spline_d'][:-1], color="k", lw=1, alpha=.5)
    ax.plot(annd_time[3:-4], moving_average(annd['spline_d'][:-1], n=7), color="k", lw=1)

    if textgrid:
        for segment in textgrid['segment']:
            if segment.text == "":
                continue
            elif segment.text == "beep":
                continue
            else:
                ax.axvline(x = segment.xmin+time_offset, color="dimgrey", lw=1, linestyle='--')
                ax.axvline(x = segment.xmax+time_offset, color="dimgrey", lw=1, linestyle='--')

    go_line = ax.axvline(x=0, color="dimgrey", lw=1, linestyle=(0, (5, 10)))
    ax.axvline(x=0, color="k", lw=1)
    ax.set_xlim(xlim)
    ax.set_ylim((0,2.05))
    ax.set_ylabel("ANND")

    
def plot_wav(ax, pd, wav_time, xlim, textgrid = None, time_offset = 0, picker=None):
    normalised_wav = pd['ultra_wav_frames']/np.amax(np.abs(pd['ultra_wav_frames']))
    if picker:
        ax.plot(wav_time, normalised_wav, color="k", lw=1, picker=picker)
    else:
        ax.plot(wav_time, normalised_wav, color="k", lw=1)

    go_line = ax.axvline(x=0, color="dimgrey", lw=1, linestyle=(0, (5, 10)))

    if textgrid:
        for segment in textgrid['segment']:
            if segment.text == "":
                continue
            elif segment.text == "beep":
                continue
            else:
                ax.axvline(x = segment.xmin+time_offset, color="dimgrey", lw=1, linestyle='--')
                ax.axvline(x = segment.xmax+time_offset, color="dimgrey", lw=1, linestyle='--')

    ax.set_xlim(xlim)
    ax.set_ylim((-1.05,1.05))
    ax.set_ylabel("Waveform")
    ax.set_xlabel("Time (s), go-signal at 0 s.")
                
            
#####
# Combined plots
#####

def draw_pd(meta, datum, figure_dir, xlim=(-.05, 1.25)):
    base_name = Path(meta['base_name'])      
    filename = base_name.name + '_pd.pdf'
    filename = figure_dir.joinpath(filename)
    
    with PdfPages(str(filename)) as pdf:
        fig = plt.figure(figsize=(9, 4))

        ax1 = plt.subplot2grid((4,1),(0,0), rowspan=3)
        plt.title(meta['prompt'].split()[0])
        #plt.grid(True, 'major', 'x')
        ax1.axes.xaxis.set_ticklabels([])
        ax3 = plt.subplot2grid((4,1),(3,0))
        #plt.grid(True, 'major', 'x')

        pd = datum['pd']
        ultra_time = pd['ultra_time'] - pd['beep_uti']
        wav_time = pd['ultra_wav_time'] - pd['beep_uti']
        
        plot_pd(ax1, pd, ultra_time, xlim, meta['textgrid'], -pd['beep_uti'])
        plot_wav(ax3, pd, wav_time, xlim, meta['textgrid'], -pd['beep_uti'])

        fig.align_ylabels()        
        pdf.savefig()  # saves the current figure into a pdf page
        plt.close()
        _plot_logger.info("Drew PD plot in " + str(filename) + ".")

        
def draw_annd(meta, datum, figure_dir, xlim=(-.05, 1.25)):
    base_name = Path(meta['base_name'])      
    filename = base_name.name + '_annd.pdf'
    filename = figure_dir.joinpath(filename)
    
    with PdfPages(str(filename)) as pdf:
        fig = plt.figure(figsize=(9, 4))

        ax2 = plt.subplot2grid((4,1),(0,0), rowspan=3)
        plt.title(meta['prompt'].split()[0])
        #plt.grid(True, 'major', 'x')
        ax2.axes.xaxis.set_ticklabels([])
        ax3 = plt.subplot2grid((4,1),(3,0))
        #plt.grid(True, 'major', 'x')

        pd = datum['pd']
        annd = datum['annd']
        annd_time = annd['annd_time'] - pd['beep_uti']
        wav_time = pd['ultra_wav_time'] - pd['beep_uti']
        
        plot_annd(ax2, annd, annd_time, xlim, meta['textgrid'], -pd['beep_uti'])
        plot_wav(ax3, pd, wav_time, xlim, meta['textgrid'], -pd['beep_uti'])

        fig.align_ylabels()        
        pdf.savefig()  # saves the current figure into a pdf page
        plt.close()
        _plot_logger.info("Drew ANND plot in " + str(filename) + ".")


def draw_annd_pd(meta, datum, figure_dir, xlim=(-.05, 1.25)):
    base_name = Path(meta['base_name'])      
    filename = base_name.name + '_annd_pd.pdf'
    filename = figure_dir.joinpath(filename)
    
    with PdfPages(str(filename)) as pdf:
        fig = plt.figure(figsize=(9, 6))

        ax1 = plt.subplot2grid((7,1),(0,0), rowspan=3)
        plt.title(meta['prompt'].split()[0])
        #plt.grid(True, 'major', 'x')
        ax1.axes.xaxis.set_ticklabels([])
        ax2 = plt.subplot2grid((7,1),(3,0), rowspan=3)
        #plt.grid(True, 'major', 'x')
        ax2.axes.xaxis.set_ticklabels([])
        ax3 = plt.subplot2grid((7,1),(6,0))
        #plt.grid(True, 'major', 'x')

        pd = datum['pd']
        annd = datum['annd']
        ultra_time = pd['ultra_time'] - pd['beep_uti']
        annd_time = annd['annd_time'] - pd['beep_uti']
        wav_time = pd['ultra_wav_time'] - pd['beep_uti']
        
        plot_pd(ax1, pd, ultra_time, xlim, meta['textgrid'], -pd['beep_uti'])
        plot_annd(ax2, annd, annd_time, xlim, meta['textgrid'], -pd['beep_uti'])
        plot_wav(ax3, pd, wav_time, xlim, meta['textgrid'], -pd['beep_uti'])

        fig.align_ylabels()        
        pdf.savefig()  # saves the current figure into a pdf page
        plt.close()
        _plot_logger.info("Drew PD and ANND plot in " + str(filename) + ".")

        
def draw_mpbpd_pd(meta, datum, figure_dir, xlim=(-.05, 1.25)):
    base_name = Path(meta['base_name'])      
    filename = base_name.name + '_mpbpd_pd.pdf'
    filename = figure_dir.joinpath(filename)
    
    with PdfPages(str(filename)) as pdf:
        fig = plt.figure(figsize=(9, 6))

        ax1 = plt.subplot2grid((7,1),(0,0), rowspan=3)
        plt.title(meta['prompt'].split()[0])
        #plt.grid(True, 'major', 'x')
        ax1.axes.xaxis.set_ticklabels([])
        ax2 = plt.subplot2grid((7,1),(3,0), rowspan=3)
        #plt.grid(True, 'major', 'x')
        ax2.axes.xaxis.set_ticklabels([])
        ax3 = plt.subplot2grid((7,1),(6,0))
        #plt.grid(True, 'major', 'x')

        pd = datum['pd']
        annd = datum['annd']
        ultra_time = pd['ultra_time'] - pd['beep_uti']
        annd_time = annd['annd_time'] - pd['beep_uti']
        wav_time = pd['ultra_wav_time'] - pd['beep_uti']
        
        plot_pd(ax1, pd, ultra_time, xlim, meta['textgrid'], -pd['beep_uti'])
        plot_mpbpd(ax2, annd, annd_time, xlim, meta['textgrid'], -pd['beep_uti'])
        plot_wav(ax3, pd, wav_time, xlim, meta['textgrid'], -pd['beep_uti'])

        fig.align_ylabels()        
        pdf.savefig()  # saves the current figure into a pdf page
        plt.close()
        _plot_logger.info("Drew PD and SPBPD plot in " + str(filename) + ".")

        
def draw_annd_mpbpd_pd(meta, datum, figure_dir, xlim=(-.05, 1.25)):
    base_name = Path(meta['base_name'])      
    filename = base_name.name + '_annd_mpbpd_pd.pdf'
    filename = figure_dir.joinpath(filename)
    
    with PdfPages(str(filename)) as pdf:
        fig = plt.figure(figsize=(9, 6))

        ax1 = plt.subplot2grid((7,1),(0,0), rowspan=3)
        plt.title(meta['prompt'].split()[0])
        #plt.grid(True, 'major', 'x')
        ax1.axes.xaxis.set_ticklabels([])
        ax2 = plt.subplot2grid((7,1),(3,0), rowspan=3)
        #plt.grid(True, 'major', 'x')
        ax2.axes.xaxis.set_ticklabels([])
        ax3 = plt.subplot2grid((7,1),(6,0))
        #plt.grid(True, 'major', 'x')

        pd = datum['pd']
        annd = datum['annd']
        ultra_time = pd['ultra_time'] - pd['beep_uti']
        annd_time = annd['annd_time'] - pd['beep_uti']
        wav_time = pd['ultra_wav_time'] - pd['beep_uti']
        
        plot_pd(ax1, pd, ultra_time, xlim, meta['textgrid'], -pd['beep_uti'])
        plot_annd_mpbpd(ax2, annd, annd_time, xlim, meta['textgrid'], -pd['beep_uti'],
                        plot_raw=False)
        plot_wav(ax3, pd, wav_time, xlim, meta['textgrid'], -pd['beep_uti'])

        fig.align_ylabels()        
        pdf.savefig()  # saves the current figure into a pdf page
        plt.close()
        _plot_logger.info("Drew MPBPD and ANND plot in " + str(filename) + ".")

        
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
        draw_mpbpd_pd(meta, datum, figure_dir, xlim=(-.05, 1.5))
        draw_annd_mpbpd_pd(meta, datum, figure_dir, xlim=(-.05, 1.5))
        draw_annd_pd(meta, datum, figure_dir, xlim=(-.05, 1.5))
        draw_annd(meta, datum, figure_dir, xlim=(-.05, 1.5))
        draw_pd(meta, datum, figure_dir, xlim=(-.05, 1.5))


def norm_comparison_plots(metalist, datalist, figure_dir):
    for i in range(len(metalist)):
        meta = metalist[i]
        data = datalist[i]
        basename = os.path.basename(meta['ult_prompt_file'])
        basename = os.path.splitext(basename)[0]
        draw_annd_pd(meta, data, basename, figure_dir)
        draw_annd(meta, data, basename, figure_dir)
        draw_pd_norms(meta, data, basename, figure_dir)
        


def ultrafest2020_plots(metalist, datalist, figure_dir):
    for i in range(len(metalist)):
        meta = metalist[i]
        data = datalist[i]
        basename = os.path.basename(meta['ult_prompt_file'])
        basename = os.path.splitext(basename)[0]
        draw_annd_pd(meta, data, basename, figure_dir)
        draw_annd(meta, data, basename, figure_dir)
        draw_pd(meta, data, basename, figure_dir)


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
        
        ax1.plot(ultra_time, pd['pd'], color="deepskyblue", lw=1)
        ax1.axvline(x=0, color="k", lw=1)
        ax1.set_xlim(xlim)
        ax1.set_ylim((0,3000))
        ax1.set_ylabel("PD")

        # last annd seems to be shit so leave it out
        ax2.plot(annd_time[:-1], annd['annd'][:-1], color="deepskyblue", lw=1, alpha=.15)
        ax2.plot(annd_time[3:-4], moving_average(annd['annd'][:-1], n=7), color="deepskyblue", lw=1)
        ax2.axvline(x=0, color="k", lw=1)
        ax2.set_xlim(xlim)
        ax2.set_ylim((0,1.45))
        ax2.set_ylabel("ANND")

        ax3.plot(wav_time, pd['ultra_wav_frames']/np.amax(np.abs(pd['ultra_wav_frames'])), color="deepskyblue", lw=1)
        #ax3.axvline(x=0, color="k", lw=1)
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
    

