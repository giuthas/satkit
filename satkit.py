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

# built-in modules
import sys
from pathlib import Path

# from icecream import ic

# For running a Qt GUI
from PyQt5 import QtWidgets

# local modules
from satkit import log_elapsed_time, set_logging_level
from satkit.annotations import (
    add_peaks  # , count_number_of_peaks, nearest_neighbours_in_downsampling,
    # prominences_in_downsampling
)
import satkit.configuration as config

from satkit.configuration import DataRunConfig
from satkit.data_structures import Session
from satkit.metrics import (add_pd,  add_spline_metric,
                            downsample_metrics)
from satkit.modalities import RawUltrasound, Splines
from satkit.qt_annotator import PdQtAnnotator
from satkit.scripting_interface import (
    # Operation,
    SatkitArgumentParser,
    load_data,  # multi_process_data,
    process_data, save_data)


def downsample(
        recording_session: Session,
        data_run_config: DataRunConfig) -> None:
    for recording in recording_session:
        downsample_metrics(recording, data_run_config.downsample)


def data_run(
        recording_session: Session,
        configuration: config.Configuration,
        exclusion_list: list[str]) -> None:
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

    process_data(recordings=recording_session.recordings,
                 processing_functions=function_dict)

    if data_run_config.downsample:
        downsample(recording_session=recording_session,
                   data_run_config=data_run_config)

    if data_run_config.peaks:
        modality_pattern = data_run_config.peaks.modality_pattern
        for recording in recording_session:
            excluded = [prompt in recording.meta_data.prompt
                        for prompt in exclusion_list]
            if any(excluded):
                print(
                    f"in satkit_publish.py: jumping over {recording.basename}")
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
    """Simple main to run the CLI and start the GUI."""

    # Arguments need to be parsed before setting up logging so that we have
    # access to the verbosity argument.
    cli = SatkitArgumentParser("SATKIT")

    logger = set_logging_level(cli.args.verbose)

    if cli.args.configuration_filename:
        config.parse_config(cli.args.configuration_filename)
    else:
        config.parse_config()
    configuration = config.Configuration(cli.args.configuration_filename)

    # TODO read the actual exclusion list and apply it
    exclusion_list = ("water swallow", "bite plate")

    recording_session = load_data(Path(cli.args.load_path))

    log_elapsed_time()

    data_run(recording_session=recording_session,
             configuration=configuration,
             exclusion_list=exclusion_list)

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
