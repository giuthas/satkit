#
# Copyright (c) 2019-2024
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

from argparse import Namespace
import csv
import logging
from contextlib import closing
from copy import deepcopy
from pathlib import Path

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from icecream import ic
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

from satkit.data_structures import Session
from satkit.configuration import (
    GuiConfig, TimeseriesNormalisation, config_dict
)
from satkit.export import (
    export_aggregate_image_and_meta,
    export_distance_matrix_and_meta,
    export_session_and_recording_meta, export_ultrasound_frame_and_meta
)
from satkit.gui import (
    BoundaryAnimator, ImageSaveDialog, ListSaveDialog,
    ReplaceDialog
)
from satkit.plot_and_publish import (
    get_colors_in_sequence,
    mark_peaks, plot_spline, plot_satgrid_tier, plot_spectrogram,
    plot_timeseries, plot_wav
)
from satkit.plot_and_publish.plot import plot_spectrogram2
from satkit.save_and_load import (
    save_recording_session, load_recording_session
)
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

    def __init__(
            self,
            recording_session: Session,
            args: Namespace,
            gui_config: GuiConfig,
            xlim: tuple[float, float] = (-0.25, 1.5),
            categories: list[str] | None = None,
            pickle_filename: Path | str | None = None
    ):
        super().__init__()
        self.setupUi(self)

        setup_qtannotator_ui_callbacks()

        self.session = recording_session
        self.recordings = recording_session.recordings
        self.index = 0
        self.max_index = len(self.recordings)

        self.commandline_args = args
        self.display_tongue = args.displayTongue

        self.gui_config = gui_config

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

        # self.export_figure_shortcut = QShortcut(QKeySequence(
        #     self.tr("Ctrl+E", "File|Export figure...")), self)
        # self.export_figure_shortcut.activated.connect(self.export_figure)

        self.action_open.triggered.connect(self.open)
        self.action_save_all.triggered.connect(self.save_all)
        self.action_save_current_textgrid.triggered.connect(self.save_textgrid)
        self.action_save_all_textgrids.triggered.connect(
            self.save_all_textgrids)
        # self.actionSaveToPickle.triggered.connect(self.save_to_pickle)

        self.action_export_aggregate_images.triggered.connect(
            self.export_aggregate_image)
        self.action_export_annotations_and_metadata.triggered.connect(
            self.export_annotations_and_meta_data)
        self.action_export_distance_matrices.triggered.connect(
            self.export_distance_matrix)
        self.action_export_main_figure.triggered.connect(self.export_figure)
        self.action_export_ultrasound_frame.triggered.connect(
            self.export_ultrasound_frame)

        self.actionNext.triggered.connect(self.next)
        self.actionPrevious.triggered.connect(self.prev)

        self.actionNext_Frame.triggered.connect(self.next_frame)
        self.actionPrevious_Frame.triggered.connect(self.previous_frame)

        self.action_quit.triggered.connect(self.quit)

        #
        # GUI buttons
        #
        self.nextButton.clicked.connect(self.next)
        self.prevButton.clicked.connect(self.prev)
        self.saveButton.clicked.connect(self.save_all)
        self.exportButton.clicked.connect(
            self.export_annotations_and_meta_data)

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

        # plt.style.use('dark_background')
        plt.style.use('tableau-colorblind10')
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.mplWindowVerticalLayout.addWidget(self.canvas)
        self.data_axes = []
        self.tier_axes = []
        self.animators = []

        self.shift_is_held = False
        # self.cid_key_press = self.figure.canvas.mpl_connect(
        #     'key_press_event', self.on_key_press)
        # self.cid_key_release = self.figure.canvas.mpl_connect(
        #     'key_release_event', self.on_key_release)

        matplotlib.rcParams.update(
            {'font.size': self.gui_config.default_font_size}
        )

        self.xlim = xlim

        height_ratios = [self.gui_config.data_and_tier_height_ratios.data,
                         self.gui_config.data_and_tier_height_ratios.tier]
        self.main_grid_spec = self.figure.add_gridspec(
            nrows=2,
            ncols=1,
            hspace=0,
            wspace=0,
            height_ratios=height_ratios)
        self.tier_grid_spec = None

        number_of_data_axes = self.gui_config.number_of_data_axes
        self.data_grid_spec = self.main_grid_spec[0].subgridspec(
            number_of_data_axes, 1, hspace=0, wspace=0)

        data_axes_params = None
        if gui_config.general_axes_params:
            general_axes_params = gui_config.general_axes_params
            if general_axes_params is not None:
                data_axes_params = general_axes_params

        for i, axes_name in enumerate(gui_config.data_axes):
            # There used to be a 'global' axes which has been moved to
            # 'general_axes_params' this may still cause problems with old
            # config files and should be fixed in them, not here.
            sharex = False
            if gui_config.data_axes[axes_name].sharex:
                sharex = gui_config.data_axes[axes_name].sharex
            elif (data_axes_params is not None and
                  data_axes_params.sharex is not None):
                sharex = data_axes_params.sharex

            if i != 0 and sharex:
                self.data_axes.append(
                    self.figure.add_subplot(
                        self.data_grid_spec[i],
                        sharex=self.data_axes[0]))
            else:
                self.data_axes.append(
                    self.figure.add_subplot(
                        self.data_grid_spec[i]))

        self.ultra_fig = Figure()
        self.ultra_canvas = FigureCanvas(self.ultra_fig)
        self.verticalLayout_6.addWidget(self.ultra_canvas)
        self.ultra_axes = self.ultra_fig.add_axes((0, 0, 1, 1))

        if not self.current.excluded:
            self.draw_plots()
        else:
            self.display_exclusion()

        self.figure.align_ylabels()

        self.multicursor = None

        self.show()
        self.ultra_canvas.draw()
        self.update()

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
        text = 'Recording: ' + str(self.index + 1) + '/' + str(self.max_index)
        text += ', prompt: ' + self.current.meta_data.prompt
        return text

    def _get_long_title(self):
        """
        Private helper function for generating a longer title for a figure.
        """
        text = 'Recording: ' + str(self.index + 1) + '/' + str(self.max_index)
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
        self.draw_plots()
        self.multicursor = MultiCursor(
            self.canvas,
            axes=self.data_axes + self.tier_axes,
            color='deepskyblue', linestyle="--", lw=1)
        self.figure.canvas.draw()

        if self.display_tongue:
            _logger.debug("Drawing ultra frame in update")
            self.draw_ultra_frame()

    def update_ui(self):
        """
        Updates parts of the UI outwith the graphs.
        """
        position_annotation = self.current.annotations['tonguePosition']
        if position_annotation in self.position_rbs:
            button_to_activate = self.position_rbs[position_annotation]
            button_to_activate.setChecked(True)

        self.goLineEdit.setText(str(self.index + 1))

    def plot_modality_axes(
            self,
            axes_number: int,
            axes_name: str,
            zero_offset: float = 0,
            ylim: list[float, float] | None = None
    ) -> None:
        """
        Plot modalities on a data_axes.

        Parameters
        ----------
        axes_number : int
            Which axes, counting from top.
        axes_name : str
            What should the axes be called. This will be the y_label.
        zero_offset : Optional[float], optional
            Where do we set 0 in time in relation to the audio, by default 0
        ylim : Optional[list[float, float]], optional
            y limits, by default None
        """
        axes_params = self.gui_config.data_axes[axes_name]
        plot_modality_names = axes_params.modalities

        if ylim is None:
            ylim = (-0.05, 1.05)

        y_offset = 0
        if axes_params.y_offset is not None:
            y_offset = axes_params.y_offset
            ylim_adjustment = y_offset * len(plot_modality_names)
            if y_offset > 0:
                ylim = (ylim[0], ylim[1] + ylim_adjustment)
            else:
                ylim = (ylim[0] + ylim_adjustment, ylim[1])

        if axes_params.colors_in_sequence:
            colors = get_colors_in_sequence(len(plot_modality_names))
        else:
            colors = None
        for i, name in enumerate(plot_modality_names):
            modality = self.current.modalities[name]
            plot_timeseries(
                self.data_axes[axes_number],
                modality.data,
                modality.timevector - zero_offset,
                self.xlim, ylim,
                color=colors[i],
                linestyle=(0, (i + 1, i + 1)),
                normalise=TimeseriesNormalisation(peak=True, bottom=True),
                y_offset=i * y_offset,
                sampling_step=i + 1,
                label=f"{modality.sampling_rate / (i + 1):.2f} Hz"
            )
            if axes_params.mark_peaks:
                mark_peaks(self.data_axes[axes_number],
                           modality,
                           self.xlim,
                           display_prominence_values=True,
                           time_offset=zero_offset)
            self.data_axes[axes_number].set_ylabel(axes_name)

    def display_exclusion(self):
        """
        Updates title and graphs to show this Recording is excluded.
        """
        self.data_axes[0].set_title(
            self._get_title() + "\nNOTE: This recording has been excluded.")

    def draw_plots(self):
        """
        Updates title and graphs. Called by self.update().
        """
        if self.current.excluded:
            self.display_exclusion()

        if 'MonoAudio' in self.current.modalities:
            self.data_axes[0].set_title(self._get_long_title())
        else:
            self.data_axes[0].set_title(
                self._get_long_title() + "\nNOTE: Audio missing.")
            return

        for axes in self.tier_axes:
            axes.remove()
        self.tier_axes = []
        if self.current.satgrid:
            nro_tiers = len(self.current.satgrid)
            self.tier_grid_spec = self.main_grid_spec[1].subgridspec(
                nro_tiers, 1, hspace=0, wspace=0)
            for axes_counter, tier in enumerate(self.current.textgrid):
                axes = self.figure.add_subplot(
                    self.tier_grid_spec[axes_counter],
                    sharex=self.data_axes[0])
                axes.set_yticks([])
                self.tier_axes.append(axes)

        for axes in self.data_axes:
            axes.xaxis.set_tick_params(bottom=False, labelbottom=False)

        for axes in self.tier_axes[:-1]:
            axes.xaxis.set_tick_params(bottom=False, labelbottom=False)

        if 'MonoAudio' not in self.current.modalities:
            return

        audio = self.current.modalities['MonoAudio']
        stimulus_onset = audio.go_signal
        wav = audio.data
        wav_time = audio.timevector - stimulus_onset

        self.xlim = (-.25, 1.5)
        if self.gui_config.xlim is not None:
            self.xlim = self.gui_config.xlim
        elif self.gui_config.auto_xlim:
            x_minimums = []
            x_maximums = []
            modalities_to_check = self.gui_config.plotted_modality_names()
            modalities_to_check.add("MonoAudio")
            for name in modalities_to_check:
                if name in self.current:
                    x_minimums.append(
                        self.current[name].timevector[0] - stimulus_onset)
                    x_maximums.append(
                        self.current[name].timevector[-1] - stimulus_onset)
            self.xlim = (np.min(x_minimums)-.05, np.max(x_maximums)+.05)

        axes_counter = 0
        for axes_name in self.gui_config.data_axes:
            match axes_name:
                case "spectrogram":
                    plot_spectrogram(self.data_axes[axes_counter],
                                     waveform=wav,
                                     ylim=(0, 10500),
                                     sampling_frequency=audio.sampling_rate,
                                     extent_on_x=(wav_time[0], wav_time[-1]))
                case "spectrogram2":
                    plot_spectrogram2(
                        self.data_axes[axes_counter],
                        waveform=wav,
                        ylim=(0, 10500),
                        sampling_frequency=audio.sampling_rate,
                        extent_on_x=(wav_time[0], wav_time[-1]))
                # TODO: figure out if this should be just completely removed.
                # looks like some old experiment.
                # add `image =` to spectrogram2 to make this work:
                # case "spectrogram distro":
                #     spectrum_data = image.get_array().flatten()
                #     ic(np.min(spectrum_data), np.max(spectrum_data))
                #     self.data_axes[axes_counter].hist(
                #         spectrum_data, bins=200)
                #     ic(np.quantile(spectrum_data,
                #        [.3, .4, .5, .6, .7, .8, .9, 1]))
                case "wav":
                    plot_wav(ax=self.data_axes[axes_counter],
                             waveform=wav,
                             wav_time=wav_time,
                             xlim=self.xlim)
                case _:
                    if not self.current.excluded:
                        self.plot_modality_axes(
                            axes_number=axes_counter,
                            axes_name=axes_name,
                            zero_offset=stimulus_onset)
            axes_counter += 1

        self.data_axes[0].legend(
            loc='upper left')

        # TODO: the sync is iffy with this one, but plotting a pd spectrum is
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
            if name in self.gui_config.pervasive_tiers:
                for data_axis in self.data_axes:
                    boundary_set = plot_satgrid_tier(
                        data_axis, tier, time_offset=stimulus_onset,
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
            for axes in self.data_axes:
                axes.axvline(x=self.current.annotations['selected_time'],
                             linestyle=':', color="deepskyblue", lw=1)
            self.data_axes[-1].axvline(
                x=self.current.annotations['selected_time'],
                linestyle=':', color="white", lw=1)
            for axes in self.tier_axes:
                axes.axvline(x=self.current.annotations['selected_time'],
                             linestyle=':', color="deepskyblue", lw=1)

    def draw_ultra_frame(self):
        """
        Display an already interpolated ultrasound frame.
        """
        if self.current.annotations['selection_index'] == -1:
            self.action_export_ultrasound_frame.setEnabled(False)
            self.ultra_axes.clear()
            image_name = 'AggregateImage mean on RawUltrasound'
            if image_name in self.current.statistics:
                stat = self.current.statistics[image_name]
                image = stat.data
                self.ultra_axes.imshow(
                    image, interpolation='nearest', cmap='gray',
                    extent=(-image.shape[1] / 2 - .5, image.shape[1] / 2 + .5,
                            -.5, image.shape[0] + .5))
        elif self.current.annotations['selection_index'] >= 0:
            self.action_export_ultrasound_frame.setEnabled(True)
            self.ultra_axes.clear()
            index = self.current.annotations['selection_index']

            ultrasound = self.current.modalities['RawUltrasound']
            image = ultrasound.interpolated_image(index)

            self.ultra_axes.imshow(
                image, interpolation='nearest', cmap='gray',
                extent=(-image.shape[1] / 2 - .5, image.shape[1] / 2 + .5,
                        -.5, image.shape[0] + .5))

            if 'Splines' in self.current.modalities:
                splines = self.current.modalities['Splines']
                index = self.current.annotations['selection_index']
                ultra = self.current.modalities['RawUltrasound']
                timestamp = ultra.timevector[index]

                spline_index = np.argmin(
                    np.abs(splines.timevector - timestamp))

                # TODO: move this to reading splines/end of loading and make
                # the system warn the user when there is a creeping
                # discrepancy. also make it an integration test where
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

                spline_config = self.session.meta_data.spline_config
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
        if self.current.annotations['selection_index'] > -1:
            self.action_export_ultrasound_frame.setEnabled(True)
            ind = self.current.annotations['selection_index']
            array = self.current.modalities['RawUltrasound'].data[ind, :, :]
        else:
            self.action_export_ultrasound_frame.setEnabled(False)
            if self.current.statistics['Aggregate mean on RawUltrasound']:
                array = self.current.modalities[
                    'Aggregate mean on RawUltrasound'].data
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
        if self.index < self.max_index - 1:
            # TODO: make it possible to select which modalities get their
            # memory released
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
        if 'PD l1 on RawUltrasound' not in self.current.modalities:
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
        index_to_jump_to = int(self.goLineEdit.text()) - 1

        if 0 <= index_to_jump_to < len(self.session):
            self.current.modalities['RawUltrasound'].data = None
            self.index = index_to_jump_to
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
            self.session = load_recording_session(
                directory=directory)
            self.recordings = self.session.recordings
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
        _logger.warning(
            "Don't yet know how to open a file "
            "even though I know the name is %s.", filename)

    def save_all(self):
        """
        Save derived modalities and annotations.
        """
        # TODO 1.0: write a call back for asking for overwrite confirmation.
        save_recording_session(self.session)

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
                "Pickling is currently disabled. Did NOT write file %s.",
                self.pickle_filename)
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
                self, 'Save TextGrid', directory='.',
                filter="TextGrid files (*.TextGrid)")
        if self.current.textgrid_path and self.current.satgrid:
            file = self.current.textgrid_path
            with open(file, 'w', encoding='utf-8') as outfile:
                outfile.write(self.current.satgrid.format_long())
            _logger.info(
                "Wrote TextGrid to file %s.",
                str(self.current.textgrid_path))

    def save_all_textgrids(self):
        """
        Save the all TextGrids in this Session.
        """
        # TODO 1.0: write a call back for asking for overwrite confirmation.
        for recording in self.session:
            if not recording.textgrid_path:
                # TODO: This will be SUPER ANNOYING when there are a lot of
                # recordings. Instead, ask for the directory to save in. In any
                # case needs to be reworked when SATKIT files no longer live
                # with the recorded data.
                (recording.textgrid_path, _) = QFileDialog.getSaveFileName(
                    self, 'Save TextGrid', directory='.',
                    filter="TextGrid files (*.TextGrid)")
            if recording.textgrid_path and recording.satgrid:
                file = recording.textgrid_path
                with open(file, 'w', encoding='utf-8') as outfile:
                    outfile.write(recording.satgrid.format_long())
                _logger.info(
                    "Wrote TextGrid to file %s.",
                    str(recording.textgrid_path))

    def export_figure(self):
        """
        Callback method to export the current figure in any supported format.

        Opens a filedialog to ask for the filename. Save format is determined
        by file extension.
        """
        suggested_path = Path.cwd() / "Satkit_figure.png"
        filename, _ = ImageSaveDialog.get_selection(
            name="Export the main figure",
            save_path=suggested_path,
            parent=self,
        )
        if filename is not None:
            self.figure.savefig(filename, bbox_inches='tight', pad_inches=0.05)
            export_session_and_recording_meta(
                filename=filename, session=self.session, recording=self.current,
                description="main GUI figure"
            )

    def export_ultrasound_frame(self) -> None:
        """
        Export the currently selected ultrasound frame and its meta data.

        The metadata is written to a separate `.txt` file of the same name as
        the image file.
        """
        # TODO: Add a check that grays out the export ultrasound figure when one
        # isn't available.

        if self.current.annotations['selection_index'] >= 0:
            suggested_path = Path.cwd() / "Raw_ultrasound_frame.png"
            path, options = ImageSaveDialog.get_selection(
                name="Export ultrasound frame",
                save_path=suggested_path,
                parent=self,
                options={'Export interpolated frame': True}
            )
            if path is None:
                return

            if options['Export interpolated frame']:
                ultrasound_modality = self.current['RawUltrasound']
                interpolation_params = ultrasound_modality.interpolation_params
            else:
                interpolation_params = None

            export_ultrasound_frame_and_meta(
                filepath=path,
                session=self.session,
                recording=self.current,
                selection_index=self.current.annotations['selection_index'],
                selection_time=self.current.annotations['selected_time'],
                ultrasound=self.current['RawUltrasound'],
                interpolation_params=interpolation_params
            )

    def export_aggregate_image(self) -> None:
        """
        Export AggregateImages connected with the current recording.
        
        The metadata is written to a separate `.txt` file of the same name as
        the corresponding image file.
        """
        statistics_names = self.current.statistics.keys()
        choice_list = [
            name for name in statistics_names if 'AggregateImage' in name]
        image_list, path, export_interpolated = ListSaveDialog.get_selection(
            name="Export AggregateImages",
            item_names=choice_list,
            parent=self,
            option_label='Export interpolated image'
        )
        if image_list is None:
            return

        if export_interpolated:
            ultrasound = "RawUltrasound"
            ultrasound_modality = next(
                recording[ultrasound] for recording in self.session
                if ultrasound in recording
            )
            interpolation_params = ultrasound_modality.interpolation_params
        else:
            interpolation_params = None

        for image in image_list:
            export_aggregate_image_and_meta(
                image=self.current.statistics[image],
                session=self.session,
                recording=self.current,
                path=path,
                interpolation_params=interpolation_params,
            )

    def export_distance_matrix(self) -> None:
        """
        Export DistanceMatrices connected with the current session.

        The metadata is written to a separate `.txt` file of the same name as
        the corresponding image file.
        """
        statistics_names = self.session.statistics.keys()
        choice_list = [
            name for name in statistics_names if 'DistanceMatrix' in name]
        matrix_list, path, _ = ListSaveDialog.get_selection(
            name="Export DistanceMatrices",
            item_names=choice_list,
            parent=self,
        )
        if matrix_list is None:
            return

        for matrix in matrix_list:
            export_distance_matrix_and_meta(
                matrix=self.session.statistics[matrix],
                session=self.session,
                path=path)

    def export_annotations_and_meta_data(self) -> None:
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
                            recording['MonoAudio'].go_signal)
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
                "Wrote onset data in file %s.", filename)

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
                subplot = i + 1
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

    # noinspection PyPep8Naming
    def keyPressEvent(self, event):
        """
        Key press callback.

        QtPy is silly and wants the callback to have this specific name.
        """
        if event.key() == Qt.Key_Shift:
            self.shift_is_held = True
        if event.key() == Qt.Key_I:
            self.gui_config.auto_xlim = False
            if self.current.annotations['selection_index'] >= 0:
                center = self.current.annotations['selected_time']
            else:
                center = (self.xlim[0] + self.xlim[1]) / 2.0
            length = (self.xlim[1] - self.xlim[0]) * .25
            self.xlim = (center - length, center + length)
            if self.gui_config.xlim is not None:
                self.gui_config.xlim = self.xlim
            self.update()
        elif event.key() == Qt.Key_O:
            self.gui_config.auto_xlim = False
            center = (self.xlim[0] + self.xlim[1]) / 2.0
            length = self.xlim[1] - self.xlim[0]
            self.xlim = (center - length, center + length)
            if self.gui_config.xlim is not None:
                self.gui_config.xlim = self.xlim
            self.update()
        elif event.key() == Qt.Key_A:
            self.gui_config.auto_xlim = True
            self.gui_config.xlim = None
            self.update()

    # noinspection PyPep8Naming
    def keyReleaseEvent(self, event):
        """
        Key release callback.

        QtPy is silly and wants the callback to have this specific name.
        """
        if event.key() == Qt.Key_Shift:
            self.shift_is_held = False
