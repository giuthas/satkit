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
import csv
import logging
from pathlib import Path
import time

import matplotlib.pyplot as plt
from matplotlib.text import Text
from matplotlib.widgets import Button, RadioButtons, TextBox 

import numpy as np
from numpy.random import rand

# local modules
from satkit.commandLineInterface import cli 
from satkit import annd
from satkit import pd
from satkit.pd_annd_plot import plot_annd, plot_pd, plot_wav

_annotator_logger = logging.getLogger('satkit.annotator')    

# todo
# - write a version in PyQt to get nicer widgets.
# - toggle for displaying acoustic boundaries
# - toggles or similar for displaying different data modalities
# even later on:
# add annotation tiers,
# possibility of editing them and hook them to the textgrids 
class Annotator():

    def __init__(self, meta, data, args, xlim = (-0.1, 1.0),
                 categories = ['Stable', 'Hesitation', 'Chaos', 'No data']):
        """ 
        Constructor for the Annotator GUI. 

        Also sets up internal state and adds keys [pdCategory, splineCategory, 
        pdOnset, splineOnset] to the data argument. For the categories -1 is used
        to mark 'not set', and for the onsets -1.0.

        """                
        self.index = 0
        self.max_index = len(meta)

        self.meta = meta
        self.data = data
        self.commanlineargs = args

        self.xlim = xlim
        self.categories = categories
        
        for token in self.data:
            token['pdCategory'] = -1
            token['splineCategory'] = -1
            token['pdOnset'] = -1.0
            token['splineOnset'] = -1.0

        self.fig = plt.figure(figsize=(15, 8))

        #
        # Graphs to be annotated and the waveform for reference.
        #
        self.ax1 = plt.subplot2grid((7,7),(0,0), rowspan=3, colspan=6)
        self.ax2 = plt.subplot2grid((7,7),(3,0), rowspan=3, colspan=6)
        self.ax3 = plt.subplot2grid((7,7),(6,0), colspan=6)

        self.draw_plots()

        self.fig.align_ylabels()        
        self.fig.canvas.mpl_connect('pick_event', self.onpick)
        
        #
        # Buttons and such.
        #        
        self.ax4 = plt.subplot2grid((7,7),(0,6), rowspan=2)
        self.ax4.axes.set_axis_off()
        self.pdCategoryRB = RadioButtons(self.ax4, self.categories,
                                         active=self.data[self.index]['pdCategory'])
        self.pdCategoryRB.on_clicked(self.pdCatCB)
        
        self.ax5 = plt.subplot2grid((7,7),(3,6), rowspan=2)
        self.ax5.axes.set_axis_off()
        self.splineCategoryRB = RadioButtons(self.ax5, self.categories,
                                             active=self.data[self.index]['splineCategory'])
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

        pd = self.data[self.index]['pd']
        annd = self.data[self.index]['annd']
        ultra_time = pd['ultra_time'] - pd['beep_uti']
        annd_time = annd['annd_time'] - pd['beep_uti']
        wav_time = pd['ultra_wav_time'] - pd['beep_uti']
        textgrid = self.meta[self.index]['textgrid']
        
        plot_pd(self.ax1, pd, ultra_time, self.xlim, textgrid, -pd['beep_uti'],
                picker=self.line_picker)
        plot_annd(self.ax2, annd, annd_time, self.xlim, textgrid, -pd['beep_uti'],
                  picker=self.line_picker)
        plot_wav(self.ax3, pd, wav_time, self.xlim, textgrid, -pd['beep_uti'])

        if self.data[self.index]['pdOnset'] > -1:
            self.ax1.axvline(x = self.data[self.index]['pdOnset'],
                             linestyle='--', color="b", lw=1)
            self.ax2.axvline(x = self.data[self.index]['pdOnset'],
                             linestyle='--', color="b", lw=1)
            self.ax3.axvline(x = self.data[self.index]['pdOnset'],
                             linestyle='--', color="b", lw=1)
        if self.data[self.index]['splineOnset'] > -1:
            self.ax1.axvline(x = self.data[self.index]['splineOnset'],
                             linestyle=':', color="g", lw=1)
            self.ax2.axvline(x = self.data[self.index]['splineOnset'],
                             linestyle=':', color="g", lw=1)
            self.ax3.axvline(x = self.data[self.index]['splineOnset'],
                             linestyle=':', color="g", lw=1)


    def updateButtons(self):
        """ 
        Updates the RadioButtons.
        """        
        self.pdCategoryRB.set_active(self.data[self.index]['pdCategory'])
        self.splineCategoryRB.set_active(self.data[self.index]['splineCategory'])

        
    def update(self):
        """ 
        Updates the graphs but not the buttons.
        """
        self.ax1.cla()
        self.ax2.cla()
        self.ax3.cla()

        self.draw_plots()
        self.fig.canvas.draw()

    
    def _get_title(self):
        """ 
        Private helper function for generating the title.
        """
        text = 'SATKIT Annotator'
        text += ', prompt: ' + self.meta[self.index]['prompt']
        text += ', token: ' + str(self.index+1) + '/' + str(self.max_index)
        return text

        
    def next(self, event):
        """ 
        Callback funtion for the Next button.
        Increases cursor index, updates the view.
        """
        if self.index < self.max_index-1:
            self.index += 1
            self.update()
            self.updateButtons()

            
    def prev(self, event):
        """ 
        Callback funtion for the Previous button.
        Decreases cursor index, updates the view.
        """
        if self.index > 0:
            self.index -= 1
            self.update()
            self.updateButtons()


    def save(self, event):
        """ 
        Callback funtion for the Save button.
        Currently overwrites what ever is at 
        local_data/onsets.csv
        """
        # eventually get this from commandline/caller/dialog window
        filename = 'local_data/onsets.csv'
        fieldnames = ['pdCategory', 'splineCategory', 'pdOnset', 'splineOnset']
        csv.register_dialect('tabseparated', delimiter='\t', quoting=csv.QUOTE_NONE)

        with closing(open(filename, 'w')) as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames, extrasaction='ignore',
                                    dialect='tabseparated')

            writer.writeheader()
            for token in self.data:
                writer.writerow(token)
            print('Wrote onset data in file ' + filename + '.')
            _annotator_logger.debug('Wrote onset data in file ' + filename + '.')
        
        
    def pdCatCB(self, event):
        """ 
        Callback funtion for the RadioButton for catogorising 
        the PD curve.
        """
        self.data[self.index]['pdCategory'] = self.categories.index(event)
        
        
    def splineCatCB(self, event):
        """ 
        Callback funtion for the RadioButton for catogorising 
        the curve of the spline metric.
        """
        self.data[self.index]['splineCategory'] = self.categories.index(event)

        
    # picking with a custom hit test function
    # you can define custom pickers by setting picker to a callable
    # function.  The function has the signature
    #
    #  hit, props = func(artist, mouseevent)
    #
    # to determine the hit test.  if the mouse event is over the artist,
    # return hit=True and props is a dictionary of
    # properties you want added to the PickEvent attributes
    def line_picker(self, line, mouseevent):
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
            self.data[self.index]['pdOnset'] = event.pickx
        else:
            self.data[self.index]['splineOnset'] = event.pickx

        self.update()

            
