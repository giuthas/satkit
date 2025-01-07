#!/usr/bin/env python3
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

# built-in modules
import sys
from pathlib import Path

from matplotlib.backends.backend_pdf import PdfPages

import numpy as np

# For running a Qt GUI
from PyQt5 import QtWidgets

# local modules
from satkit import log_elapsed_time, set_logging_level
from satkit.annotations import (
    add_peaks, count_number_of_peaks, nearest_neighbours_in_downsampling,
    prominences_in_downsampling)
from satkit.annotations.peaks import annotations_to_dataframe
import satkit.configuration as config

from satkit.metrics import (
    add_pd, add_spline_metric, downsample_metrics)
from satkit.modalities import RawUltrasound, Splines
from satkit.plot_and_publish import (
    publish_session_pdf, publish_distribution_data)
from satkit.plot_and_publish.publish import publish_distribution_data_seaborn
from satkit.qt_annotator import PdQtAnnotator
from satkit.scripting_interface import (
    # Operation,
    SatkitArgumentParser,
    load_data,  # multi_process_data,
    process_modalities, save_data)


def main():
    """Simple main to run some publishing functions."""

    # Arguments need to be parsed before setting up logging so that we have
    # access to the verbosity argument.
    cli = SatkitArgumentParser("SATKIT")

    logger = set_logging_level(cli.args.verbose)

    if cli.args.configuration_filename:
        config.parse_config(cli.args.configuration_filename)
    else:
        config.parse_config()
    configuration = config.Configuration(cli.args.configuration_filename)

    recording_session = load_data(Path(cli.args.load_path))

    log_elapsed_time()

    # function_dict = {'pd':pd.pd, 'annd':annd.annd}
    # pd_arguments = {
    #     # 'norms': ['l0', 'l0.01', 'l0.1', 'l0.5', 'l1', 'l2',
    #     # 'l4', 'l10', 'l_inf', 'd'],
    #     'norms': ['l0', 'l0.5', 'l1', 'l2', 'l5', 'l_inf'],
    #     'timesteps': [1, 2, 3, 4, 5, 6, 7],
    #     # 'timesteps': [1],
    #     'mask_images': False,
    #     'pd_on_interpolated_data': False,
    #     'release_data_memory': True,
    #     'preload': True}

    data_run_config = configuration.data_run_config

    function_dict = {}
    if data_run_config.pd_arguments:
        pd_arguments = data_run_config.pd_arguments
        function_dict["PD"] = (
            add_pd,
            [RawUltrasound],
            pd_arguments.model_dump()
        )

    if data_run_config.spline_metric_arguments:
        spline_metric_args = data_run_config.spline_metric_arguments
        function_dict["SplineMetric"] = (
            add_spline_metric,
            [Splines],
            spline_metric_args.model_dump()
        )

    # TODO: turn these commented out bits into an example script of how to do
    # things programmatically.
    # spline_config = recording_session.config.spline_config
    # spline_metric_arguments = {
    #     'metrics': ['annd', 'mpbpd', 'modified_curvature', 'fourier'],
    #     'timesteps': [3],
    #     'exclude_points': spline_config.data_config.ignore_points,
    #     'release_data_memory': False,
    #     'preload': True}

    # function_dict = {
    #     'PD': (add_pd,
    #            [RawUltrasound],
    #            pd_arguments.model_dump()),

    #     'SplineMetric': (add_spline_metric,
    #                      [Splines],
    #                      spline_metric_args.model_dump())  # ,
    # }

    process_modalities(recordings=recording_session.recordings,
                       processing_functions=function_dict)

    # if data_run_config.peaks is not None:
    #     peaks, properties = find_gesture_peaks(
    #         data, data_run_config.peaks)
    # else:
    #     peaks, properties = find_gesture_peaks(data)

    # operation = Operation(processing_function=pd.add_pd,
    #                       modality=RawUltrasound,
    #                       arguments={'mask_images': True,
    #                                  'pd_on_interpolated_data': True,
    #                                  'release_data_memory': True,
    #                                  'preload': True})
    # multi_process_data(recordings, operation)

    if data_run_config.downsample:
        downsample_config = data_run_config.downsample

        for recording in recording_session:
            downsample_metrics(recording, **downsample_config.model_dump())

    exclusion_list = ("water swallow", "bite plate")
    if data_run_config.peaks:
        modality_pattern = data_run_config.peaks.modality_pattern
        for recording in recording_session:
            excluded = [prompt in recording.metadata.prompt
                        for prompt in exclusion_list]
            if any(excluded):
                print(
                    f"in satkit_publish.py: jumping over {recording.basename}")
                continue
            for modality_name in recording:
                if modality_pattern in modality_name:
                    add_peaks(
                        recording[modality_name],
                        configuration.data_run_config.peaks,
                    )

        metrics = data_run_config.pd_arguments.norms
        downsampling_ratios = data_run_config.downsample.downsampling_ratios
        number_of_peaks = count_number_of_peaks(
            recording_session.recordings,
            metrics=metrics,
            downsampling_ratios=downsampling_ratios)

        reference = number_of_peaks[:, :, 0]

        # reference = reference.reshape(list(reference.shape).append(1))
        # ic(reference.shape)
        referees = number_of_peaks.copy()
        referees = np.moveaxis(referees, (0, 1, 2), (1, 2, 0))
        peak_number_ratio = referees/reference
        # ic(peak_number_ratio.shape)
        peak_number_ratio = np.moveaxis(
            peak_number_ratio, (0, 1, 2), (2, 1, 0))
        # ic(peak_number_ratio.shape)

        frequency_table = [recording['RawUltrasound'].sampling_rate
                           for recording in recording_session
                           if 'RawUltrasound' in recording]
        frequency = np.average(frequency_table)
        frequencies = [f"{frequency/(i+1):.0f}" for i in range(7)]
        with PdfPages('figures/peak_number_ratios2.pdf') as pdf:
            publish_distribution_data(
                peak_number_ratio,
                plot_categories=metrics,
                within_plot_categories=frequencies,
                pdf=pdf,
                common_ylabel="Ratio of detected peaks",
                common_xlabel="Data sampling frequency (Hz)",
            )

        with PdfPages('figures/peak_numbers2.pdf') as pdf:
            number_of_peaks = np.moveaxis(
                number_of_peaks, (0, 1, 2), (1, 0, 2))
            # ic(number_of_peaks.shape)
            publish_distribution_data(
                number_of_peaks,
                plot_categories=metrics,
                within_plot_categories=frequencies,
                pdf=pdf,
                common_ylabel="Number of peaks",
                common_xlabel="Data sampling frequency (Hz)",
            )

        with PdfPages('figures/peak_distances2.pdf') as pdf:
            publish_distribution_data(
                nearest_neighbours_in_downsampling(
                    recording_session.recordings,
                    metrics=metrics,
                    downsampling_ratios=downsampling_ratios,),
                plot_categories=metrics,
                within_plot_categories=frequencies,
                pdf=pdf,
                legend_loc="upper left",
                common_ylabel="Mean absolute error of peak position",
                common_xlabel="Data sampling frequency (Hz)",
                horizontal_line=.075)

        with PdfPages('figures/peak_prominences2.pdf') as pdf:
            publish_distribution_data(
                prominences_in_downsampling(
                    recording_session.recordings,
                    metrics=metrics,
                    downsampling_ratios=downsampling_ratios,),
                plot_categories=metrics,
                within_plot_categories=frequencies,
                pdf=pdf,
                legend_loc="upper left",
                common_ylabel="Mean peak prominence",
                common_xlabel="Data sampling frequency (Hz)",
            )

        with PdfPages('figures/seaborn_test.pdf') as pdf:
            dataframe = annotations_to_dataframe(
                recording_session.recordings,
                modality_name="RawUltrasound",
                metrics=metrics,
                downsampling_ratios=downsampling_ratios,)
            publish_distribution_data_seaborn(
                dataframe,
                'prominence',
                plot_categories='metric',
                within_plot_categories='downsampling_ratio',
                pdf=pdf,
                category_titles=frequencies,
                common_ylabel="Mean peak prominence",
                common_xlabel="Data sampling frequency (Hz)",
            )
    logger.info('Data run ended.')

    # save before plotting just in case.
    if cli.args.output_filename:
        save_data(Path(cli.args.output_filename), recording_session)

    # Plot the data into files if asked to.
    if cli.args.publish:
        publish_session_pdf(
            recording_session=recording_session,
            timeseries_params=configuration.publish_config.timeseries_plot)

    log_elapsed_time()

    if cli.args.annotator:
        # Get the GUI running.
        app = QtWidgets.QApplication(sys.argv)
        # Apparently the assignment to an unused variable is needed
        # to avoid a segfault.
        app.annotator = PdQtAnnotator(
            recording_session=recording_session,
            args=cli.args,
            config=configuration)
        sys.exit(app.exec_())


if __name__ == '__main__':
    main()
