#
# Copyright (c) 2019-2023
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
"""
This is the main GUI class for SATKIT.
"""


# Built in packages
import csv
import logging
from contextlib import closing
from copy import deepcopy

import numpy as np
import matplotlib
from matplotlib.backends.backend_qt5agg import \
    FigureCanvasQTAgg as FigureCanvas
# Plotting functions and hooks for GUI
from matplotlib.figure import Figure
from matplotlib.widgets import MultiCursor
# GUI functionality
from PyQt5.QtCore import QCoreApplication, Qt
from PyQt5.QtGui import QIntValidator, QKeySequence
from PyQt5.QtWidgets import QFileDialog, QShortcut
from PyQt5.uic import loadUiType

from icecream import ic

# Local modules
# import satkit.io as satkit_io
from satkit.data_structures import RecordingSession
from satkit.constants import TimeseriesNormalisation
from satkit.configuration import gui_params, config_dict, data_run_params
from satkit.gui import BoundaryAnimator, ReplaceDialog
from satkit.plot_and_publish.plot import plot_spline
from satkit.plot_and_publish import (
    plot_satgrid_tier, plot_spectrogram, plot_timeseries, plot_wav)
from satkit.save_and_load import (
    save_recording_session, load_recording_session)
from satkit.ui_callbacks import UiCallbacks

# Load the GUI layout generated with QtDesigner.
Ui_MainWindow, QMainWindow = loadUiType('satkit/gui/qt_annotator.ui')

_logger = logging.getLogger('satkit.qt_annotator')


def setup_qtannotator_ui_callbacks():
    """
    Register UI callback functions.
    """
    UiCallbacks.register_overwrite_confirmation_callback(
        ReplaceDialog.confirm_overwrite)


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

    def __init__(self, recording_session: RecordingSession, args,
                 xlim=(-0.25, 1.5),
                 categories=None, pickle_filename=None):
        super().__init__()
        self.setupUi(self)

        setup_qtannotator_ui_callbacks()

        self.recording_session = recording_session
        self.recordings = recording_session.recordings
        self.index = 0
        self.max_index = len(self.recordings)

        self.commandline_args = args
        self.display_tongue = args.displayTongue

        if categories is None:
            self.categories = PdQtAnnotator.default_categories
        else:
            self.categories = categories
        self.tongue_positions = PdQtAnnotator.default_tongue_positions
        self._add_annotations()

        self.pickle_filename = pickle_filename

        #
        # Menu actions and shortcuts
        #
        self.close_window_shortcut = QShortcut(
            QKeySequence(self.tr("Ctrl+W", "File|Quit")), self)
        self.close_window_shortcut.activated.connect(self.quit)

        self.export_figure_shortcut = QShortcut(QKeySequence(
            self.tr("Ctrl+E", "File|Export figure...")), self)
        self.export_figure_shortcut.activated.connect(self.export_figure)

        self.actionOpen.triggered.connect(self.open)
        self.actionSaveAll.triggered.connect(self.save_all)
        # self.actionSaveToPickle.triggered.connect(self.save_to_pickle)
        self.action_export_figure.triggered.connect(self.export_figure)

        self.actionNext.triggered.connect(self.next)
        self.actionPrevious.triggered.connect(self.prev)

        self.actionNext_Frame.triggered.connect(self.next_frame)
        self.actionPrevious_Frame.triggered.connect(self.previous_frame)

        self.actionQuit.triggered.connect(self.quit)

        #
        # GUI buttons
        #
        self.nextButton.clicked.connect(self.next)
        self.prevButton.clicked.connect(self.prev)
        self.saveButton.clicked.connect(self.save_all)
        self.exportButton.clicked.connect(self.export)

        go_validator = QIntValidator(1, self.max_index + 1, self)
        self.goLineEdit.setValidator(go_validator)
        self.goButton.clicked.connect(self.go_to_recording)

        # TODO: add recording list to the display and highlight current
        # recording

        # self.categoryRB_1.toggled.connect(self.pd_category_cb)
        # self.categoryRB_2.toggled.connect(self.pd_category_cb)
        # self.categoryRB_3.toggled.connect(self.pd_category_cb)
        # self.categoryRB_4.toggled.connect(self.pd_category_cb)
        # self.categoryRB_5.toggled.connect(self.pd_category_cb)

        self.positionRB_1.toggled.connect(self.tongue_position_cb)
        self.positionRB_2.toggled.connect(self.tongue_position_cb)
        self.positionRB_3.toggled.connect(self.tongue_position_cb)
        self.position_rbs = {
            self.positionRB_1.text(): self.positionRB_1,
            self.positionRB_2.text(): self.positionRB_2,
            self.positionRB_3.text(): self.positionRB_3
        }

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.mplWindowVerticalLayout.addWidget(self.canvas)
        self.data_axes = []
        self.tier_axes = []

        self.shift_is_held = False
        # self.cid_key_press = self.figure.canvas.mpl_connect(
        #     'key_press_event', self.on_key_press)
        # self.cid_key_release = self.figure.canvas.mpl_connect(
        #     'key_release_event', self.on_key_release)

        matplotlib.rcParams.update(
            {'font.size': gui_params['default font size']})

        self.xlim = xlim

        # TODO this should be based on the plotted modalities, not on a random
        # choice from depths of time. It is a good idea though: Setting ylim
        # over the whole data rather than on recording.
        max_pds = np.zeros(len(self.recordings))
        for i, recording in enumerate(self.recordings):
            if 'PD l1 on RawUltrasound' in recording.modalities:
                max_pds[i] = np.max(recording.modalities
                                    ['PD l1 on RawUltrasound'].data[10:])
        self.ylim = (-50, np.max(max_pds)*1.05)

        height_ratios = [gui_params['data/tier height ratios']["data"],
                         gui_params['data/tier height ratios']["tier"]]
        self.main_grid_spec = self.figure.add_gridspec(
            nrows=2,
            ncols=1,
            hspace=0,
            wspace=0,
            height_ratios=height_ratios)

        nro_data_modalities = gui_params['number of data axes']
        self.data_grid_spec = self.main_grid_spec[0].subgridspec(
            nro_data_modalities, 1, hspace=0, wspace=0)
        self.data_axes.append(self.figure.add_subplot(self.data_grid_spec[0]))
        for i in range(1, nro_data_modalities):
            self.data_axes.append(
                self.figure.add_subplot(
                    self.data_grid_spec[i],
                    sharex=self.data_axes[0]))

        self.ultra_fig = Figure()
        self.ultra_canvas = FigureCanvas(self.ultra_fig)
        self.verticalLayout_6.addWidget(self.ultra_canvas)
        self.ultra_axes = self.ultra_fig.add_axes([0, 0, 1, 1])

        if not self.current.excluded:
            self.draw_plots()

        self.figure.align_ylabels()

        self.multicursor = None

        self.show()
        self.ultra_canvas.draw()

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
            'selected_time': -1.0,
            'selection_index': -1,
        }

    def _add_annotations(self):
        """Add the annotations."""
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

    def _get_long_title(self):
        """
        Private helper function for generating a longer title for a figure.
        """
        text = 'Recording: ' + str(self.index+1) + '/' + str(self.max_index)
        text += ', Speaker: ' + str(self.current.meta_data.participant_id)
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

        self.draw_plots()
        self.multicursor = MultiCursor(
            self.canvas,
            axes=self.data_axes+self.tier_axes,
            color='deepskyblue', linestyle="--", lw=1)
        self.figure.canvas.draw()

        if self.display_tongue:
            _logger.debug("Drawing ultra frame in update")
            self.draw_ultra_frame()

    def update_ui(self):
        """
        Updates parts of the UI outwith the graphs.
        """
        # TODO: highlight current recording

        position_annotation = self.current.annotations['tonguePosition']
        if position_annotation in self.position_rbs:
            button_to_activate = self.position_rbs[position_annotation]
            button_to_activate.setChecked(True)

        self.goLineEdit.setText(str(self.index + 1))

    def draw_plots(self):
        """
        Updates title and graphs. Called by self.update().
        """
        self.data_axes[0].set_title(self._get_title())
        self.data_axes[0].set_title(self._get_long_title())

        for axes in self.tier_axes:
            axes.remove()
        self.tier_axes = []
        if self.current.satgrid:
            nro_tiers = len(self.current.satgrid)
            self.tier_grid_spec = self.main_grid_spec[1].subgridspec(
                nro_tiers, 1, hspace=0, wspace=0)
            for i, tier in enumerate(self.current.textgrid):
                axes = self.figure.add_subplot(self.tier_grid_spec[i],
                                               sharex=self.data_axes[0])
                axes.set_yticks([])
                self.tier_axes.append(axes)

        for axes in self.data_axes:
            axes.xaxis.set_tick_params(bottom=False, labelbottom=False)

        for axes in self.tier_axes[:-1]:
            axes.xaxis.set_tick_params(bottom=False, labelbottom=False)

        # self.tier_axes[-1].xaxis.set_tick_params(labelbottom=True)
        # ticks = self.tier_axes[-1].xaxis.set_tick_params(bottom=True,
        #                                                  labelbottom=True)

        audio = self.current.modalities['MonoAudio']
        stimulus_onset = audio.go_signal
        wav = audio.data
        wav_time = audio.timevector - stimulus_onset

        # ic(self.current.modalities)

        l1 = self.current.modalities['PD l1 on RawUltrasound']

        # plot_modality_names = [
        #     (f"PD l1 ts{i+1} on RawUltrasound") for i in range(7)]
        # plot_modality_names[0] = "PD l1 on RawUltrasound"

        plot_modality_names = [
            (f"PD {norm} on RawUltrasound")
            for norm in data_run_params['pd_arguments']['norms'][1:-1]]

        ultra_time = l1.timevector - stimulus_onset
        ylim = None

        if 'auto x' in gui_params and gui_params['auto x']:
            # TODO: find the minimum and maximum timestamp of all the
            # modalities being plotted. this can be really done only after
            # plotting is controlled by config instead of manual code
            self.xlim = (
                np.min([np.min(wav_time), np.min(ultra_time)]),
                np.max([np.max(wav_time), np.max(ultra_time)])
            )
        elif 'xlim' in gui_params:
            self.xlim = gui_params['xlim']
        else:
            self.xlim = (-.25, 1.5)

        # plot_density(self.data_axes[0], frequencies.data)

        plots = []
        labels = []
        for i, name in enumerate(plot_modality_names):
            modality = self.current.modalities[name]
            new = plot_timeseries(
                self.data_axes[i],
                modality.data, modality.timevector-stimulus_onset,
                self.xlim, ylim,
                # color=(0+i*.1, 0+i*.1, 0+i*.1),
                # linestyle=(0, (i+1, i+1)),
                normalise=TimeseriesNormalisation('PEAK AND BOTTOM'),
                find_peaks=True,
                # sampling_step=i+1
            )
            plots.append(new)
            self.data_axes[i].set_ylabel(modality.metadata.metric)
            labels.append(f"{modality.sampling_rate/(i+1):.2f}")

        # self.data_axes[0].legend(
        #     plots, labels,
        #     loc='upper left')

        # self.data_axes[0].set_ylabel("Pixel difference (PD)")

        plot_wav(self.data_axes[-1], wav, wav_time, self.xlim)
        plot_spectrogram(self.data_axes[-2],
                         waveform=wav,
                         ylim=(0, 10500),
                         sampling_frequency=audio.sampling_rate,
                         xtent_on_x=[wav_time[0], wav_time[-1]])

        # TODO: the sync is out with this one, but plotting a pd spectrum is
        # still a good idea. Just need to get the FFT parameters tuned - if
        # that's even possible.
        # plot_spectrogram(self.data_axes[1],
        #                  waveform=l1.data,
        #                  ylim=(0, 60),
        #                  sampling_frequency=l1.sampling_rate,
        #                  noverlap=98, NFFT=100,
        #                  #  xtent_on_x=[-1, 1])  # ,
        #                  xtent_on_x=[ultra_time[0], ultra_time[-1]])  # ,

        # segment_line = None
        self.animators = []
        iterator = zip(self.current.satgrid.items(),
                       self.tier_axes, strict=True)
        for (name, tier), axis in iterator:
            boundaries_by_axis = []

            # boundary_set, segment_line = plot_satgrid_tier(
            boundary_set, _ = plot_satgrid_tier(
                axis, tier, time_offset=stimulus_onset, text_y=.5)
            boundaries_by_axis.append(boundary_set)
            axis.set_ylabel(
                name, rotation=0, horizontalalignment="right",
                verticalalignment="center")
            axis.set_xlim(self.xlim)
            if name in gui_params["pervasive tiers"]:
                for axis in self.data_axes:
                    boundary_set = plot_satgrid_tier(
                        axis, tier, time_offset=stimulus_onset,
                        draw_text=False)[0]
                    boundaries_by_axis.append(boundary_set)

            # Change rows to be individual boundaries instead of axis. This
            # makes it possible to create animators for each boundary as
            # represented by multiple lines on different axes.
            boundaries_by_boundary = list(map(list, zip(*boundaries_by_axis)))

            for boundaries, interval in zip(
                    boundaries_by_boundary, tier, strict=True):
                animator = BoundaryAnimator(
                    self, boundaries, interval, stimulus_onset)
                animator.connect()
                self.animators.append(animator)
        if self.tier_axes:
            self.tier_axes[-1].set_xlabel("Time (s), go-signal at 0 s.")

        self.figure.tight_layout()

        if self.current.annotations['selected_time'] > -1:
            for axes in self.data_axes[:-1]:
                axes.axvline(x=self.current.annotations['selected_time'],
                             linestyle=':', color="deepskyblue", lw=1)
            self.data_axes[-1].axvline(x=self.current.annotations
                                       ['selected_time'],
                                       linestyle=':', color="white", lw=1)
            for axes in self.tier_axes:
                axes.axvline(x=self.current.annotations['selected_time'],
                             linestyle=':', color="deepskyblue", lw=1)

        # if self.display_tongue:
        #     _qt_annotator_logger.debug("Drawing ultra frame in plots")
        #     self.draw_ultra_frame()

    def draw_ultra_frame(self):
        """
        Display an already interpolated ultrasound frame.
        """
        if (self.current.excluded or
                self.current.annotations['selection_index'] == -1):
            self.ultra_axes.clear()
        elif self.current.annotations['selection_index']:
            self.ultra_axes.clear()
            index = self.current.annotations['selection_index']

            ultrasound = self.current.modalities['RawUltrasound']
            image = ultrasound.interpolated_image(index)

            self.ultra_axes.imshow(
                image, interpolation='nearest', cmap='gray',
                extent=(-image.shape[1]/2-.5, image.shape[1]/2+.5,
                        -.5, image.shape[0]+.5))

            if 'Splines' in self.current.modalities:
                splines = self.current.modalities['Splines']
                index = self.current.annotations['selection_index']
                ultra = self.current.modalities['RawUltrasound']
                timestamp = ultra.timevector[index]

                spline_index = np.argmin(
                    np.abs(splines.timevector - timestamp))

                # TODO: move this to reading splines/end of loading and make
                # the system warn the user when there is a creeping
                # discrepancy. also make it a integration test where
                # spline_test_token1 gets run and triggers this
                # ic(splines.timevector)
                # ic(ultra.timevector[:len(splines.timevector)])
                # time_diff = splines.timevector - \
                #     ultra.timevector[:len(splines.timevector)]
                # ic(np.diff(time_diff, n=1))
                # ic(np.max(np.abs(np.diff(time_diff, n=1))))

                epsilon = max((config_dict['epsilon'], splines.time_precision))
                min_difference = abs(
                    splines.timevector[spline_index] - timestamp)
                # maybe this instead when loading data
                # str(number)[::-1].find('.') -> precision

                # ic(epsilon, splines.timevector[spline_index] - timestamp)
                # ic(splines.timevector[spline_index], timestamp)
                if min_difference > epsilon:
                    _logger.info("Splines out of synch in %s.",
                                 self.current.basename)
                    _logger.info("Minimal difference: %f, epsilon: %f",
                                 min_difference, epsilon)

                spline_config = self.recording_session.config.spline_config
                if spline_config.data_config:
                    limits = spline_config.data_config.ignore_points
                    plot_spline(self.ultra_axes,
                                splines.cartesian_spline(spline_index),
                                limits=limits)
                else:
                    plot_spline(self.ultra_axes,
                                splines.cartesian_spline(spline_index))
            else:
                _logger.info("No splines")
        self.ultra_canvas.draw()

    def draw_raw_ultra_frame(self):
        """
        Interpolate and display a raw ultrasound frame.
        """
        if self.current.annotations['selection_index']:
            ind = self.current.annotations['selection_index']
            array = self.current.modalities['RawUltrasound'].data[ind, :, :]
        else:
            array = self.current.modalities['RawUltrasound'].data[1, :, :]
        array = np.transpose(array)
        array = np.flip(array, 0).copy()
        array = array.astype(np.int8)
        self.ultra_axes.imshow(array, interpolation='nearest', cmap='gray')
        self.ultra_canvas.draw()

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

        if 'PD l1 on RawUltrasound' in self.current.modalities:
            pd_metrics = self.current.modalities['PD l1 on RawUltrasound']
            ultra_time = pd_metrics.timevector - stimulus_onset
            index = self.current.annotations['selection_index']
            self.current.annotations['selected_time'] = ultra_time[index]

    def next_frame(self):
        """
        Move the data cursor to the next frame.
        """
        if not 'PD l1 on RawUltrasound' in self.current.modalities:
            return

        selection_index = self.current.annotations['selection_index']
        pd = self.current.modalities['PD l1 on RawUltrasound']
        data_length = pd.data.size
        if -1 < selection_index < data_length:
            self.current.annotations['selection_index'] += 1
            _logger.debug(
                "next frame: %d",
                (self.current.annotations['selection_index']))
            self._update_pd_onset()
            self.update()
            self.update_ui()

    def previous_frame(self):
        """
        Move the data cursor to the previous frame.
        """
        if self.current.annotations['selection_index'] > 0:
            self.current.annotations['selection_index'] -= 1
            _logger.debug(
                "previous frame: %d",
                (self.current.annotations['selection_index']))
            self._update_pd_onset()
            self.update()
            self.update_ui()

    def prev(self):
        """
        Callback function for the Previous button.
        Decreases cursor index, updates the view.
        """
        if self.index > 0:
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

    def open(self):
        """
        Open either SATKIT saved data or import new data.
        """
        directory = QFileDialog.getExistingDirectory(
            self, caption="Open directory", directory='.')
        if directory:
            self.recording_session = load_recording_session(
                directory=directory)
            self.recordings = self.recording_session.recordings
            self.index = 0
            self.max_index = len(self.recordings)
            self._add_annotations()
            self.update()

    def open_file(self):
        """
        Open either SATKIT saved data or import new data.
        """
        filename = QFileDialog.getOpenFileName(
            self, caption="Open file", directory='.',
            filter="SATKIT files (*.satkit_meta)")
        print(
            f"Don't yet know how to open a file "
            f"even though I know the name is {filename}.")

    def save_all(self):
        """
        Save derived modalities and annotations.
        """
        # TODO 1.0: write a call back for asking for overwrite confirmation.
        save_recording_session(self.recording_session)

    def save_to_pickle(self):
        """
        Save the recordings into a pickle file.
        """
        if not self.pickle_filename:
            (self.pickle_filename, _) = QFileDialog.getSaveFileName(
                self, 'Save file', directory='.',
                filter="Pickle files (*.pickle)")
        if self.pickle_filename:
            _logger.info(
                "Pickling is currently disabled. Did NOT write file {file}.",
                file=self.pickle_filename)
            # satkit_io.save2pickle(
            #     self.recordings,
            #     self.pickle_filename)
            # _qt_annotator_logger.info(
            #     "Wrote data to file {file}.", file = self.pickle_filename)

    def save_textgrid(self):
        """
        Save the current TextGrid.
        """
        # TODO 1.0: write a call back for asking for overwrite confirmation.
        if not self.current.textgrid_path:
            (self.current.textgrid_path, _) = QFileDialog.getSaveFileName(
                self, 'Save file', directory='.',
                filter="TextGrid files (*.TextGrid)")
        if self.current.textgrid_path and self.current.satgrid:
            file = self.current.textgrid_path
            with open(file, 'w', encoding='utf-8') as outfile:
                outfile.write(self.current.satgrid.format_long())
            _logger.info(
                "Wrote TextGrid to file %s.", str(self.current.textgrid_path))

    def export_figure(self):
        """
        Callback method to export the current figure in any supported format.

        Opens a filedialog to ask for the filename. Save format is determined
        by file extension.
        """
        (filename, _) = QFileDialog.getSaveFileName(
            self, 'Export figure', directory='.')
        self.figure.savefig(filename, bbox_inches='tight', pad_inches=0.05)

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
                annotations['basename'] = recording.basename
                annotations['date_and_time'] = (
                    recording.meta_data.time_of_recording)
                annotations['prompt'] = recording.meta_data.prompt
                annotations['word'] = recording.meta_data.prompt.split()[0]

                word_dur = -1.0
                acoustic_onset = -1.0
                if 'word' in recording.textgrid:
                    for interval in recording.textgrid['word']:
                        # change this to access the phonemeDict and
                        # check for included words, then search for
                        # phonemes based on the same
                        if interval.text == "":
                            continue

                        # Before 1.0: check if there is a duration to use here.
                        # and maybe make this more intelligent by selecting
                        # purposefully the last non-empty first and taking the
                        # duration?
                        word_dur = interval.dur
                        stimulus_onset = (
                            recording.modalities['MonoAudio'].go_signal)
                        acoustic_onset = interval.xmin - stimulus_onset
                        break
                    annotations['word_dur'] = word_dur
                else:
                    annotations['word_dur'] = -1.0

                if acoustic_onset < 0 or annotations['selected_time'] < 0:
                    aai = -1.0
                else:
                    aai = acoustic_onset - annotations['selected_time']
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

                annotations['C1'] = recording.meta_data.prompt[0]
                writer.writerow(annotations)
            _logger.info(
                "Wrote onset data in file %s.", (filename))

    def pd_category_cb(self):
        """
        Callback function for the RadioButton for categorising
        the PD curve.
        """
        radio_button = self.sender()
        if radio_button.isChecked():
            self.current.annotations['pdCategory'] = radio_button.text()

    def tongue_position_cb(self):
        """
        Callback function for the RadioButton for categorising
        the PD curve.
        """
        radio_button = self.sender()
        if radio_button.isChecked():
            self.current.annotations['tonguePosition'] = radio_button.text()

    def onpick(self, event):
        """
        Callback for handling time selection on events.
        """
        if not event.xdata:
            self.current.annotations['selected_time'] = -1
            self.current.annotations['selection_index'] = -1
            self.update()
            return

        subplot = 0
        for i, axes in enumerate(self.data_axes):
            if axes == event.inaxes:
                subplot = i+1
                break

        _logger.debug(
            "Inside onpick - subplot: %d, x=%f",
            subplot, event.xdata)

        # if subplot == 1:
        #     self.current.annotations['selected_time'] = event.pickx

        audio = self.current.modalities['MonoAudio']
        stimulus_onset = audio.go_signal

        timevector = (
            self.current.modalities['PD l1 on RawUltrasound'].timevector)
        distances = np.abs(timevector - stimulus_onset - event.xdata)
        self.current.annotations['selection_index'] = np.argmin(distances)
        self.current.annotations['selected_time'] = event.xdata

        _logger.debug(
            "Inside onpick - subplot: %d, index=%d, x=%f",
            subplot,
            self.current.annotations['selection_index'],
            self.current.annotations['selected_time'])

        self.update()

    def resize_event(self, event):
        """
        Window resize callback.
        """
        self.update()
        QMainWindow.resizeEvent(self, event)

    def keyPressEvent(self, event):
        """
        Key press callback.

        QtPy is silly and wants the callback to have this specific name.
        """
        if event.key() == Qt.Key_Shift:
            self.shift_is_held = True
        if event.key() == Qt.Key_I:
            gui_params['auto x'] = False
            if self.current.annotations['selection_index'] >= 0:
                center = self.current.annotations['selected_time']
            else:
                center = (self.xlim[0] + self.xlim[1])/2.0
            length = (self.xlim[1] - self.xlim[0])*.25
            self.xlim = (center-length, center+length)
            if 'xlim' in gui_params:
                gui_params['xlim'] = self.xlim
            self.update()
        elif event.key() == Qt.Key_O:
            gui_params['auto x'] = False
            center = (self.xlim[0] + self.xlim[1])/2.0
            length = self.xlim[1] - self.xlim[0]
            self.xlim = (center-length, center+length)
            if 'xlim' in gui_params:
                gui_params['xlim'] = self.xlim
            self.update()
        elif event.key() == Qt.Key_A:
            gui_params['auto x'] = True
            self.update()
        # else:
        #     print(event.key())

    def keyReleaseEvent(self, event):
        """
        Key release callback.

        QtPy is silly and wants the callback to have this specific name.
        """
        if event.key() == Qt.Key_Shift:
            self.shift_is_held = False
        # else:
        #     print(event.key)
