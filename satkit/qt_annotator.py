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
import csv
import logging
from contextlib import closing
from copy import deepcopy

# Numpy
import numpy as np
from matplotlib.backends.backend_qt5agg import \
    FigureCanvasQTAgg as FigureCanvas
# from matplotlib.backends.backend_qt5agg import \
#     NavigationToolbar2QT as NavigationToolbar
# Plotting functions and hooks for GUI
from matplotlib.figure import Figure
# GUI functionality
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtGui import QIntValidator, QKeySequence
from PyQt5.QtWidgets import QFileDialog, QShortcut
from PyQt5.uic import loadUiType

# Local modules
import satkit.io as satkit_io
from satkit.configuration import config, data_run_params
from satkit.gui.boundary_animation import BoundaryAnimator
from satkit.plot import (plot_satgrid_tier, plot_spectrogram, plot_timeseries,
                         plot_wav)

# Load the GUI layout generated with QtDesigner.
Ui_MainWindow, QMainWindow = loadUiType('satkit/gui/qt_annotator.ui')

_qt_annotator_logger = logging.getLogger('satkit.qt_annotator')


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

        self.close_window = QShortcut(QKeySequence(self.tr("Ctrl+W", "File|Quit")),
                     self)
        self.close_window.activated.connect(self.quit)

        self.actionNext.triggered.connect(self.next)
        self.actionPrevious.triggered.connect(self.prev)

        self.actionNext_Frame.triggered.connect(self.next_frame)
        self.actionPrevious_Frame.triggered.connect(self.previous_frame)

        self.actionQuit.triggered.connect(self.quit)

        self.nextButton.clicked.connect(self.next)
        self.prevButton.clicked.connect(self.prev)
        self.saveButton.clicked.connect(self.save)
        self.exportButton.clicked.connect(self.save_textgrid)

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

        self.fig = Figure()
        self.data_axes = []
        self.tier_axes = []
 
        self.xlim = xlim
        max_pds = np.zeros(len(self.recordings))
        for i, recording in enumerate(self.recordings):
            if 'PD l2 on RawUltrasound' in recording.modalities:
                max_pds[i] = np.max(recording.modalities['PD l2 on RawUltrasound'].data)
        self.ylim = (-50, np.max(max_pds)+50)

        height_ratios = [config['data/tier height ratios']["data"], 
                        config['data/tier height ratios']["tier"]]
        self.main_grid_spec = self.fig.add_gridspec(
                                nrows=2,
                                ncols=1, 
                                hspace=0, 
                                wspace=0, 
                                height_ratios=height_ratios)

        nro_data_modalities = len(data_run_params['gui params']['data axes'])
        self.data_grid_spec = self.main_grid_spec[0].subgridspec(nro_data_modalities, 
                                                    1, hspace=0, wspace=0)
        self.data_axes.append(self.fig.add_subplot(self.data_grid_spec[0]))
        for i in range(1, nro_data_modalities):
            self.data_axes.append(self.fig.add_subplot(self.data_grid_spec[i],
                                                    sharex=self.data_axes[0]))


        self.ultra_fig = Figure()
        self.ultra_axes = self.ultra_fig.add_axes([0, 0, 1, 1])

        if not self.current.excluded:
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
        text = 'Recording: ' + str(self.index+1) + '/' + str(self.max_index)
        text += ', prompt: ' + self.current.meta_data.prompt
        return text

    def clear_axes(self):
        """Clear data axes of this annotator."""
        for axes in self.data_axes:
            axes.cla()

    def update(self):
        """
        Updates the graphs but not the buttons.
        """
        self.clear_axes()
        if self.current.excluded:
            pass
        else:
            self.draw_plots()
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

        self.ultra_canvas = FigureCanvas(self.ultra_fig)
        self.verticalLayout_6.addWidget(self.ultra_canvas)
        self.ultra_canvas.draw()

    def remove_mpl_elements(self):
        """Remove matplotlib elements before update."""
        self.mplWindowVerticalLayout.removeWidget(self.canvas)
        self.canvas.close()

        self.verticalLayout_6.removeWidget(self.ultra_canvas)
        self.ultra_canvas.close()

    def draw_plots(self):
        """
        Updates title and graphs. Called by self.update().
        """
        self.data_axes[0].set_title(self._get_title())

        for axes in self.tier_axes:
            axes.remove()
        self.tier_axes = []
        if self.current.satgrid:
            nro_tiers = len(self.current.satgrid)
            self.tier_grid_spec = self.main_grid_spec[1].subgridspec(nro_tiers, 1, hspace=0, wspace=0)
            for i, tier in enumerate(self.current.textgrid):
                axes = self.fig.add_subplot(self.tier_grid_spec[i],
                                                        sharex=self.data_axes[0])
                axes.set_yticks([])
                self.tier_axes.append(axes)

        audio = self.current.modalities['MonoAudio']
        stimulus_onset = audio.go_signal
        wav = audio.data
        wav_time = (audio.timevector - stimulus_onset)

        l2 = self.current.modalities['PD l2 on RawUltrasound']
        ultra_time = l2.timevector - stimulus_onset

        #self.xlim = [ultra_time[0] - 0.05, ultra_time[-1]+0.05]

         # self.pd_boundaries = plot_pd(
            # self.ax1, pd.data['pd'],
            # ultra_time, self.xlim, textgrid, stimulus_onset,
            # picker=PdQtAnnotator.line_xdirection_picker)
        # plot_wav(self.ax3, wav, wav_time, self.xlim,
        #          textgrid, stimulus_onset, 
        #          picker=PdQtAnnotator.line_xdirection_picker)
        plot_timeseries(self.data_axes[0], l2.data,
            ultra_time, self.xlim, self.ylim)
        plot_wav(self.data_axes[1], wav, wav_time, self.xlim)
        plot_spectrogram(self.data_axes[2], 
                        waveform=wav, 
                        sampling_frequency=audio.sampling_rate, 
                        xtent_on_x=[wav_time[0], wav_time[-1]])

        segment_line = None
        self.animators = []
        for (name, tier), axis in zip(self.current.satgrid.items(), self.tier_axes, strict=True):
            boundaries_by_axis = []
            boundary_set, segment_line = plot_satgrid_tier(axis, tier, 
                        time_offset=stimulus_onset, text_y=.5)
            boundaries_by_axis.append(boundary_set)
            axis.set_ylabel(name, rotation=0, 
                        horizontalalignment="right", verticalalignment="center")
            axis.set_xlim(self.xlim)
            if name in data_run_params["gui params"]["pervasive tiers"]:
                for axis in self.data_axes:
                    boundary_set = plot_satgrid_tier(axis, tier, 
                        time_offset=stimulus_onset, draw_text=False)[0]
                    boundaries_by_axis.append(boundary_set)

            # Change rows to be individual boundaries instead of axis. This
            # makes it possible to create animatores for each boundary as
            # represented by multiple lines on different axes.
            boundaries_by_boundary = list(map(list, zip(*boundaries_by_axis)))

            for boundaries, interval in zip(boundaries_by_boundary, tier, strict=True):
                animator = BoundaryAnimator(boundaries, interval, stimulus_onset) 
                animator.connect()
                self.animators.append(animator)
        if self.tier_axes:
            self.tier_axes[-1].set_xlabel("Time (s), go-signal at 0 s.")

        self.fig.tight_layout()

        if self.current.annotations['pdOnset'] > -1:
            self.data_axes[0].axvline(x=self.current.annotations['pdOnset'],
                             linestyle=':', color="deepskyblue", lw=1)
            self.data_axes[1].axvline(x=self.current.annotations['pdOnset'],
                             linestyle=':', color="deepskyblue", lw=1)
        if self.display_tongue:
            self.draw_ultra_frame()

    def draw_ultra_frame(self):
        """
        Display an already interpolated ultrasound frame.
        """
        index = 1
        if self.current.excluded:
            self.ultra_axes.clear()
        elif self.current.annotations['pdOnsetIndex']:
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
            if 'RawUltrasound' in self.current.modalities:
                self.current.modalities['RawUltrasound'].data = None
            self.index += 1
            self.update()
            self.update_ui()

    def _update_pd_onset(self):
        audio = self.current.modalities['MonoAudio']
        stimulus_onset = audio.go_signal

        pd_metrics = self.current.modalities['PD l2 on RawUltrasound']
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

    def save_textgrid(self):
        """
        Save the recordings.
        """
        if not self.current._textgrid_path:
            (self.current._textgrid_path, _) = QFileDialog.getSaveFileName(
                self, 'Save file', directory='.', filter="TextGrid files (*.TextGrid)")
        if self.current._textgrid_path and self.current.satgrid:
            with open(self.current._textgrid_path, 'w') as outfile:
                outfile.write(self.current.satgrid.format_long())
            _qt_annotator_logger.info(
                "Wrote TextGrid to file %s.", str(self.current._textgrid_path))

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
        stimulus_onset = audio.go_signal

        pd_metrics = self.current.modalities['PD l2 on RawUltrasound']
        ultra_time = pd_metrics.timevector - stimulus_onset
        self.current.annotations['pdOnsetIndex'] = np.nonzero(
            ultra_time >= event.pickx)[0][0]
        self.update()

    def resizeEvent(self, event):
        """Handle window being resized."""
        self.update()
        QMainWindow.resizeEvent(self, event)
