#!/usr/bin/env python3
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

# built-in modules
import logging
import sys
from pathlib import Path
from typing import Optional

# For running a Qt GUI
from PyQt5 import QtWidgets

# local modules
from satkit import log_elapsed_time, set_logging_level
from satkit.metrics import pd, peaks
from satkit.modalities import RawUltrasound
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

    if cli.args.exclusion_filename:
        recordings = load_data(Path(cli.args.load_path), Path(cli.args.exclusion_filename))
    else:
        recordings = load_data(Path(cli.args.load_path), None)

    log_elapsed_time()

    #function_dict = {'pd':pd.pd, 'annd':annd.annd}
    pd_arguments = {
        # 'norms': ['l0', 'l0.01', 'l0.1', 'l0.5', 'l1', 'l2', 'l4', 'l10', 'l_inf', 'd'],
        'norms': ['l1'],
        'mask_images': True, 
        'pd_on_interpolated_data': False, 
        'release_data_memory': True, 
        'preload': True}

    function_dict = {
        'PD': (pd.add_pd, 
        [RawUltrasound], 
        pd_arguments)#,
        # 'peaks': (peaks.time_series_peaks,
        # [RawUltrasound], # TODO: figure out if this will actually work because this should be 'PD l1 on RawUltrasound' or something like that
        # peak_arguments)
    }
    process_data(recordings=recordings, processing_functions=function_dict)

    # operation = Operation(
    #     processing_function = pd.add_pd, 
    #     modality = RawUltrasound, 
    #     arguments= {'mask_images': True, 'pd_on_interpolated_data': True, 'release_data_memory': True, 'preload': True})
    # multi_process_data(recordings, operation)

    logger.info('Data run ended.')

    # save before plotting just in case.
    if cli.args.output_filename:
        save_data(Path(cli.args.output_filename), recordings)

    # Plot the data into files if asked to.
    if cli.args.plot:
        print("implement plotting to get results")

    log_elapsed_time()

    # Get the GUI running.
    app = QtWidgets.QApplication(sys.argv)
    # Apparently the assigment to an unused variable is needed to avoid a segfault.
    annotator = PdQtAnnotator(recordings, cli.args)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
