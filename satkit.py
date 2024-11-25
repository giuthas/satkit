#!/usr/bin/env python3
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
Current main script for running SATKIT.

DEPRECATION WARNING:
This file will be removed when the main method of running SATKIT will move to a
proper access point.
"""

# built-in modules
import sys
from pathlib import Path

# For running a Qt GUI
from PyQt5 import QtWidgets

# local modules
from satkit import log_elapsed_time, set_logging_level
from satkit.annotations import (
    add_peaks  # , count_number_of_peaks, nearest_neighbours_in_downsampling,
    # prominences_in_downsampling
)
import satkit.configuration as config

from satkit.configuration import (
    apply_exclusion_list, DataRunConfig, load_exclusion_list
)
from satkit.data_structures import Session
from satkit.export import (
    publish_distance_matrix,
    publish_aggregate_images
)
from satkit.metrics import (
    add_aggregate_images, add_distance_matrices, add_pd, add_spline_metric,
    downsample_metrics
)
from satkit.modalities import RawUltrasound, Splines
from satkit.qt_annotator import PdQtAnnotator
from satkit.scripting_interface import (
    # Operation,
    SatkitArgumentParser,
    load_data,  # multi_process_data,
    process_modalities, process_statistics_in_recordings,
    save_data
)


def downsample(
        recording_session: Session,
        data_run_config: DataRunConfig
) -> None:
    """
    Downsample metrics in the session.

    Parameters
    ----------
    recording_session : Session
        _description_
    data_run_config : DataRunConfig
        _description_
    """
    for recording in recording_session:
        downsample_metrics(recording, data_run_config.downsample)


def data_run(
        recording_session: Session,
        configuration: config.Configuration,
) -> None:
    data_run_config = configuration.data_run_config

    modality_operation_dict = {}
    if data_run_config.pd_arguments:
        pd_arguments = data_run_config.pd_arguments
        modality_operation_dict["PD"] = (
            add_pd,
            [RawUltrasound],
            pd_arguments.model_dump()
        )

    if data_run_config.aggregate_image_arguments:
        aggregate_image_arguments = data_run_config.aggregate_image_arguments
        modality_operation_dict["AggregateImage"] = (
            add_aggregate_images,
            [RawUltrasound],
            aggregate_image_arguments.model_dump()
        )

    if data_run_config.spline_metric_arguments:
        spline_metric_args = data_run_config.spline_metric_arguments
        modality_operation_dict["SplineMetric"] = (
            add_spline_metric,
            [Splines],
            spline_metric_args.model_dump()
        )

    process_modalities(recordings=recording_session,
                       processing_functions=modality_operation_dict)

    statistic_operation_dict = {}
    if data_run_config.distance_matrix_arguments:
        distance_matrix_arguments = data_run_config.distance_matrix_arguments
        statistic_operation_dict["DistanceMatrix"] = (
            add_distance_matrices,
            ["AggregateImage mean on RawUltrasound"],
            distance_matrix_arguments.model_dump()
        )

    process_statistics_in_recordings(
        session=recording_session,
        processing_functions=statistic_operation_dict)

    if data_run_config.downsample:
        downsample(recording_session=recording_session,
                   data_run_config=data_run_config)

    if data_run_config.peaks:
        modality_pattern = data_run_config.peaks.modality_pattern
        for recording in recording_session:
            if recording.excluded:
                print(
                    f"in satkit.py: jumping over {recording.basename}")
                continue
            for modality_name in recording:
                # TODO make this deal with both strings and regexps as the
                # modality pattern
                if modality_pattern.match(modality_name):
                    add_peaks(
                        recording[modality_name],
                        configuration.data_run_config.peaks,
                    )


def main():
    """Main to run the CLI and start the GUI."""

    # Arguments need to be parsed before setting up logging so that we have
    # access to the verbosity argument.
    cli = SatkitArgumentParser("SATKIT")

    logger = set_logging_level(cli.args.verbose)

    # TODO: this should be done in one:
    if cli.args.configuration_filename:
        config.parse_config(cli.args.configuration_filename)
    else:
        config.parse_config()
    configuration = config.Configuration(cli.args.configuration_filename)

    exclusion_list = None
    if cli.args.exclusion_filename:
        exclusion_list = load_exclusion_list(cli.args.exclusion_filename)
    recording_session = load_data(Path(cli.args.load_path))
    apply_exclusion_list(recording_session, exclusion_list=exclusion_list)

    log_elapsed_time()

    data_run(recording_session=recording_session,
             configuration=configuration)

    if configuration.publish_config is not None:
        publish_aggregate_images(
            session=recording_session,
            image_name='AggregateImage mean on RawUltrasound')
        publish_distance_matrix(
            session=recording_session,
            distance_matrix_name=(
                'DistanceMatrix mean_squared_error on AggregateImage mean '
                'on RawUltrasound')
        )

    logger.info('Data run ended.')

    # save before plotting just in case.
    if cli.args.output_filename:
        save_data(Path(cli.args.output_filename), recording_session)

    log_elapsed_time()

    if cli.args.annotator:
        # Get the GUI running.
        app = QtWidgets.QApplication(sys.argv)
        # Apparently the assignment to an unused variable is needed
        # to avoid a segfault.
        app.annotator = PdQtAnnotator(
            recording_session=recording_session,
            args=cli.args,
            gui_config=configuration.gui_config)
        sys.exit(app.exec_())


if __name__ == '__main__':
    main()
