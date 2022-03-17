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
from PyQt5.QtWidgets import QFileDialog, QLineEdit
from PyQt5.QtGui import QIntValidator
from PyQt5.uic import loadUiType

# Plotting functions and hooks for GUI
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)

# Local modules
#from satkit.annotator import CurveAnnotator, PD_Annotator
from satkit.pd_annd_plot import plot_pd, plot_pd_3d, plot_wav, plot_wav_3D_ultra
import satkit.io as satkit_io

# Load the GUI layout generated with QtDesigner.
Ui_MainWindow, QMainWindow = loadUiType('satkit/qt_annotator.ui')

_qt_annotator_logger = logging.getLogger('satkit.qt_annotator')


class PD_Qt_Annotator(QMainWindow, Ui_MainWindow):
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
        d = np.abs(xdata - mouseevent.xdata)

        ind = np.argmin(d)
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
        self.displayTongue = args.displayTongue

        if categories is None:
            self.categories = PD_Qt_Annotator.default_categories
        else:
            self.categories = categories
        self.tongue_positions = PD_Qt_Annotator.default_tongue_positions
        self._addAnnotations()

        self.pickle_filename = pickle_filename

        self.fig_dict = {}

        self.fig = Figure()

        self.actionNext.triggered.connect(self.next)
        self.actionPrevious.triggered.connect(self.prev)

        self.actionQuit.triggered.connect(self.quit)

        self.nextButton.clicked.connect(self.next)
        self.prevButton.clicked.connect(self.prev)
        self.saveButton.clicked.connect(self.save)
        self.exportButton.clicked.connect(self.export)

        goValidator = QIntValidator(1, self.max_index + 1, self)
        self.goLineEdit.setValidator(goValidator)
        self.goButton.clicked.connect(self.go)

        self.categoryRB_1.toggled.connect(self.pdCategoryCB)
        self.categoryRB_2.toggled.connect(self.pdCategoryCB)
        self.categoryRB_3.toggled.connect(self.pdCategoryCB)
        self.categoryRB_4.toggled.connect(self.pdCategoryCB)
        self.categoryRB_5.toggled.connect(self.pdCategoryCB)

        self.positionRB_1.toggled.connect(self.tonguePositionCB)
        self.positionRB_2.toggled.connect(self.tonguePositionCB)
        self.positionRB_3.toggled.connect(self.tonguePositionCB)

        self.xlim = xlim

        #
        # Graphs to be annotated and the waveform for reference.
        #
        # gs = self.fig.add_gridspec(4, 7)
        # self.ax1 = self.fig.add_subplot(gs[0:0+3, 0:0+7])
        # self.ax3 = self.fig.add_subplot(gs[3:3+1, 0:0+7])
        gs = self.fig.add_gridspec(5)
        self.ax1 = self.fig.add_subplot(gs[0:0+4])
        self.ax3 = self.fig.add_subplot(gs[4:4+1])

        self.ultra_fig = Figure()
        self.ultra_axes = self.ultra_fig.add_axes([0, 0, 1, 1])

        self.draw_plots()

        self.fig.align_ylabels()
        self.fig.canvas.mpl_connect('pick_event', self.onpick)

        self.add_mpl_elements()

        self.show()

    @property
    def current(self):
        return self.recordings[self.index]

    @property
    def default_annotations(self):
        return {
            'pdCategory': self.categories[-1],
            'tonguePosition': self.tongue_positions[-1],
            'pdOnset': -1.0,
            'pdOnsetIndex': -1,
        }

    def _addAnnotations(self):
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
        if self.displayTongue:
            self.draw_ultra_frame()

    def updateUI(self):
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
            picker=PD_Qt_Annotator.line_xdirection_picker)
        plot_wav(self.ax3, wav, wav_time, self.xlim,
                 textgrid, stimulus_onset)

        if self.current.annotations['pdOnset'] > -1:
            self.ax1.axvline(x=self.current.annotations['pdOnset'],
                             linestyle=':', color="deepskyblue", lw=1)
            self.ax3.axvline(x=self.current.annotations['pdOnset'],
                             linestyle=':', color="deepskyblue", lw=1)
        if self.displayTongue:
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
            # TODO: wrap in a data modalities accessor and possibly make these preloading at +/-1 step
            self.current.modalities['RawUltrasound'].data = None
            self.index += 1
            self.update()
            self.updateUI()

    def prev(self):
        """
        Callback function for the Previous button.
        Decreases cursor index, updates the view.
        """
        if self.index > 0:
            # TODO: wrap in a data modalities accessor and possibly make these preloading at +/-1 step
            self.current.modalities['RawUltrasound'].data = None
            self.index -= 1
            self.update()
            self.updateUI()

    def go(self):
        """
        Go to a recording.
        """
        self.current.modalities['RawUltrasound'].data = None
        self.index = int(self.goLineEdit.text())-1
        self.update()
        self.updateUI()

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
                "Wrote data to file %s.", self.pickle_filename)

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

        with closing(open(filename, 'w')) as csvfile:
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
                        # change this to access the phonemeDict and check for included words, then search for
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
                    AAI = -1.0
                else:
                    AAI = acoustic_onset - annotations['pdOnset']
                annotations['AAI'] = AAI

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
                'Wrote onset data in file %s.', filename)

    def pdCategoryCB(self):
        """
        Callback funtion for the RadioButton for catogorising
        the PD curve.
        """
        radioBtn = self.sender()
        if radioBtn.isChecked():
            self.current.annotations['pdCategory'] = radioBtn.text()

    def tonguePositionCB(self):
        """
        Callback funtion for the RadioButton for catogorising
        the PD curve.
        """
        radioBtn = self.sender()
        if radioBtn.isChecked():
            self.current.annotations['tonguePosition'] = radioBtn.text()

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

            audio = self.current.modalities['MonoAudio']
            stimulus_onset = audio.meta['stimulus_onset']

            pd = self.current.modalities['PD on RawUltrasound']
            ultra_time = pd.timevector - stimulus_onset
            self.current.annotations['pdOnsetIndex'] = np.nonzero(
                ultra_time >= event.pickx)[0][0]
        self.update()


class PD_3D_Qt_Annotator(QMainWindow, Ui_MainWindow):
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
        d = np.abs(xdata - mouseevent.xdata)

        ind = np.argmin(d)
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
            self.categories = PD_3D_Qt_Annotator.default_categories
        else:
            self.categories = categories
        self.tongue_positions = PD_3D_Qt_Annotator.default_tongue_positions
        self._addAnnotations()

        self.pickle_filename = pickle_filename

        self.fig_dict = {}

        self.fig = Figure()
        self.keypress_id = self.fig.canvas.mpl_connect(
            'key_press_event', self.on_key)

        self.actionNext.triggered.connect(self.next)
        self.actionPrevious.triggered.connect(self.prev)

        self.actionQuit.triggered.connect(self.quit)

        goValidator = QIntValidator(1, self.max_index + 1, self)
        self.goLineEdit.setValidator(goValidator)
        self.goButton.clicked.connect(self.go)

        self.nextButton.clicked.connect(self.next)
        self.prevButton.clicked.connect(self.prev)
        self.saveButton.clicked.connect(self.save)
        self.exportButton.clicked.connect(self.export)

        self.categoryRB_1.toggled.connect(self.pdCategoryCB)
        self.categoryRB_2.toggled.connect(self.pdCategoryCB)
        self.categoryRB_3.toggled.connect(self.pdCategoryCB)
        self.categoryRB_4.toggled.connect(self.pdCategoryCB)
        self.categoryRB_5.toggled.connect(self.pdCategoryCB)

        self.positionRB_1.toggled.connect(self.tonguePositionCB)
        self.positionRB_2.toggled.connect(self.tonguePositionCB)
        self.positionRB_3.toggled.connect(self.tonguePositionCB)

        self.xlim = xlim

        #
        # Graphs to be annotated and the waveform for reference.
        #
        # gs = self.fig.add_gridspec(4, 7)
        # self.ax1 = self.fig.add_subplot(gs[0:0+3, 0:0+7])
        # self.ax3 = self.fig.add_subplot(gs[3:3+1, 0:0+7])
        gs = self.fig.add_gridspec(5)
        self.ax1 = self.fig.add_subplot(gs[0:0+4])
        self.ax3 = self.fig.add_subplot(gs[4:4+1])

        self.ultra_fig = Figure()
        self.ultra_axes = self.ultra_fig.add_axes([0, 0, 1, 1])

        self.draw_plots()

        self.fig.align_ylabels()
        self.fig.canvas.mpl_connect('pick_event', self.onpick)

        self.add_mpl_elements()

        self.show()

    @property
    def current(self):
        return self.recordings[self.index]

    @property
    def default_annotations(self):
        return {
            'pdCategory': self.categories[-1],
            'tonguePosition': self.tongue_positions[-1],
            'pdOnset': -1.0,
            'pdOnsetIndex': -1,
        }

    def _addAnnotations(self):
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

    def updateUI(self):
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

        pd = self.current.modalities['PD on ThreeD_Ultrasound']
        ultra_time = pd.timevector - pd.timevector[-1] + wav_time[-1]

        self.xlim = [ultra_time[0] - 0.05, ultra_time[-1]+0.05]

        textgrid = self.current.textgrid

        plot_pd_3d(
            self.ax1, pd.data['pd'],
            ultra_time, self.xlim, textgrid, stimulus_onset,
            picker=PD_3D_Qt_Annotator.line_xdirection_picker)
        plot_wav_3D_ultra(self.ax3, wav, wav_time, self.xlim,
                          textgrid, stimulus_onset)

        if self.current.annotations['pdOnset'] > -1:
            self.ax1.axvline(x=self.current.annotations['pdOnset'],
                             linestyle=':', color="deepskyblue", lw=1)
            self.ax3.axvline(x=self.current.annotations['pdOnset'],
                             linestyle=':', color="deepskyblue", lw=1)
        self.draw_ultra_frame()

    def draw_ultra_frame(self):
        if self.current.annotations['pdOnsetIndex']:
            ind = self.current.annotations['pdOnsetIndex']
            array = self.current.modalities['ThreeD_Ultrasound'].data[ind, :, :, 32]
        else:
            array = self.current.modalities['ThreeD_Ultrasound'].data[1, :, :, 32]
        array = np.transpose(array)
        array = np.flip(array, 0).copy()
        array = array.astype(np.int8)
        self.ultra_axes.imshow(array, interpolation='nearest', cmap='Greys')

    def next(self):
        """
        Callback function for the Next button.
        Increases cursor index, updates the view.
        """
        if self.index < self.max_index-1:
            # TODO: wrap in a data modalities accessor and possibly make these preloading at +/-1 step
            self.current.modalities['ThreeD_Ultrasound'].data = None
            self.index += 1
            self.update()
            self.updateUI()

    def prev(self):
        """
        Callback function for the Previous button.
        Decreases cursor index, updates the view.
        """
        if self.index > 0:
            # TODO: wrap in a data modalities accessor and possibly make these preloading at +/-1 step
            self.current.modalities['ThreeD_Ultrasound'].data = None
            self.index -= 1
            self.update()
            self.updateUI()

    def go(self):
        """
        Go to a recording.
        """
        self.current.modalities['ThreeD_Ultrasound'].data = None
        self.index = int(self.goLineEdit.text())-1
        self.update()
        self.updateUI()

    def on_key(self, event):
        """
        Callback function for keypresses.

        Right and left arrows move to the next and previous token. 
        Pressing 's' saves the annotations in a csv-file.
        Pressing 'q' seems to be captured by matplotlib and interpeted as quit.
        """
        if event.key == "right":
            self.next()
        elif event.key == "left":
            self.prev()
        elif event.key == "s":
            self.save()

    def quit(self):
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
                "Wrote data to file %s.", self.pickle_filename)

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

        with closing(open(filename, 'w')) as csvfile:
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
                        # change this to access the phonemeDict and check for included words, then search for
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
                    AAI = -1.0
                else:
                    AAI = acoustic_onset - annotations['pdOnset']
                annotations['AAI'] = AAI

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
                'Wrote onset data in file %s.', filename)

    def pdCategoryCB(self):
        """
        Callback funtion for the RadioButton for catogorising
        the PD curve.
        """
        radioBtn = self.sender()
        if radioBtn.isChecked():
            self.current.annotations['pdCategory'] = radioBtn.text()

    def tonguePositionCB(self):
        """
        Callback funtion for the RadioButton for catogorising
        the PD curve.
        """
        radioBtn = self.sender()
        if radioBtn.isChecked():
            self.current.annotations['tonguePosition'] = radioBtn.text()

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

            audio = self.current.modalities['MonoAudio']
            wav_time = audio.timevector

            pd = self.current.modalities['PD on ThreeD_Ultrasound']
            ultra_time = pd.timevector - pd.timevector[-1] + wav_time[-1]
            self.current.annotations['pdOnsetIndex'] = np.nonzero(
                ultra_time >= event.pickx)[0][0]
        self.update()
