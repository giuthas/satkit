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
import satkit.configuration as config
from satkit.configuration import (
    apply_exclusion_list, load_exclusion_list
)

from satkit.qt_annotator import PdQtAnnotator
from satkit.argument_parser import SatkitArgumentParser
from satkit.data_loader import load_data
from satkit.data_processor import (
    add_derived_data,
)


def initialise_satkit():
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
    session = load_data(Path(cli.args.load_path))
    apply_exclusion_list(session, exclusion_list=exclusion_list)
    return cli, configuration, logger, session


def main():
    """Main to run the CLI and start the GUI."""

    cli, configuration, logger, session = initialise_satkit()
    log_elapsed_time()

    add_derived_data(session=session,
                     configuration=configuration)

    if configuration.publish_config is not None:
        # TODO 1.0: This should probably be its own CLI command.
        logger.info(
            "Currently publishing from the satkit.py script is disabled.")

    logger.info('Data run ended.')

    # save before plotting just in case.
    if cli.args.output_filename:
        logger.critical(
            "Old style data saving is no longer supported. "
            "Use 'Save all' in the GUI or implement a better way :^)")

    log_elapsed_time()

    if cli.args.annotator:
        # Get the GUI running.
        app = QtWidgets.QApplication(sys.argv)
        # Apparently the assignment to an unused variable is needed
        # to avoid a segfault.
        app.annotator = PdQtAnnotator(
            recording_session=session,
            args=cli.args,
            gui_config=configuration.gui_config)
        sys.exit(app.exec_())


if __name__ == '__main__':
    main()
