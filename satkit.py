#!/usr/bin/env python3
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

# built-in modules
import sys
from pathlib import Path

# from icecream import ic
# For running a Qt GUI
from PyQt5 import QtWidgets

# local modules
from satkit import log_elapsed_time, set_logging_level
from satkit.annotations import find_gesture_peaks
from satkit.configuration import configuration

from satkit.metrics import add_pd, add_spline_metric
from satkit.modalities import RawUltrasound, Splines
from satkit.plot_and_publish import publish_pdf
from satkit.qt_annotator import PdQtAnnotator
from satkit.scripting_interface import (Operation, SatkitArgumentParser,
                                        load_data, multi_process_data,
                                        process_data, save_data)


def main():
    """Simple main to run the CLI back end and start the QT front end."""

    # Arguments need to be parsed before setting up logging so that we have
    # access to the verbosity argument.
    cli = SatkitArgumentParser("SATKIT")

    logger = set_logging_level(cli.args.verbose)
    if cli.args.configuration_filename:
        configuration.load_config(cli.args.configuration_filename)
    else:
        configuration.load_config()

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
    pd_arguments = configuration.data_run_params['pd_arguments']

    # TODO: turn these commented out bits into an example script of how to do
    # things programmatically.
    # spline_config = recording_session.config.spline_config
    # spline_metric_arguments = {
    #     'metrics': ['annd', 'mpbpd', 'modified_curvature', 'fourier'],
    #     'timesteps': [3],
    #     'exclude_points': spline_config.data_config.ignore_points,
    #     'release_data_memory': False,
    #     'preload': True}

    function_dict = {
        'PD': (add_pd,
               [RawUltrasound],
               pd_arguments)  # ,

        # 'SplineMetric': (add_spline_metric,
        #                  [Splines],
        #                  spline_metric_arguments)  # ,
    }
    process_data(recordings=recording_session.recordings,
                 processing_functions=function_dict)

    # if 'peaks' in configuration.data_run_params:
    #     peaks, properties = find_gesture_peaks(
    #         data, configuration.data_run_params['peaks'])
    # else:
    #     peaks, properties = find_gesture_peaks(data)

    # operation = Operation(processing_function=pd.add_pd,
    #                       modality=RawUltrasound,
    #                       arguments={'mask_images': True,
    #                                  'pd_on_interpolated_data': True,
    #                                  'release_data_memory': True,
    #                                  'preload': True})
    # multi_process_data(recordings, operation)

    logger.info('Data run ended.')

    # save before plotting just in case.
    if cli.args.output_filename:
        save_data(Path(cli.args.output_filename), recording_session)

    # Plot the data into files if asked to.
    if cli.args.publish:
        publish_pdf(recording_session)

    log_elapsed_time()

    if cli.args.annotator:
        # Get the GUI running.
        app = QtWidgets.QApplication(sys.argv)
        # Apparently the assignment to an unused variable is needed
        # to avoid a segfault.
        app.annotator = PdQtAnnotator(recording_session, cli.args)
        sys.exit(app.exec_())


if __name__ == '__main__':
    main()
