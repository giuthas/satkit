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

# Scientific plotting
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
    
    
