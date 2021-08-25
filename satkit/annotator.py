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
import csv
import logging
from pathlib import Path
import time

from abc import ABC, abstractmethod

import matplotlib.pyplot as plt
from matplotlib.text import Text
from matplotlib.widgets import Button, RadioButtons, TextBox

import numpy as np
from numpy.random import rand

# local modules
from satkit import annd
from satkit import pd
from satkit.pd_annd_plot import plot_mpbpd, plot_pd, plot_l1, plot_wav

_annotator_logger = logging.getLogger('satkit.curveannotator')


class CurveAnnotator(ABC):
    """ 
    Annotator is an abstract base class for GUIs for annotating speech data.
    """

    def __init__(self, recordings, args, xlim=(-0.1, 1.0), figsize=(15, 8)):
        self.index = 0
        self.max_index = len(recordings)

        self.recordings = recordings
        self.commanlineargs = args

        self.fig = plt.figure(figsize=figsize)
        self.keypress_id = self.fig.canvas.mpl_connect(
            'key_press_event', self.on_key)

        self.xlim = xlim

    @abstractmethod
    def draw_plots(self):
        pass

    @abstractmethod
    def updateUI(self):
        """ 
        Updates parts of the UI outwith the graphs.
        """
        pass

    @abstractmethod
    def clear_axis(self):
        pass

    def update(self):
        """ 
        Updates the graphs but not the buttons.
        """
        self.clear_axis()
        self.draw_plots()
        self.fig.canvas.draw()

    def _get_title(self):
        """ 
        Private helper function for generating the title.
        """
        text = 'SATKIT Annotator'
        text += ', prompt: ' + self.current.meta['prompt']
        text += ', token: ' + str(self.index+1) + '/' + str(self.max_index)
        return text

    @property
    def current(self):
        return self.recordings[self.index]

    def next(self, event):
        """ 
        Callback function for the Next button.
        Increases cursor index, updates the view.
        """
        if self.index < self.max_index-1:
            self.index += 1
            self.update()
            self.updateUI()

    def prev(self, event):
        """ 
        Callback function for the Previous button.
        Decreases cursor index, updates the view.
        """
        if self.index > 0:
            self.index -= 1
            self.update()
            self.updateUI()

    @abstractmethod
    def save(self, event):
        pass

    def on_key(self, event):
        """ 
        Callback function for keypresses.

        Right and left arrows move to the next and previous token. 
        Pressing 's' saves the annotations in a csv-file.
        Pressing 'q' seems to be captured by matplotlib and interpeted as quit.
        """
        if event.key == "right":
            self.next(event)
        elif event.key == "left":
            self.prev(event)
        elif event.key == "s":
            self.save(event)

    @abstractmethod
    def onpick(self, event):
        pass

    @staticmethod
    def line_xdirection_picker(line, mouseevent):
        """
        Find the nearest point in the x (time) direction from the mouseclick in
        data coordinates. Return index of selected point, x and y coordinates of 
        the data at that point, and inaxes to enable originating subplot to be 
        identified.
        """
        if mouseevent.xdata is None:
            return False, dict()
        xdata = line.get_xdata()
        ydata = line.get_ydata()
        d = np.abs(xdata - mouseevent.xdata)

        ind = np.argmin(d)
        if 1:
            pickx = np.take(xdata, ind)
            picky = np.take(ydata, ind)
            props = dict(ind=ind,
                         pickx=pickx,
                         picky=picky,
                         inaxes=mouseevent.inaxes)
            return True, props
        else:
            return False, dict()


class PD_Annotator(CurveAnnotator):
    """ 
    PD_Annotator is a GUI class for annotating PD curves.

    The annotator works with PD curves and allows 
    selection of a single points (labelled as pdOnset in the saved file).
    The GUI also displays the waveform, and if TextGrids
    are provided, the acoustic segment boundaries.
    """

    def __init__(self, recordings, args, xlim=(-0.1, 1.0),
                 figsize=(15, 6),
                 categories=['Stable', 'Hesitation', 'Chaos', 'No data',
                             'Not set']):
        """ 
        Constructor for the PD_Annotator GUI. 

        Also sets up internal state and adds keys [pdCategory, splineCategory, 
        pdOnset, splineOnset] to the data argument. For the categories -1 is used
        to mark 'not set', and for the onsets -1.0.
        """
        super().__init__(recordings, args, xlim, figsize)

        self.categories = categories

        for token in self.recordings:
            token.annotations['pdCategory'] = -1
            token.annotations['splineCategory'] = -1
            token.annotations['pdOnset'] = -1.0
            token.annotations['splineOnset'] = -1.0

        #
        # Subplot grid shape
        #
        sbuplot_grid = (4, 7)

        #
        # Graphs to be annotated and the waveform for reference.
        #
        self.ax1 = plt.subplot2grid(sbuplot_grid, (0, 0), rowspan=3, colspan=6)
        self.ax3 = plt.subplot2grid(sbuplot_grid, (3, 0), colspan=6)

        self.draw_plots()

        self.fig.align_ylabels()
        self.fig.canvas.mpl_connect('pick_event', self.onpick)

        #
        # Buttons and such.
        #
        self.ax4 = plt.subplot2grid(sbuplot_grid, (0, 6), rowspan=2)
        self.ax4.axes.set_axis_off()
        self.pdCategoryRB = RadioButtons(
            self.ax4, self.categories,
            active=self.current.annotations['pdCategory'])
        self.pdCategoryRB.on_clicked(self.pdCatCB)

        self.axnext = plt.axes([0.85, 0.225, 0.1, 0.055])
        self.bnext = Button(self.axnext, 'Next')
        self.bnext.on_clicked(self.next)

        self.axprev = plt.axes([0.85, 0.15, 0.1, 0.055])
        self.bprev = Button(self.axprev, 'Previous')
        self.bprev.on_clicked(self.prev)

        self.axsave = plt.axes([0.85, 0.05, 0.1, 0.055])
        self.bsave = Button(self.axsave, 'Save')
        self.bsave.on_clicked(self.save)

        plt.show()

    def draw_plots(self):
        """ 
        Updates title and graphs. Called by self.update().
        """
        self.ax1.set_title(self._get_title())
        self.ax1.axes.xaxis.set_ticklabels([])

        audio = self.current.modalities['AAA_audio']
        stimulus_onset = audio.meta['stimulus_onset']
        wav = audio.data
        wav_time = (audio.timevector - stimulus_onset)

        pd = self.current.modalities['ultrasound PD']
        ultra_time = pd.timevector - stimulus_onset

        textgrid = self.current.textgrid

        plot_pd(
            self.ax1, pd.data['pd'],
            ultra_time, self.xlim, textgrid, stimulus_onset,
            picker=CurveAnnotator.line_xdirection_picker)
        plot_wav(self.ax3, wav, wav_time, self.xlim, textgrid, stimulus_onset)

        if self.current.annotations['pdOnset'] > -1:
            self.ax1.axvline(x=self.current.annotations['pdOnset'],
                             linestyle=':', color="deepskyblue", lw=1)
            self.ax3.axvline(x=self.current.annotations['pdOnset'],
                             linestyle=':', color="deepskyblue", lw=1)

    def clear_axis(self):
        self.ax1.cla()
        self.ax3.cla()

    def updateUI(self):
        """ 
        Updates parts of the UI outwith the graphs.
        """
        self.pdCategoryRB.set_active(self.current.annotations['pdCategory'])

    def save(self, event):
        """ 
        Callback funtion for the Save button.
        Currently overwrites what ever is at 
        local_data/onsets.csv
        """
        # eventually get this from commandline/caller/dialog window
        filename = 'local_data/PD_MPBPD_onsets.csv'
        fieldnames = ['pdCategory', 'pdOnset']
        csv.register_dialect('tabseparated', delimiter='\t',
                             quoting=csv.QUOTE_NONE)

        with closing(open(filename, 'w')) as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames, extrasaction='ignore',
                                    dialect='tabseparated')

            writer.writeheader()
            for token in self.recordings:
                writer.writerow(token)
            print('Wrote onset data in file ' + filename + '.')
            _annotator_logger.debug(
                'Wrote onset data in file ' + filename + '.')

    def pdCatCB(self, event):
        """ 
        Callback funtion for the RadioButton for catogorising 
        the PD curve.
        """
        self.current.annotations['pdCategory'] = self.categories.index(
            event)

    def onpick(self, event):
        """
        Callback for handling time selection on events.
        """
        subplot = 0
        for i, ax in enumerate([self.ax1]):
            # For infomation, print which axes the click was in
            if ax == event.inaxes:
                subplot = i+1
                break

        if subplot == 1:
            self.current.annotations['pdOnset'] = event.pickx

        self.update()


class PD_MPBPD_Annotator(CurveAnnotator):
    """ 
    PD_MPBPD_Annotator is a GUI class for annotating PD and MPBPD curves.

    The annotator works with PD and MPBPD curves and allows 
    selection of single points (labelled as [metric]Onset in the saved file)
    -- one per curve. The GUI also displays the waveform, and if TextGrids
    are provided, the acoustic segment boundaries.
    """

    def __init__(self, recordings, args, xlim=(-0.1, 1.0),
                 figsize=(15, 8),
                 categories=['Stable', 'Hesitation', 'Chaos', 'No data',
                             'Not set']):
        """ 
        Constructor for the PD_MPBPD_Annotator GUI. 

        Also sets up internal state and adds keys [pdCategory, splineCategory, 
        pdOnset, splineOnset] to the data argument. For the categories -1 is used
        to mark 'not set', and for the onsets -1.0.
        """
        super().__init__(recordings, args, xlim, figsize)

        self.categories = categories

        for token in self.recordings:
            token['pdCategory'] = -1
            token['splineCategory'] = -1
            token['pdOnset'] = -1.0
            token['splineOnset'] = -1.0

        #
        # Subplot grid shape
        #
        sbuplot_grid = (7, 7)

        #
        # Graphs to be annotated and the waveform for reference.
        #
        self.ax1 = plt.subplot2grid(sbuplot_grid, (0, 0), rowspan=3, colspan=6)
        self.ax2 = plt.subplot2grid(sbuplot_grid, (3, 0), rowspan=3, colspan=6)
        self.ax3 = plt.subplot2grid(sbuplot_grid, (6, 0), colspan=6)

        self.draw_plots()

        self.fig.align_ylabels()
        self.fig.canvas.mpl_connect('pick_event', self.onpick)

        #
        # Buttons and such.
        #
        self.ax4 = plt.subplot2grid(sbuplot_grid, (0, 6), rowspan=2)
        self.ax4.axes.set_axis_off()
        self.pdCategoryRB = RadioButtons(
            self.ax4, self.categories,
            active=self.current.annotations['pdCategory'])
        self.pdCategoryRB.on_clicked(self.pdCatCB)

        self.ax5 = plt.subplot2grid(sbuplot_grid, (3, 6), rowspan=2)
        self.ax5.axes.set_axis_off()
        self.splineCategoryRB = RadioButtons(
            self.ax5, self.categories,
            active=self.current.annotations['splineCategory'])
        self.splineCategoryRB.on_clicked(self.splineCatCB)

        self.axnext = plt.axes([0.85, 0.225, 0.1, 0.055])
        self.bnext = Button(self.axnext, 'Next')
        self.bnext.on_clicked(self.next)

        self.axprev = plt.axes([0.85, 0.15, 0.1, 0.055])
        self.bprev = Button(self.axprev, 'Previous')
        self.bprev.on_clicked(self.prev)

        self.axsave = plt.axes([0.85, 0.05, 0.1, 0.055])
        self.bsave = Button(self.axsave, 'Save')
        self.bsave.on_clicked(self.save)

        plt.show()

    def draw_plots(self):
        """ 
        Updates title and graphs. Called by self.update().
        """
        self.ax1.set_title(self._get_title())
        self.ax1.axes.xaxis.set_ticklabels([])
        self.ax2.axes.xaxis.set_ticklabels([])

        audio = self.current.modalities['AAA_audio']
        stimulus_onset = audio.meta['stimulus_onset']
        wav = audio.data
        wav_time = (audio.timevector - stimulus_onset)

        pd = self.current.modalities['ultrasound PD']
        ultra_time = pd.timevector - stimulus_onset

        annd = self.current.modalities['annd']
        annd_time = annd.timevector - stimulus_onset

        textgrid = self.current.textgrid

        plot_pd(
            self.ax1, pd.data['pd'],
            ultra_time, self.xlim, textgrid, stimulus_onset,
            picker=CurveAnnotator.line_xdirection_picker)
        plot_mpbpd(
            self.ax2, annd.data, annd_time, self.xlim, textgrid,
            stimulus_onset, picker=CurveAnnotator.line_xdirection_picker,
            plot_raw=True)
        plot_wav(self.ax3, wav, wav_time, self.xlim, textgrid, stimulus_onset)

        if self.current.annotations['pdOnset'] > -1:
            self.ax1.axvline(x=self.current.annotations['pdOnset'],
                             linestyle=':', color="deepskyblue", lw=1)
            self.ax2.axvline(x=self.current.annotations['pdOnset'],
                             linestyle=':', color="deepskyblue", lw=1)
            self.ax3.axvline(x=self.current.annotations['pdOnset'],
                             linestyle=':', color="deepskyblue", lw=1)
        if self.current.annotations['splineOnset'] > -1:
            self.ax1.axvline(x=self.current.annotations['splineOnset'],
                             linestyle='-.', color="seagreen", lw=1)
            self.ax2.axvline(x=self.current.annotations['splineOnset'],
                             linestyle='-.', color="seagreen", lw=1)
            self.ax3.axvline(x=self.current.annotations['splineOnset'],
                             linestyle='-.', color="seagreen", lw=1)

    def clear_axis(self):
        self.ax1.cla()
        self.ax2.cla()
        self.ax3.cla()

    def updateUI(self):
        """ 
        Updates parts of the UI outwith the graphs.
        """
        self.pdCategoryRB.set_active(self.current.annotations['pdCategory'])
        self.splineCategoryRB.set_active(
            self.current.annotations['splineCategory'])

    def save(self, event):
        """ 
        Callback funtion for the Save button.
        Currently overwrites what ever is at 
        local_data/onsets.csv
        """
        # eventually get this from commandline/caller/dialog window
        filename = 'local_data/PD_MPBPD_onsets.csv'
        fieldnames = ['pdCategory', 'splineCategory', 'pdOnset', 'splineOnset']
        csv.register_dialect('tabseparated', delimiter='\t',
                             quoting=csv.QUOTE_NONE)

        with closing(open(filename, 'w')) as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames, extrasaction='ignore',
                                    dialect='tabseparated')

            writer.writeheader()
            for token in self.recordings:
                writer.writerow(token)
            print('Wrote onset data in file ' + filename + '.')
            _annotator_logger.debug(
                'Wrote onset data in file ' + filename + '.')

    def pdCatCB(self, event):
        """ 
        Callback funtion for the RadioButton for catogorising 
        the PD curve.
        """
        self.current.annotations['pdCategory'] = self.categories.index(
            event)

    def splineCatCB(self, event):
        """ 
        Callback funtion for the RadioButton for catogorising 
        the curve of the spline metric.
        """
        self.current.annotations['splineCategory'] = self.categories.index(
            event)

    def onpick(self, event):
        """
        Callback for handling time selection on events.
        """
        subplot = 0
        for i, ax in enumerate([self.ax1, self.ax2]):
            # For infomation, print which axes the click was in
            if ax == event.inaxes:
                subplot = i+1
                break

        if subplot == 1:
            self.current.annotations['pdOnset'] = event.pickx
        else:
            self.current.annotations['splineOnset'] = event.pickx

        self.update()


class l1_MPBPD_Annotator(CurveAnnotator):
    """ 
    l1_MPBPD_Annotator is a GUI class for annotating l1 PD and MPBPD curves.

    The annotator works with PD and MPBPD curves and allows 
    selection of single points (labelled as [metric]Onset in the saved file)
    -- one per curve. The GUI also displays the waveform, and if TextGrids
    are provided, the acoustic segment boundaries.
    """

    def __init__(self, recordings, args, xlim=(-0.1, 1.0),
                 figsize=(15, 8),
                 categories=['Stable', 'Hesitation', 'Chaos', 'No data',
                             'Not set']):
        """ 
        Constructor for the PD_MPBPD_Annotator GUI. 

        Also sets up internal state and adds keys [l1Category, splineCategory, 
        l1Onset, splineOnset] to the data argument. For the categories -1 is used
        to mark 'not set', and for the onsets -1.0.
        """
        super().__init__(recordings, args, xlim, figsize)

        self.categories = categories

        for token in self.recordings:
            token['l1Category'] = -1
            token['splineCategory'] = -1
            token['l1Onset'] = -1.0
            token['splineOnset'] = -1.0

        #
        # Subplot grid shape
        #
        sbuplot_grid = (7, 7)

        #
        # Graphs to be annotated and the waveform for reference.
        #
        self.ax1 = plt.subplot2grid(sbuplot_grid, (0, 0), rowspan=3, colspan=6)
        self.ax2 = plt.subplot2grid(sbuplot_grid, (3, 0), rowspan=3, colspan=6)
        self.ax3 = plt.subplot2grid(sbuplot_grid, (6, 0), colspan=6)

        self.draw_plots()

        self.fig.align_ylabels()
        self.fig.canvas.mpl_connect('pick_event', self.onpick)

        #
        # Buttons and such.
        #
        self.ax4 = plt.subplot2grid(sbuplot_grid, (0, 6), rowspan=2)
        self.ax4.axes.set_axis_off()
        self.pdCategoryRB = RadioButtons(
            self.ax4, self.categories,
            active=self.current.annotations['l1Category'])
        self.pdCategoryRB.on_clicked(self.pdCatCB)

        self.ax5 = plt.subplot2grid(sbuplot_grid, (3, 6), rowspan=2)
        self.ax5.axes.set_axis_off()
        self.splineCategoryRB = RadioButtons(
            self.ax5, self.categories,
            active=self.current.annotations['splineCategory'])
        self.splineCategoryRB.on_clicked(self.splineCatCB)

        self.axnext = plt.axes([0.85, 0.225, 0.1, 0.055])
        self.bnext = Button(self.axnext, 'Next')
        self.bnext.on_clicked(self.next)

        self.axprev = plt.axes([0.85, 0.15, 0.1, 0.055])
        self.bprev = Button(self.axprev, 'Previous')
        self.bprev.on_clicked(self.prev)

        self.axsave = plt.axes([0.85, 0.05, 0.1, 0.055])
        self.bsave = Button(self.axsave, 'Save')
        self.bsave.on_clicked(self.save)

        plt.show()

    def draw_plots(self):
        """ 
        Updates title and graphs. Called by self.update().
        """
        self.ax1.set_title(self._get_title())
        self.ax1.axes.xaxis.set_ticklabels([])
        self.ax2.axes.xaxis.set_ticklabels([])

        audio = self.current.modalities['AAA_audio']
        stimulus_onset = audio.meta['stimulus_onset']
        wav = audio.data
        wav_time = (audio.timevector - stimulus_onset)

        pd = self.current.modalities['ultrasound PD']
        ultra_time = pd.timevector - stimulus_onset

        annd = self.current.modalities['annd']
        annd_time = annd.timevector - stimulus_onset

        textgrid = self.current.textgrid

        plot_pd(
            self.ax1, pd.data['l1'],
            ultra_time, self.xlim, textgrid, stimulus_onset,
            picker=CurveAnnotator.line_xdirection_picker)
        plot_mpbpd(
            self.ax2, annd.data, annd_time, self.xlim, textgrid,
            stimulus_onset, picker=CurveAnnotator.line_xdirection_picker,
            plot_raw=True)
        plot_wav(self.ax3, wav, wav_time, self.xlim, textgrid, stimulus_onset)

        if self.current.annotations['l1Onset'] > -1:
            self.ax1.axvline(x=self.current.annotations['l1Onset'],
                             linestyle=':', color="deepskyblue", lw=1)
            self.ax2.axvline(x=self.current.annotations['l1Onset'],
                             linestyle=':', color="deepskyblue", lw=1)
            self.ax3.axvline(x=self.current.annotations['l1Onset'],
                             linestyle=':', color="deepskyblue", lw=1)
        if self.current.annotations['splineOnset'] > -1:
            self.ax1.axvline(x=self.current.annotations['splineOnset'],
                             linestyle='-.', color="seagreen", lw=1)
            self.ax2.axvline(x=self.current.annotations['splineOnset'],
                             linestyle='-.', color="seagreen", lw=1)
            self.ax3.axvline(x=self.current.annotations['splineOnset'],
                             linestyle='-.', color="seagreen", lw=1)

    def clear_axis(self):
        self.ax1.cla()
        self.ax2.cla()
        self.ax3.cla()

    def updateUI(self):
        """ 
        Updates parts of the UI outwith the graphs.
        """
        self.pdCategoryRB.set_active(self.current.annotations['l1Category'])
        self.splineCategoryRB.set_active(
            self.current.annotations['splineCategory'])

    def save(self, event):
        """ 
        Callback funtion for the Save button.
        Currently overwrites what ever is at 
        local_data/onsets.csv
        """
        # eventually get this from commandline/caller/dialog window
        filename = 'local_data/l1_MPBPD_onsets.csv'
        fieldnames = ['l1Category', 'splineCategory', 'l1Onset', 'splineOnset']
        csv.register_dialect('tabseparated', delimiter='\t',
                             quoting=csv.QUOTE_NONE)

        with closing(open(filename, 'w')) as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames, extrasaction='ignore',
                                    dialect='tabseparated')

            writer.writeheader()
            for token in self.recordings:
                writer.writerow(token)
            print('Wrote onset data in file ' + filename + '.')
            _annotator_logger.debug(
                'Wrote onset data in file ' + filename + '.')

    def pdCatCB(self, event):
        """ 
        Callback funtion for the RadioButton for catogorising 
        the PD curve.
        """
        self.current.annotations['l1Category'] = self.categories.index(
            event)

    def splineCatCB(self, event):
        """ 
        Callback funtion for the RadioButton for catogorising 
        the curve of the spline metric.
        """
        self.current.annotations['splineCategory'] = self.categories.index(
            event)

    def onpick(self, event):
        """
        Callback for handling time selection on events.
        """
        subplot = 0
        for i, ax in enumerate([self.ax1, self.ax2]):
            # For infomation, print which axes the click was in
            if ax == event.inaxes:
                subplot = i+1
                break

        if subplot == 1:
            self.current.annotations['l1Onset'] = event.pickx
        else:
            self.current.annotations['splineOnset'] = event.pickx

        self.update()
