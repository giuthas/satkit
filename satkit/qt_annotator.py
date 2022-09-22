#
# Copyright (c) 2019-2022 Pertti Palo, Scott Moisik, Matthew Faytak, and Motoki Saito.
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
from copy import deepcopy
import csv
import logging

# Numpy
import numpy as np

# GUI functionality
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtGui import QIntValidator
from PyQt5.uic import loadUiType

# Plotting functions and hooks for GUI
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)

# Local modules
#from satkit.annotator import CurveAnnotator, PD_Annotator
from satkit.pd_annd_plot import plot_pd, plot_pd_3d, plot_wav, plot_wav_3D_ultra, plot_pd_norms_intensity
import satkit.io as satkit_io

# Load the GUI layout generated with QtDesigner.
Ui_MainWindow, QMainWindow = loadUiType('satkit/qt_annotator.ui')

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
        text += ', token: ' + str(self.index+1) + '/' + str(self.max_index)
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
        self.toolbar = NavigationToolbar(self.canvas,
                                         self, coordinates=True)
        self.addToolBar(self.toolbar)

        self.ultra_canvas = FigureCanvas(self.ultra_fig)
        self.verticalLayout_6.addWidget(self.ultra_canvas)
        self.ultra_canvas.draw()

    def remove_mpl_elements(self):
        """Remove matplotlib elements."""
        self.mplWindowVerticalLayout.removeWidget(self.canvas)
        self.canvas.close()

        self.mplWindowVerticalLayout.removeWidget(self.toolbar)
        self.toolbar.close()

        self.verticalLayout_6.removeWidget(self.ultra_canvas)
        self.ultra_canvas.close()

    def draw_plots(self):
        """
        Updates title and graphs. Called by self.update().
        """
        self.ax1.set_title(self._get_title())
        self.ax1.axes.xaxis.set_ticklabels([])

        audio = self.current.modalities['MonoAudio']
        stimulus_onset = audio.meta['stimulus_onset']
        wav = audio.data
        wav_time = (audio.timevector - stimulus_onset)

        pd = self.current.modalities['PD on RawUltrasound']
        ultra_time = pd.timevector - stimulus_onset

        #self.xlim = [ultra_time[0] - 0.05, ultra_time[-1]+0.05]
        self.xlim = [-0.25, 1.0]

        textgrid = self.current.textgrid

        plot_pd(
            self.ax1, pd.data['pd'],
            ultra_time, self.xlim, textgrid, stimulus_onset,
            picker=PdQtAnnotator.line_xdirection_picker)
        plot_wav(self.ax3, wav, wav_time, self.xlim,
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


class Annotator():
    """
    Annotator controls QtAnnotatorWindow and the data.

    In the Model-view-presenter pattern this class is the Presenter,
    QtAnnotatorWindow is the View and a Recordings array is the Model.
    """

    def __init__(self, recordings, args, xlim=(-0.1, 1.0),
                 categories=None, pickle_filename=None):

        self.view_window = QtAnnotatorWindow(self)

        self.index = 0
        self.max_index = len(recordings)

        self.recordings = recordings
        self.commandlineargs = args
        self.display_tongue = args.displayTongue

        self.xlim = xlim

        if categories is None:
            self.categories = PdQtAnnotator.default_categories
        else:
            self.categories = categories
        self.tongue_positions = PdQtAnnotator.default_tongue_positions
        self._add_annotations()

        self.pickle_filename = pickle_filename

        self.has_been_saved = False

    @property
    def current(self):
        """Current recording."""
        return self.recordings[self.index]

    @property
    def default_annotations(self):
        """Default annotations with default values."""
        return {
            'pdCategory': self.categories[-1],
            'tonguePosition': self.tongue_positions[-1],
            'pdOnset': -1.0,
            'pdOnsetIndex': -1,
        }

    def _add_annotations(self):
        """Add annotation dicts to this annotator's recordings."""
        for recording in self.recordings:
            if recording.annotations:
                recording.annotations = dict(
                    list(self.default_annotations.items()) +
                    list(recording.annotations.items()))
            else:
                recording.annotations = deepcopy(self.default_annotations)

    def next_cb(self):
        """
        Callback function for the Next button.
        Increases cursor index, updates the view.
        """
        if self.index < self.max_index-1:
            # TODO: wrap in a data modalities accessor
            self.current.modalities['RawUltrasound'].data = None
            self.index += 1
            self.view_window.update_figures()
            self.view_window.update_ui()

    def prev_cb(self):
        """
        Callback function for the Previous button.
        Decreases cursor index, updates the view.
        """
        if self.index > 0:
            # TODO: wrap in a data modalities accessor
            self.current.modalities['RawUltrasound'].data = None
            self.index -= 1
            self.view_window.update_figures()
            self.view_window.update_ui()

    def go_cb(self):
        """
        Go to a recording.
        """
        self.current.modalities['RawUltrasound'].data = None
        self.index = int(self.view_window.goLineEdit.text())-1
        self.view_window.update_figures()
        self.view_window.update_ui()

    def quit_cb(self):
        """
        Quit the app.
        """
        # TODO: make sure the data has been saved before quitting.
        if not self.has_been_saved:
            self.save_cb()
        QCoreApplication.quit()

    def save_cb(self):
        """
        Save the recordings.
        """
        if not self.pickle_filename:
            (self.pickle_filename, _) = QFileDialog.getSaveFileName(
                self, 'Save file', directory='.', filter="Pickle files (*.pickle)")
        if self.pickle_filename:
            satkit_io.save2pickle(
                self.recordings,
                self.pickle_filename)
            _qt_annotator_logger.info(
                "Wrote data to file {file}.", file = self.pickle_filename)
        self.has_been_saved = True

    def export_cb(self):
        """
        Export annotations and some other meta data to a utf-8 .csv file.
        """
        (filename, _) = QFileDialog.getSaveFileName(
            self, 'Save file', directory='.', filter="CSV files (*.csv)")

        if not filename:
            return

        vowels = ['a', 'A', 'e', 'E', 'i', 'I',
                  'o', 'O', 'u', '@', "@`", 'OI', 'V']
        fieldnames = ['basename', 'date_and_time', 'prompt', 'C1', 'C1_dur',
                      'word_dur', 'first_sound',
                      'first_sound_type', 'first_sound_dur', 'AAI']
        fieldnames.extend(self.default_annotations.keys())
        csv.register_dialect('tabseparated', delimiter='\t',
                             quoting=csv.QUOTE_NONE)

        with closing(open(filename, 'w', encoding='utf-8')) as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames, extrasaction='ignore',
                                    dialect='tabseparated')

            writer.writeheader()
            for recording in self.recordings:
                annotations = recording.annotations.copy()
                annotations['basename'] = recording.meta['basename']
                annotations['date_and_time'] = recording.meta['date_and_time']
                annotations['prompt'] = recording.meta['prompt']
                annotations['word'] = recording.meta['prompt'].split()[1]

                word_dur = -1.0
                acoustic_onset = -1.0
                if 'word' in recording.textgrid:
                    for interval in recording.textgrid['word']:
                        # change this to access the phonemeDict and check for included words,
                        # then search for phonemes based on the same
                        if interval.text == "":
                            continue

                        # Before 1.0: check if there is a duration to use here. and maybe make this
                        # more intelligent by selecting purposefully the last non-empty first and
                        # taking the duration?
                        word_dur = interval.dur
                        stimulus_onset = recording.modalities['MonoAudio'].meta['stimulus_onset']
                        acoustic_onset = interval.xmin - stimulus_onset
                        break
                    annotations['word_dur'] = word_dur
                else:
                    annotations['word_dur'] = -1.0

                if acoustic_onset < 0 or annotations['pdOnset'] < 0:
                    aai = -1.0
                else:
                    aai = acoustic_onset - annotations['pdOnset']
                annotations['AAI'] = aai

                first_sound_dur = -1.0
                first_sound = ""
                if 'segment' in recording.textgrid:
                    for interval in recording.textgrid['segment']:
                        if interval.text and interval.text != 'beep':
                            first_sound_dur = interval.dur
                            first_sound = interval.text
                            break
                annotations['first_sound_dur'] = first_sound_dur
                annotations['first_sound'] = first_sound
                if first_sound in vowels:
                    annotations['first_sound_type'] = 'V'
                else:
                    annotations['first_sound_type'] = 'C'

                annotations['C1'] = recording.meta['prompt'][0]
                writer.writerow(annotations)
            _qt_annotator_logger.info(
                'Wrote onset data in file {file}.', file = filename)

    def pd_category_cb(self):
        """
        Callback funtion for the RadioButton for catogorising
        the PD curve.
        """
        radio_button = self.view_window.sender()
        if radio_button.isChecked():
            self.current.annotations['pdCategory'] = radio_button.text()
            self.has_been_saved = False

    def tongue_position_cb(self):
        """
        Callback funtion for the RadioButton for catogorising
        the PD curve.
        """
        radio_button = self.view_window.sender()
        if radio_button.isChecked():
            self.current.annotations['tonguePosition'] = radio_button.text()
            self.has_been_saved = False


    def onpick_cb(self, event):
        """
        Callback for handling time selection on events.
        """
        subplot = 0
        for i, axis in enumerate([self.view_window.ax1]):
            # For infomation, print which axes the click was in
            if axis == event.inaxes:
                subplot = i+1
                break

        if subplot == 1:
            self.current.annotations['pdOnset'] = event.pickx

            audio = self.current.modalities['MonoAudio']
            stimulus_onset = audio.meta['stimulus_onset']

            pd = self.current.modalities['PD on RawUltrasound']
            ultra_time = pd.timevector - stimulus_onset
            self.current.annotations['pdOnsetIndex'] = np.nonzero(
                ultra_time >= event.pickx)[0][0]
            self.has_been_saved = False
        self.view_window.update_figures()


class PdQtAnnotator(QMainWindow, Ui_MainWindow):
    """
    Qt_Annotator_Window is a GUI class for annotating PD curves.

    The annotator works with PD curves and allows
    selection of a single points (labelled as pdOnset in the saved file).
    The GUI also displays the waveform, and if TextGrids
    are provided, the acoustic segment boundaries.
    """

    default_categories = ['Stable', 'Hesitation', 'Chaos', 'No data',
                          'Not set']

    default_tongue_positions = ['High', 'Low', 'Other / Not visible']

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
        distances = np.abs(xdata - mouseevent.xdata)

        ind = np.argmin(distances)
        # if 1:
        pickx = np.take(xdata, ind)
        picky = np.take(ydata, ind)
        props = dict(ind=ind,
                     pickx=pickx,
                     picky=picky,
                     inaxes=mouseevent.inaxes)
        return True, props
        # else:
        #     return False, dict()

    def __init__(self, recordings, args, xlim=(-0.25, 1.5),
                 categories=None, pickle_filename=None):
        super().__init__()

        self.setupUi(self)

        self.index = 0
        self.max_index = len(recordings)

        self.recordings = recordings
        self.commandlineargs = args
        self.display_tongue = args.displayTongue

        if categories is None:
            self.categories = PdQtAnnotator.default_categories
        else:
            self.categories = categories
        self.tongue_positions = PdQtAnnotator.default_tongue_positions
        self._add_annotations()

        self.pickle_filename = pickle_filename

        self.fig_dict = {}

        self.fig = Figure()

        self.actionNext.triggered.connect(self.next)
        self.actionPrevious.triggered.connect(self.prev)

        self.actionNext_Frame.triggered.connect(self.next_frame)
        self.actionPrevious_Frame.triggered.connect(self.previous_frame)

        self.actionQuit.triggered.connect(self.quit)

        self.nextButton.clicked.connect(self.next)
        self.prevButton.clicked.connect(self.prev)
        self.saveButton.clicked.connect(self.save)
        self.exportButton.clicked.connect(self.export)

        go_validator = QIntValidator(1, self.max_index + 1, self)
        self.goLineEdit.setValidator(go_validator)
        self.goButton.clicked.connect(self.go_to_recording)

        self.categoryRB_1.toggled.connect(self.pd_category_cb)
        self.categoryRB_2.toggled.connect(self.pd_category_cb)
        self.categoryRB_3.toggled.connect(self.pd_category_cb)
        self.categoryRB_4.toggled.connect(self.pd_category_cb)
        self.categoryRB_5.toggled.connect(self.pd_category_cb)

        self.positionRB_1.toggled.connect(self.tongue_position_cb)
        self.positionRB_2.toggled.connect(self.tongue_position_cb)
        self.positionRB_3.toggled.connect(self.tongue_position_cb)

        self.xlim = xlim
        max_pds = np.zeros(len(self.recordings))
        for i, recording in enumerate(self.recordings):
            if 'PD on RawUltrasound' in recording.modalities:
                max_pds[i] = np.max(recording.modalities['PD on RawUltrasound'].data['pd'])
        self.ylim = (-50, np.max(max_pds)+50)

        #
        # Graphs to be annotated and the waveform for reference.
        #
        # gs = self.fig.add_gridspec(4, 7)
        # self.ax1 = self.fig.add_subplot(gs[0:0+3, 0:0+7])
        # self.ax3 = self.fig.add_subplot(gs[3:3+1, 0:0+7])
        grid_specification = self.fig.add_gridspec(5)
        self.ax1 = self.fig.add_subplot(grid_specification[0:0+4])
        self.ax3 = self.fig.add_subplot(grid_specification[4:4+1])

        self.ultra_fig = Figure()
        self.ultra_axes = self.ultra_fig.add_axes([0, 0, 1, 1])

        self.draw_plots()

        self.fig.align_ylabels()
        self.fig.canvas.mpl_connect('pick_event', self.onpick)

        self.add_mpl_elements()

        self.show()

    @property
    def current(self):
        """Current recording index."""
        return self.recordings[self.index]

    @property
    def default_annotations(self):
        """List default annotations and their default values as a dict."""
        return {
            'pdCategory': self.categories[-1],
            'tonguePosition': self.tongue_positions[-1],
            'pdOnset': -1.0,
            'pdOnsetIndex': -1,
        }

    def _add_annotations(self):
        """Plot the annotations."""
        for recording in self.recordings:
            if recording.annotations:
                recording.annotations = dict(
                    list(self.default_annotations.items()) +
                    list(recording.annotations.items()))
            else:
                recording.annotations = deepcopy(self.default_annotations)

    def _get_title(self):
        """
        Private helper function for generating the title.
        """
        text = 'SATKIT Annotator'
        text += ', prompt: ' + self.current.meta['prompt']
        text += ', token: ' + str(self.index+1) + '/' + str(self.max_index)
        return text

    def clear_axis(self):
        """Clear all plotting axis of this annotator."""
        self.ax1.cla()
        self.ax3.cla()

    def update(self):
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
        if self.categoryRB_1.text() == self.current.annotations['pdCategory']:
            self.categoryRB_1.setChecked(True)
        if self.categoryRB_2.text() == self.current.annotations['pdCategory']:
            self.categoryRB_2.setChecked(True)
        if self.categoryRB_3.text() == self.current.annotations['pdCategory']:
            self.categoryRB_3.setChecked(True)
        if self.categoryRB_4.text() == self.current.annotations['pdCategory']:
            self.categoryRB_4.setChecked(True)
        if self.categoryRB_5.text() == self.current.annotations['pdCategory']:
            self.categoryRB_5.setChecked(True)

        if self.positionRB_1.text() == self.current.annotations['tonguePosition']:
            self.positionRB_1.setChecked(True)
        if self.positionRB_2.text() == self.current.annotations['tonguePosition']:
            self.positionRB_2.setChecked(True)
        if self.positionRB_3.text() == self.current.annotations['tonguePosition']:
            self.positionRB_3.setChecked(True)

        self.goLineEdit.setText(str(self.index + 1))

    def add_mpl_elements(self):
        """Add matplotlib elements - used also in updating."""
        self.canvas = FigureCanvas(self.fig)
        self.mplWindowVerticalLayout.addWidget(self.canvas)
        self.canvas.draw()
        self.toolbar = NavigationToolbar(self.canvas,
                                         self, coordinates=True)
        self.addToolBar(self.toolbar)

        self.ultra_canvas = FigureCanvas(self.ultra_fig)
        self.verticalLayout_6.addWidget(self.ultra_canvas)
        self.ultra_canvas.draw()

    def remove_mpl_elements(self):
        """Remove matplotlib elements before update."""
        self.mplWindowVerticalLayout.removeWidget(self.canvas)
        self.canvas.close()

        self.mplWindowVerticalLayout.removeWidget(self.toolbar)
        self.toolbar.close()

        self.verticalLayout_6.removeWidget(self.ultra_canvas)
        self.ultra_canvas.close()

    def draw_plots(self):
        """
        Updates title and graphs. Called by self.update().
        """
        self.ax1.set_title(self._get_title())
        self.ax1.axes.xaxis.set_ticklabels([])

        audio = self.current.modalities['MonoAudio']
        stimulus_onset = audio.meta['stimulus_onset']
        wav = audio.data
        wav_time = (audio.timevector - stimulus_onset)

        pd_metrics = self.current.modalities['PD on RawUltrasound']
        ultra_time = pd_metrics.timevector - stimulus_onset

        #self.xlim = [ultra_time[0] - 0.05, ultra_time[-1]+0.05]

        textgrid = self.current.textgrid

        # plot_pd_norms_intensity(self.ax1, pd_metrics, ultra_time, self.xlim, 
        #     textgrid=textgrid, time_offset=stimulus_onset, 
        #     picker=PdQtAnnotator.line_xdirection_picker)
        plot_pd(
            self.ax1, pd_metrics.data['pd'],
            ultra_time, self.xlim, self.ylim, textgrid, stimulus_onset,
            picker=PdQtAnnotator.line_xdirection_picker)
        plot_wav(self.ax3, wav, wav_time, self.xlim,
                 textgrid, stimulus_onset, 
                 picker=PdQtAnnotator.line_xdirection_picker)

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

    def next(self):
        """
        Callback function for the Next button.
        Increases cursor index, updates the view.
        """
        if self.index < self.max_index-1:
            # TODO: wrap in a data modalities accessor
            self.current.modalities['RawUltrasound'].data = None
            self.index += 1
            self.update()
            self.update_ui()

    def _update_pd_onset(self):
        audio = self.current.modalities['MonoAudio']
        stimulus_onset = audio.meta['stimulus_onset']

        pd_metrics = self.current.modalities['PD on RawUltrasound']
        ultra_time = pd_metrics.timevector - stimulus_onset
        self.current.annotations['pdOnset'] = ultra_time[self.current.annotations['pdOnsetIndex']]

    def next_frame(self):
        """
        Move the data cursor to the next frame.
        """
        if (self.current.annotations['pdOnsetIndex'] > -1 and 
            self.current.annotations['pdOnsetIndex'] < self.current.modalities['RawUltrasound'].data.size-1):

            self.current.annotations['pdOnsetIndex'] += 1            
            self._update_pd_onset()
            self.update()
            self.update_ui()

    def previous_frame(self):
        """
        Move the data cursor to the previous frame.
        """
        if self.current.annotations['pdOnsetIndex'] > 0:
            self.current.annotations['pdOnsetIndex'] -= 1
            self._update_pd_onset()
            self.update()
            self.update_ui()

    def prev(self):
        """
        Callback function for the Previous button.
        Decreases cursor index, updates the view.
        """
        if self.index > 0:
            # TODO: wrap in a data modalities accessor
            self.current.modalities['RawUltrasound'].data = None
            self.index -= 1
            self.update()
            self.update_ui()

    def go_to_recording(self):
        """
        Go to a recording specified in the goLineEdit text input field.
        """
        self.current.modalities['RawUltrasound'].data = None
        self.index = int(self.goLineEdit.text())-1
        self.update()
        self.update_ui()

    def quit(self):
        """
        Quit the app.
        """
        QCoreApplication.quit()

    def save(self):
        """
        Save the recordings.
        """
        if not self.pickle_filename:
            (self.pickle_filename, _) = QFileDialog.getSaveFileName(
                self, 'Save file', directory='.', filter="Pickle files (*.pickle)")
        if self.pickle_filename:
            satkit_io.save2pickle(
                self.recordings,
                self.pickle_filename)
            _qt_annotator_logger.info(
                "Wrote data to file {file}.", file = self.pickle_filename)

    def export(self):
        """
        Export annotations and some other meta data.
        """
        (filename, _) = QFileDialog.getSaveFileName(
            self, 'Save file', directory='.', filter="CSV files (*.csv)")

        if not filename:
            return

        vowels = ['a', 'A', 'e', 'E', 'i', 'I',
                  'o', 'O', 'u', '@', "@`", 'OI', 'V']
        fieldnames = ['basename', 'date_and_time', 'prompt', 'C1', 'C1_dur',
                      'word_dur', 'first_sound',
                      'first_sound_type', 'first_sound_dur', 'AAI']
        fieldnames.extend(self.default_annotations.keys())
        csv.register_dialect('tabseparated', delimiter='\t',
                             quoting=csv.QUOTE_NONE)

        with closing(open(filename, 'w', encoding='utf-8')) as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames, extrasaction='ignore',
                                    dialect='tabseparated')

            writer.writeheader()
            for recording in self.recordings:
                annotations = recording.annotations.copy()
                annotations['basename'] = recording.meta['basename']
                annotations['date_and_time'] = recording.meta['date_and_time']
                annotations['prompt'] = recording.meta['prompt']
                annotations['word'] = recording.meta['prompt'].split()[0]

                word_dur = -1.0
                acoustic_onset = -1.0
                if 'word' in recording.textgrid:
                    for interval in recording.textgrid['word']:
                        # change this to access the phonemeDict and
                        # check for included words, then search for
                        # phonemes based on the same
                        if interval.text == "":
                            continue

                        # Before 1.0: check if there is a duration to use here. and maybe make this
                        # more intelligent by selecting purposefully the last non-empty first and
                        # taking the duration?
                        word_dur = interval.dur
                        stimulus_onset = recording.modalities['MonoAudio'].meta['stimulus_onset']
                        acoustic_onset = interval.xmin - stimulus_onset
                        break
                    annotations['word_dur'] = word_dur
                else:
                    annotations['word_dur'] = -1.0

                if acoustic_onset < 0 or annotations['pdOnset'] < 0:
                    aai = -1.0
                else:
                    aai = acoustic_onset - annotations['pdOnset']
                annotations['AAI'] = aai

                first_sound_dur = -1.0
                first_sound = ""
                if 'segment' in recording.textgrid:
                    for interval in recording.textgrid['segment']:
                        if interval.text and interval.text != 'beep':
                            first_sound_dur = interval.dur
                            first_sound = interval.text
                            break
                annotations['first_sound_dur'] = first_sound_dur
                annotations['first_sound'] = first_sound
                if first_sound in vowels:
                    annotations['first_sound_type'] = 'V'
                else:
                    annotations['first_sound_type'] = 'C'

                annotations['C1'] = recording.meta['prompt'][0]
                writer.writerow(annotations)
            _qt_annotator_logger.info(
                'Wrote onset data in file {file}.', file = filename)

    def pd_category_cb(self):
        """
        Callback funtion for the RadioButton for catogorising
        the PD curve.
        """
        radio_button = self.sender()
        if radio_button.isChecked():
            self.current.annotations['pdCategory'] = radio_button.text()

    def tongue_position_cb(self):
        """
        Callback funtion for the RadioButton for catogorising
        the PD curve.
        """
        radio_button = self.sender()
        if radio_button.isChecked():
            self.current.annotations['tonguePosition'] = radio_button.text()

    def onpick(self, event):
        """
        Callback for handling time selection on events.
        """
        # TODO: BY VERSION 1.0 The below commented out code is possibly useful if dealing with more
        # than one modality to annotate.
        # subplot = 0
        # for i, axis in enumerate([self.ax1]):
        #     if axis == event.inaxes:
        #         subplot = i+1
        #         break

        # if subplot == 1:
        self.current.annotations['pdOnset'] = event.pickx

        audio = self.current.modalities['MonoAudio']
        stimulus_onset = audio.meta['stimulus_onset']

        pd_metrics = self.current.modalities['PD on RawUltrasound']
        ultra_time = pd_metrics.timevector - stimulus_onset
        self.current.annotations['pdOnsetIndex'] = np.nonzero(
            ultra_time >= event.pickx)[0][0]
        self.update()


class Pd3dQtAnnotator(QMainWindow, Ui_MainWindow):
    """
    Qt_Annotator_Window is a GUI class for annotating PD curves.

    The annotator works with PD curves and allows
    selection of a single points (labelled as pdOnset in the saved file).
    The GUI also displays the waveform, and if TextGrids
    are provided, the acoustic segment boundaries.
    """

    default_categories = ['Stable', 'Hesitation', 'Chaos', 'No data',
                          'Not set']

    default_tongue_positions = ['High', 'Low', 'Other / Not visible']

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
        distances = np.abs(xdata - mouseevent.xdata)

        ind = np.argmin(distances)
        # if 1:
        pickx = np.take(xdata, ind)
        picky = np.take(ydata, ind)
        props = dict(ind=ind,
                     pickx=pickx,
                     picky=picky,
                     inaxes=mouseevent.inaxes)
        return True, props
        # else:
        #     return False, dict()

    def __init__(self, recordings, args, xlim=(-0.1, 1.0),
                 categories=None, pickle_filename=None):
        super().__init__()

        self.setupUi(self)

        self.index = 0
        self.max_index = len(recordings)

        self.recordings = recordings
        self.commandlineargs = args

        if categories is None:
            self.categories = Pd3dQtAnnotator.default_categories
        else:
            self.categories = categories
        self.tongue_positions = Pd3dQtAnnotator.default_tongue_positions
        self._add_annotations()

        self.pickle_filename = pickle_filename

        self.fig_dict = {}

        self.fig = Figure()
        self.keypress_id = self.fig.canvas.mpl_connect(
            'key_press_event', self.on_key)

        self.actionNext.triggered.connect(self.next)
        self.actionPrevious.triggered.connect(self.prev)

        self.actionNext_Frame.triggered.connect(self.next_frame)
        self.actionPrevious_Frame.triggered.connect(self.previous_frame)

        self.actionQuit.triggered.connect(self.quit)

        go_validator = QIntValidator(1, self.max_index + 1, self)
        self.goLineEdit.setValidator(go_validator)
        self.goButton.clicked.connect(self.go_to_recording)

        self.nextButton.clicked.connect(self.next)
        self.prevButton.clicked.connect(self.prev)
        self.saveButton.clicked.connect(self.save)
        self.exportButton.clicked.connect(self.export)

        self.categoryRB_1.toggled.connect(self.pd_category_cb)
        self.categoryRB_2.toggled.connect(self.pd_category_cb)
        self.categoryRB_3.toggled.connect(self.pd_category_cb)
        self.categoryRB_4.toggled.connect(self.pd_category_cb)
        self.categoryRB_5.toggled.connect(self.pd_category_cb)

        self.positionRB_1.toggled.connect(self.tongue_position_cb)
        self.positionRB_2.toggled.connect(self.tongue_position_cb)
        self.positionRB_3.toggled.connect(self.tongue_position_cb)

        self.xlim = xlim

        #
        # Graphs to be annotated and the waveform for reference.
        #
        # gs = self.fig.add_gridspec(4, 7)
        # self.ax1 = self.fig.add_subplot(gs[0:0+3, 0:0+7])
        # self.ax3 = self.fig.add_subplot(gs[3:3+1, 0:0+7])
        grid_specification = self.fig.add_gridspec(5)
        self.ax1 = self.fig.add_subplot(grid_specification[0:0+4])
        self.ax3 = self.fig.add_subplot(grid_specification[4:4+1])

        self.ultra_fig = Figure()
        self.ultra_axes = self.ultra_fig.add_axes([0, 0, 1, 1])

        self.draw_plots()

        self.fig.align_ylabels()
        self.fig.canvas.mpl_connect('pick_event', self.onpick)

        self.add_mpl_elements()

        self.show()

    @property
    def current(self):
        """Current recording index."""
        return self.recordings[self.index]

    @property
    def default_annotations(self):
        """List default annotations and their default values as a dict."""
        return {
            'pdCategory': self.categories[-1],
            'tonguePosition': self.tongue_positions[-1],
            'pdOnset': -1.0,
            'pdOnsetIndex': -1,
        }

    def _add_annotations(self):
        """Add expected annotations."""
        for recording in self.recordings:
            if recording.annotations:
                recording.annotations.update(self.default_annotations)
            else:
                recording.annotations = deepcopy(self.default_annotations)

    def _get_title(self):
        """
        Private helper function for generating the title.
        """
        text = 'SATKIT Annotator'
        text += ', prompt: ' + self.current.meta['prompt']
        text += ', token: ' + str(self.index+1) + '/' + str(self.max_index)
        return text

    def clear_axis(self):
        """Clear the curve axis."""
        self.ax1.cla()
        self.ax3.cla()

    def update(self):
        """
        Updates the graphs but not the buttons.
        """
        self.clear_axis()
        self.remove_mpl_elements()
        self.draw_plots()
        self.add_mpl_elements()
        self.fig.canvas.draw()
        self.draw_ultra_frame()

    def update_ui(self):
        """
        Updates parts of the UI outwith the graphs.
        """
        # self.pdCategoryRB.set_active(self.current.annotations['pdCategory'])
        if self.categoryRB_1.text() == self.current.annotations['pdCategory']:
            self.categoryRB_1.setChecked(True)
        if self.categoryRB_2.text() == self.current.annotations['pdCategory']:
            self.categoryRB_2.setChecked(True)
        if self.categoryRB_3.text() == self.current.annotations['pdCategory']:
            self.categoryRB_3.setChecked(True)
        if self.categoryRB_4.text() == self.current.annotations['pdCategory']:
            self.categoryRB_4.setChecked(True)
        if self.categoryRB_5.text() == self.current.annotations['pdCategory']:
            self.categoryRB_5.setChecked(True)

        if self.positionRB_1.text() == self.current.annotations['tonguePosition']:
            self.positionRB_1.setChecked(True)
        if self.positionRB_2.text() == self.current.annotations['tonguePosition']:
            self.positionRB_2.setChecked(True)
        if self.positionRB_3.text() == self.current.annotations['tonguePosition']:
            self.positionRB_3.setChecked(True)

    def add_mpl_elements(self):
        """Add matplotlib elements. Used also in updating the UI."""
        self.canvas = FigureCanvas(self.fig)
        self.mplWindowVerticalLayout.addWidget(self.canvas)
        self.canvas.draw()
        self.toolbar = NavigationToolbar(self.canvas,
                                         self, coordinates=True)
        self.addToolBar(self.toolbar)

        self.ultra_canvas = FigureCanvas(self.ultra_fig)
        self.verticalLayout_6.addWidget(self.ultra_canvas)
        self.ultra_canvas.draw()

    def remove_mpl_elements(self):
        """Remove matplotlib elements. Used in updating the UI."""
        self.mplWindowVerticalLayout.removeWidget(self.canvas)
        self.canvas.close()

        self.mplWindowVerticalLayout.removeWidget(self.toolbar)
        self.toolbar.close()

        self.verticalLayout_6.removeWidget(self.ultra_canvas)
        self.ultra_canvas.close()

    def draw_plots(self):
        """
        Updates title and graphs. Called by self.update().
        """
        self.ax1.set_title(self._get_title())
        self.ax1.axes.xaxis.set_ticklabels([])

        audio = self.current.modalities['MonoAudio']
        stimulus_onset = audio.meta['stimulus_onset']
        wav = audio.data
        wav_time = audio.timevector

        pd_metrics = self.current.modalities['PD on ThreeD_Ultrasound']
        ultra_time = pd_metrics.timevector - pd_metrics.timevector[-1] + wav_time[-1]

        self.xlim = [ultra_time[0] - 0.05, ultra_time[-1]+0.05]

        textgrid = self.current.textgrid

        plot_pd_3d(
            self.ax1, pd_metrics.data['pd'],
            ultra_time, self.xlim, textgrid, stimulus_onset,
            picker=Pd3dQtAnnotator.line_xdirection_picker)
        plot_wav_3D_ultra(self.ax3, wav, wav_time, self.xlim,
                          textgrid, stimulus_onset)

        if self.current.annotations['pdOnset'] > -1:
            self.ax1.axvline(x=self.current.annotations['pdOnset'],
                             linestyle=':', color="deepskyblue", lw=1)
            self.ax3.axvline(x=self.current.annotations['pdOnset'],
                             linestyle=':', color="deepskyblue", lw=1)
        self.draw_ultra_frame()

    def draw_ultra_frame(self):
        """
        Display the ultrasound frame at current index.

        Draws in the designated part of the UI.
        """
        if self.current.annotations['pdOnsetIndex']:
            ind = self.current.annotations['pdOnsetIndex']
            array = self.current.modalities['ThreeD_Ultrasound'].data[ind, :, :, 32]
        else:
            array = self.current.modalities['ThreeD_Ultrasound'].data[1, :, :, 32]
        array = np.transpose(array)
        array = np.flip(array, 0).copy()
        array = array.astype(np.int8)
        self.ultra_axes.imshow(array, interpolation='nearest', cmap='Greys')

    def next_frame(self):
        """
        Move the data cursor to the next frame.
        """
        if (self.current.annotations['pdOnsetIndex'] > -1 and 
            self.current.annotations['pdOnsetIndex'] < self.current.data.size[0]-1):
            self.current.annotations['pdOnsetIndex'] += 1
            self.update()
            self.update_ui()

    def previous_frame(self):
        """
        Move the data cursor to the previous frame.
        """
        if self.current.annotations['pdOnsetIndex'] > 0:
            self.current.annotations['pdOnsetIndex'] -= 1
            self.update()
            self.update_ui()

    def next(self):
        """
        Callback function for the Next button.
        Increases cursor index, updates the view.
        """
        if self.index < self.max_index-1:
            # TODO: wrap in a data modalities accessor
            self.current.modalities['ThreeD_Ultrasound'].data = None
            self.index += 1
            self.update()
            self.update_ui()

    def prev(self):
        """
        Callback function for the Previous button.
        Decreases cursor index, updates the view.
        """
        if self.index > 0:
            # TODO: wrap in a data modalities accessor
            self.current.modalities['ThreeD_Ultrasound'].data = None
            self.index -= 1
            self.update()
            self.update_ui()

    def go_to_recording(self):
        """
        Go to the Recording specified by the index in the goLineEdit field.
        """
        self.current.modalities['ThreeD_Ultrasound'].data = None
        self.index = int(self.goLineEdit.text())-1
        self.update()
        self.update_ui()

    def on_key(self, event):
        """
        Callback function for keypresses.

        Right and left arrows move to the next and previous token.
        Pressing 's' saves the annotations in a csv-file.
        Pressing 'q' seems to be captured by matplotlib and interpeted as quit.
        """
        if event.key == "up":
            self.next()
        elif event.key == "down":
            self.prev()
        elif event.key == "s":
            self.save()

    def quit(self):
        """Quit the application."""
        QCoreApplication.quit()

    def save(self):
        """
        Save the recordings.
        """
        if not self.pickle_filename:
            (self.pickle_filename, _) = QFileDialog.getSaveFileName(
                self, 'Save file', directory='.', filter="Pickle files (*.pickle)")
        if self.pickle_filename:
            satkit_io.save2pickle(
                self.recordings,
                self.pickle_filename)
            _qt_annotator_logger.info(
                "Wrote data to file {file}.", file = self.pickle_filename)

    def export(self):
        """
        Export annotations and some other meta data.
        """
        (filename, _) = QFileDialog.getSaveFileName(
            self, 'Save file', directory='.', filter="CSV files (*.csv)")

        if not filename:
            return

        vowels = ['a', 'A', 'e', 'E', 'i', 'I',
                  'o', 'O', 'u', '@', "@`", 'OI', 'V']
        fieldnames = ['basename', 'date_and_time', 'prompt', 'C1', 'C1_dur',
                      'word_dur', 'first_sound',
                      'first_sound_type', 'first_sound_dur', 'AAI']
        fieldnames.extend(self.default_annotations.keys())
        csv.register_dialect('tabseparated', delimiter='\t',
                             quoting=csv.QUOTE_NONE)

        with closing(open(filename, 'w', encoding='utf-8')) as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames, extrasaction='ignore',
                                    dialect='tabseparated')

            writer.writeheader()
            for recording in self.recordings:
                annotations = recording.annotations.copy()
                annotations['basename'] = recording.meta['basename']
                annotations['date_and_time'] = recording.meta['date_and_time']
                annotations['prompt'] = recording.meta['prompt']
                annotations['word'] = recording.meta['prompt']
                print(recording.meta['prompt'])

                word_dur = -1.0
                acoustic_onset = -1.0
                if 'word' in recording.textgrid:
                    for interval in recording.textgrid['word']:
                        # change this to access the phonemeDict and
                        # check for included words, then search for
                        # phonemes based on the same
                        if interval.text == "":
                            continue

                        # Before 1.0: check if there is a duration to use here. and maybe make this
                        # more intelligent by selecting purposefully the last non-empty first and
                        # taking the duration?
                        word_dur = interval.dur
                        acoustic_onset = interval.xmin
                        break
                    annotations['word_dur'] = word_dur
                else:
                    annotations['word_dur'] = -1.0

                if acoustic_onset < 0 or annotations['pdOnset'] < 0:
                    aai = -1.0
                else:
                    aai = acoustic_onset - annotations['pdOnset']
                annotations['AAI'] = aai

                first_sound_dur = -1.0
                first_sound = ""
                if 'phoneme' in recording.textgrid:
                    for interval in recording.textgrid['phoneme']:
                        if interval.text and interval.text != 'beep':
                            first_sound_dur = interval.dur
                            first_sound = interval.text
                            break
                annotations['first_sound_dur'] = first_sound_dur
                annotations['first_sound'] = first_sound
                if first_sound in vowels:
                    annotations['first_sound_type'] = 'V'
                else:
                    annotations['first_sound_type'] = 'C'

                annotations['C1'] = recording.meta['prompt'][0]
                writer.writerow(annotations)
            _qt_annotator_logger.info(
                'Wrote onset data in file {}.', file = filename)

    def pd_category_cb(self):
        """
        Callback funtion for the RadioButton for catogorising
        the PD curve.
        """
        radio_button = self.sender()
        if radio_button.isChecked():
            self.current.annotations['pdCategory'] = radio_button.text()

    def tongue_position_cb(self):
        """
        Callback funtion for the RadioButton for catogorising
        the PD curve.
        """
        radio_button = self.sender()
        if radio_button.isChecked():
            self.current.annotations['tonguePosition'] = radio_button.text()

    def onpick(self, event):
        """
        Callback for handling time selection on events.
        """
        subplot = 0
        for i, axes in enumerate([self.ax1]):
            # For infomation, print which axes the click was in
            if axes == event.inaxes:
                subplot = i+1
                break

        if subplot == 1:
            self.current.annotations['pdOnset'] = event.pickx

            audio = self.current.modalities['MonoAudio']
            wav_time = audio.timevector

            pd_metrics = self.current.modalities['PD on ThreeD_Ultrasound']
            ultra_time = pd_metrics.timevector - pd_metrics.timevector[-1] + wav_time[-1]
            self.current.annotations['pdOnsetIndex'] = np.nonzero(
                ultra_time >= event.pickx)[0][0]
        self.update()
