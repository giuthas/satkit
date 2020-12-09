
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


# todo
# get actual data plotted
# add buttons and such for
# - moving to the next one
# - excluding from consideration
# - categorising PD and MPBPD separately into ok, hesitation, chaos
# - toggle for displaying acoustic boundaries
# - toggles or similar for displaying different data modalities
# even later on: add annotation tiers, possibility of editing them and hook them to the textgrids 
class Annotator():

    def __init__(self):#, meta, data, args):
        self.index = 0
        self.max_index = 2#len(meta)

        #
        # the selections and categories need to be initialised as arrays
        # and/or stored directly in meta/data 
        #
        self.selection1 = -1
        self.selection2 = -1

        self.pdCatogory = 0
        self.splineCatogory = 0

        self.fig = plt.figure(figsize=(12, 6))

        #
        # Graphs to be annotated and the waveform for reference.
        #
        self.ax1 = plt.subplot2grid((7,7),(0,0), rowspan=3, colspan=6)
        self.ax1.set_title('SATKIT Annotator')
        self.ax1.axes.xaxis.set_ticklabels([])

        self.ax2 = plt.subplot2grid((7,7),(3,0), rowspan=3, colspan=6)
        self.ax2.axes.xaxis.set_ticklabels([])

        self.ax3 = plt.subplot2grid((7,7),(6,0), colspan=6)

        self.data = rand(10)
        self.data2 = rand(17)
        self.range1 = np.linspace(0.0,1.0,10)
        self.range2 = np.linspace(0.0,1.0,17)

        self.ax1.plot(self.range1, self.data, '-', picker=self.line_picker)
        self.ax2.plot(self.range2, self.data2, '-', color='g', picker=self.line_picker)

        self.fig.canvas.mpl_connect('pick_event', self.onpick)


        #
        # Buttons and such.
        #        
        categories = ['Stable', 'Hesitation', 'Chaos', 'No data']
        self.ax4 = plt.subplot2grid((7,7),(0,6), rowspan=2)
        self.ax4.axes.set_axis_off()
        self.pdCategoryRB = RadioButtons(self.ax4, categories)
        self.pdCategoryRB.on_clicked(self.pdCatCB)
        
        self.ax5 = plt.subplot2grid((7,7),(3,6), rowspan=2)
        self.ax5.axes.set_axis_off()
        self.splineCategoryRB = RadioButtons(self.ax5, categories)
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
        # this could also go into a pyqt5 window in its own file,
        # but for now saving to a prenamed file is enough

        plt.show()

        
    def next(self, event):
        if self.index < self.max_index:
            self.index += 1
            self.update()


    def prev(self, event):
        if self.index > 0:
            self.index -= 1
            self.update()


    def save(self, event):
        print('Saving is not yet implemented.')


    def splineCatCB(self, event):
        print(event)

        
    def pdCatCB(self, event):
        print(event)

        
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
        find the nearest point in the x-direction from the mouseclick in
        data coords and attach some extra attributes, pickx and picky
        which are the data points that were picked
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
                         inaxes=mouseevent.inaxes,
                         foobar="foobar")
            return True, props
        else:
            return False, dict()


    def onpick(self, event):
        subplot = 0
        for i, ax in enumerate([self.ax1, self.ax2]):
            # For infomation, print which axes the click was in
            if ax == event.inaxes:
                subplot = i+1
                break

        if subplot == 1:
            self.selection1 = event.pickx
        else:
            self.selection2 = event.pickx

        self.update()

            
    def update(self):
        self.ax1.cla()
        self.ax2.cla()
        self.ax1.plot(self.range1, self.data, '-', picker=self.line_picker)
        self.ax2.plot(self.range2, self.data2, '-', color='g', picker=self.line_picker)

        self.ax1.axvline(x = self.selection1, linestyle='--', color="b", lw=1)
        self.ax1.axvline(x = self.selection2, linestyle=':', color="g", lw=1)
        self.ax2.axvline(x = self.selection1, linestyle='--', color="b", lw=1)
        self.ax2.axvline(x = self.selection2, linestyle=':', color="g", lw=1)

        self.fig.canvas.draw()


    
if (__name__ == '__main__'):
    # t = time.time()

    # # Run the command line interface.
    # function_dict = {'pd':pd.pd, 'annd':annd.annd}
    # (meta, data, args) = cli("SATKIT GUI", function_dict, plot=False)

    # elapsed_time = time.time() - t
    # logging.info('Elapsed time ' + str(elapsed_time))

    # Get the GUI running.
    da = Annotator()#meta, data, args)

