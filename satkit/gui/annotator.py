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

import csv
import logging
# Built in packages
from contextlib import closing
from copy import deepcopy

# Numpy
import numpy as np
# Local modules
import satkit.io as satkit_io
from matplotlib.backends.backend_qt5agg import \
    FigureCanvasQTAgg as FigureCanvas
# from matplotlib.backends.backend_qt5agg import \
#     NavigationToolbar2QT as NavigationToolbar
# Plotting functions and hooks for GUI
from matplotlib.figure import Figure
# GUI functionality
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QFileDialog
from PyQt5.uic import loadUiType
from satkit.configuration.configuration import config, data_run_params
from satkit.gui.qt_annotator_window import QtAnnotatorWindow
from satkit.plot import plot_timeseries, plot_wav
from satkit.plot.plot import plot_satgrid_tier

# Load the GUI layout generated with QtDesigner.
Ui_MainWindow, QMainWindow = loadUiType('satkit/gui/qt_annotator.ui')

_qt_annotator_logger = logging.getLogger('satkit.qt_annotator')


class Annotator():
    """
    Annotator controls QtAnnotatorWindow and the data.

    In the Model-view-presenter pattern this class is the Presenter,
    QtAnnotatorWindow is the View and a Recordings array is the Model.
    """

    default_categories = ['Stable', 'Hesitation', 'Chaos', 'No data',
                          'Not set']

    default_tongue_positions = ['High', 'Low', 'Other / Not visible']

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
            self.categories = Annotator.default_categories
        else:
            self.categories = categories
        self.tongue_positions = Annotator.default_tongue_positions
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
