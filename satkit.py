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

# built-in modules
import datetime
import logging
import sys
import time
from pathlib import Path
from typing import Optional

# For running a Qt GUI
from PyQt5 import QtWidgets

# local modules
from satkit.metrics import pd
from satkit.modalities import RawUltrasound
from satkit.qt_annotator import PdQtAnnotator
from satkit.scripting_interface import (Operation, SatkitArgumentParser,
                                        load_data, multi_process_data,
                                        process_data, save_data)


def set_up_logging(verbosity: Optional[int]):
        """Set up logging with the logging module.

        Main thing to do is set the level of printed output based on the
        verbosity argument.
        """
        logger = logging.getLogger('satkit')
        logger.setLevel(logging.DEBUG)

        # also log to the console at a level determined by the --verbose flag
        console_handler = logging.StreamHandler()  # sys.stderr

        # Set the level of logging messages that will be printed to
        # console/stderr.
        if not verbosity:
            console_handler.setLevel('WARNING')
        elif verbosity < 1:
            console_handler.setLevel('ERROR')
        elif verbosity == 1:
            console_handler.setLevel('WARNING')
        elif verbosity == 2:
            console_handler.setLevel('INFO')
        elif verbosity >= 3:
            console_handler.setLevel('DEBUG')
        else:
            logging.critical("Negative argument %s to verbose!",
                str(verbosity))
        logger.addHandler(console_handler)

        logger.info('Data run started at %s.', str(datetime.datetime.now()))
        
        return logger

def main():
    """Simple main to run the CLI back end and start the QT front end."""
    start_time = time.time()

    # Arguments need to be parsed before setting up logging so that we have
    # access to the verbosity argument.
    cli = SatkitArgumentParser("SATKIT")

    logger = set_up_logging(cli.args.verbose)

    if cli.args.exclusion_filename:
        recordings = load_data(Path(cli.args.load_path), Path(cli.args.exclusion_filename))
    else:
        recordings = load_data(Path(cli.args.load_path), None)

    #function_dict = {'pd':pd.pd, 'annd':annd.annd}
    function_dict = {
        'PD': (pd.add_pd, 
        [RawUltrasound], 
        {'mask_images': True, 'pd_on_interpolated_data': False, 'release_data_memory': True, 'preload': True})}
    process_data(recordings=recordings, processing_functions=function_dict)

    # operation = Operation(
    #     processing_function = pd.add_pd, 
    #     modality = RawUltrasound, 
    #     arguments= {'mask_images': True, 'pd_on_interpolated_data': True, 'release_data_memory': True, 'preload': True})
    # multi_process_data(recordings, operation)

    logger.info('Data run ended at %s.', str(datetime.datetime.now()))

    # save before plotting just in case.
    if cli.args.output_filename:
        save_data(Path(cli.args.output_filename), recordings)

    # Plot the data into files if asked to.
    if cli.args.plot:
        print("implement plotting to get results")


    elapsed_time = time.time() - start_time
    log_text = 'Elapsed time ' + str(elapsed_time)
    logger.info(log_text)

    # Get the GUI running.
    app = QtWidgets.QApplication(sys.argv)
    # Apparently the assigment to an unused variable is needed to avoid a segfault.
    annotator = PdQtAnnotator(recordings, cli.args)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
