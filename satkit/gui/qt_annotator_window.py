#
# Copyright (c) 2019-2025
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

# Built in packages
import logging

# Numpy
import numpy as np
# Plotting functions and hooks for GUI
from matplotlib.backends.backend_qt5agg import \
    FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
# GUI functionality
from PyQt5.QtGui import QIntValidator
from PyQt5.uic import loadUiType
# Local modules
from satkit.plot_and_publish import plot_timeseries, plot_wav

# Load the GUI layout generated with QtDesigner.
Ui_MainWindow, QMainWindow = loadUiType('satkit/gui/qt_annotator.ui')

_qt_annotator_logger = logging.getLogger('satkit.qt_annotator')


class QtAnnotatorWindow(QMainWindow, Ui_MainWindow):
    """
    QtAnnotatorWindow provides the GUI basis for Annotator.

    In the Model-view-presenter pattern this class is the View, current
    Annotator is the Presenter and a Recordings array is the Model. See
    https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93presenter

    The idea is for QtAnnotatorWindow to only have minimal functionality. Adding
    display views, buttons and such is the job of Annotator. Annotator in turn
    may delegate these to other classes.

    Reason for not implementing much anything in QtAnnotatorWindow is two-fold:
    1. Inheriting a class that inherits QMainWindow and Ui_MainWindow does not
    seem to work. 2. We will try to keep inheritance trees fairly shallow to
    make them easier to manage and maintain.
    """

    @staticmethod
    def line_xdirection_picker(line, mouse_event):
        """
        Find the nearest point in the x (time) direction from the mouseclick in
        data coordinates. Return index of selected point, x and y coordinates of
        the data at that point, and inaxes to enable originating subplot to be
        identified.
        """
        if mouse_event.xdata is None:
            return False, dict()
        xdata = line.get_xdata()
        ydata = line.get_ydata()
        distances = np.abs(xdata - mouse_event.xdata)

        ind = np.argmin(distances)
        # if 1:
        pickx = np.take(xdata, ind)
        picky = np.take(ydata, ind)
        props = dict(ind=ind,
                     pickx=pickx,
                     picky=picky,
                     inaxes=mouse_event.inaxes)
        return True, props
        # else:
        #     return False, dict()

    def __init__(self, annotator):
        super().__init__()

        self.setupUi(self)

        self.annotator = annotator

        self.fig_dict = {}

        self.fig = Figure()

        self.actionNext.triggered.connect(annotator.next_cb)
        self.actionPrevious.triggered.connect(annotator.prev_cb)

        self.actionQuit.triggered.connect(annotator.quit_cb)

        self.nextButton.clicked.connect(annotator.next_cb)
        self.prevButton.clicked.connect(annotator.prev_cb)
        self.saveButton.clicked.connect(annotator.save_cb)
        self.exportButton.clicked.connect(annotator.export_cb)

        go_validator = QIntValidator(1, annotator.max_index + 1, self)
        self.goLineEdit.setValidator(go_validator)
        self.goButton.clicked.connect(annotator.go_cb)

        self.categoryRB_1.toggled.connect(annotator.pd_category_cb)
        self.categoryRB_2.toggled.connect(annotator.pd_category_cb)
        self.categoryRB_3.toggled.connect(annotator.pd_category_cb)
        self.categoryRB_4.toggled.connect(annotator.pd_category_cb)
        self.categoryRB_5.toggled.connect(annotator.pd_category_cb)

        self.positionRB_2.toggled.connect(annotator.tongue_position_cb)
        self.positionRB_3.toggled.connect(annotator.tongue_position_cb)
        self.positionRB_1.toggled.connect(annotator.tongue_position_cb)

        #
        # Graphs to be annotated and the waveform for reference.
        #
        # gs = self.fig.add_gridspec(4, 7)
        # self.ax1 = self.fig.add_subplot(gs[0:0+3, 0:0+7])
        # self.ax3 = self.fig.add_subplot(gs[3:3+1, 0:0+7])
        gridspec = self.fig.add_gridspec(5)
        self.ax1 = self.fig.add_subplot(gridspec[0:0+4])
        self.ax3 = self.fig.add_subplot(gridspec[4:4+1])

        self.ultra_fig = Figure()
        self.ultra_axes = self.ultra_fig.add_axes([0, 0, 1, 1])

        self.draw_plots()

        self.fig.align_ylabels()
        self.fig.canvas.mpl_connect('pick_event', self.onpick_cb)

        self.add_mpl_elements()

        self.show()

    def _get_title(self):
        """
        Private helper function for generating the title.
        """
        text = 'SATKIT Annotator'
        text += ', prompt: ' + self.current.meta['prompt']
        text += ', recording: ' + str(self.index+1) + '/' + str(self.max_index)
        return text

    def clear_axis(self):
        """Clear the axis."""
        self.ax1.cla()
        self.ax3.cla()

    def update_figures(self):
        """
        Updates the graphs but not the buttons.
        """
        self.clear_axis()
        self.remove_mpl_elements()
        self.draw_plots()
        self.add_mpl_elements()
        self.fig.canvas.draw()
        if self.display_tongue:
            self.draw_ultra_frame()

    def update_ui(self):
        """
        Updates parts of the UI outwith the graphs.
        """
        # self.pdCategoryRB.set_active(self.current.annotations['pdCategory'])
        if self.categoryRB_1.text() == self.annotator.current.annotations['pdCategory']:
            self.categoryRB_1.setChecked(True)
        if self.categoryRB_2.text() == self.annotator.current.annotations['pdCategory']:
            self.categoryRB_2.setChecked(True)
        if self.categoryRB_3.text() == self.annotator.current.annotations['pdCategory']:
            self.categoryRB_3.setChecked(True)
        if self.categoryRB_4.text() == self.annotator.current.annotations['pdCategory']:
            self.categoryRB_4.setChecked(True)
        if self.categoryRB_5.text() == self.annotator.current.annotations['pdCategory']:
            self.categoryRB_5.setChecked(True)

        if self.positionRB_1.text() == self.annotator.current.annotations['tonguePosition']:
            self.positionRB_1.setChecked(True)
        if self.positionRB_2.text() == self.annotator.current.annotations['tonguePosition']:
            self.positionRB_2.setChecked(True)
        if self.positionRB_3.text() == self.annotator.current.annotations['tonguePosition']:
            self.positionRB_3.setChecked(True)

        self.goLineEdit.setText(str(self.index + 1))

    def add_mpl_elements(self):
        """Add matplotlib elements."""
        self.canvas = FigureCanvas(self.fig)
        self.mplWindowVerticalLayout.addWidget(self.canvas)
        self.canvas.draw()
        # self.toolbar = NavigationToolbar(self.canvas,
        #                                  self, coordinates=True)
        # self.addToolBar(self.toolbar)

        self.ultra_canvas = FigureCanvas(self.ultra_fig)
        self.verticalLayout_6.addWidget(self.ultra_canvas)
        self.ultra_canvas.draw()

    def remove_mpl_elements(self):
        """Remove matplotlib elements."""
        self.mplWindowVerticalLayout.removeWidget(self.canvas)
        self.canvas.close()

        # self.mplWindowVerticalLayout.removeWidget(self.toolbar)
        # self.toolbar.close()

        self.verticalLayout_6.removeWidget(self.ultra_canvas)
        self.ultra_canvas.close()

    def draw_plots(self):
        """
        Updates title and graphs. Called by self.update().
        """
        self.ax1.set_title(self._get_title())
        # self.ax1.axes.xaxis.set_ticklabels([])

        audio = self.current.modalities['MonoAudio']
        stimulus_onset = audio.meta['stimulus_onset']
        wav = audio.data
        wav_time = (audio.timevector - stimulus_onset)

        pd = self.current.modalities['PD on RawUltrasound']
        ultra_time = pd.timevector - stimulus_onset

        # self.xlim = [ultra_time[0] - 0.05, ultra_time[-1]+0.05]
        self.xlim = [-0.25, 1.0]

        textgrid = self.current.textgrid

        # self.pd_boundaries = plot_pd(
        # self.ax1, pd.data['pd'],
        # ultra_time, self.xlim, textgrid, stimulus_onset,
        # picker=PdQtAnnotator.line_xdirection_picker)
        self.pd_boundaries = plot_timeseries(
            self.ax1, pd.data['pd'],
            ultra_time, self.xlim, textgrid, stimulus_onset)
        self.wav_boundaries = plot_wav(self.ax3, wav, wav_time, self.xlim,
                                       textgrid, stimulus_onset)

        if self.current.annotations['pdOnset'] > -1:
            self.ax1.axvline(x=self.current.annotations['pdOnset'],
                             linestyle=':', color="deepskyblue", lw=1)
            self.ax3.axvline(x=self.current.annotations['pdOnset'],
                             linestyle=':', color="deepskyblue", lw=1)
        if self.display_tongue:
            self.draw_ultra_frame()

    def draw_ultra_frame(self):
        """
        Display an already interpolated ultrasound frame.
        """
        index = 1
        if self.current.annotations['pdOnsetIndex']:
            index = self.current.annotations['pdOnsetIndex']
        image = self.current.modalities['RawUltrasound'].interpolated_image(
            index)
        self.ultra_axes.imshow(image, interpolation='nearest', cmap='gray')

    def draw_raw_ultra_frame(self):
        """
        Interpolate and display a raw ultrasound frame.
        """
        if self.current.annotations['pdOnsetIndex']:
            ind = self.current.annotations['pdOnsetIndex']
            array = self.current.modalities['RawUltrasound'].data[ind, :, :]
        else:
            array = self.current.modalities['RawUltrasound'].data[1, :, :]
        array = np.transpose(array)
        array = np.flip(array, 0).copy()
        array = array.astype(np.int8)
        self.ultra_axes.imshow(array, interpolation='nearest', cmap='gray')
