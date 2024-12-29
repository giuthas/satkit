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

import logging
import time
from typing import Optional

start_time = time.time()
last_log_time = time.time()


# Do not do anything like this as any logging done here needs to be done with
# passed arguments instead. Otherwise, there will be trouble with circular
# imports as this module will get imported before logging is actually properly
# setup.
# _satkit_logger = logging.getLogger('satkit')


def set_logging_level(verbosity: Optional[int]):
    """
    Set up logging with the logging module.

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
        logging.critical(
            "Negative argument %s to verbose!",
            str(verbosity))
    logger.addHandler(console_handler)

    logger.info('Data run started.')

    return logger


def log_elapsed_time(logger: logging.Logger):
    """
    Log the time elapsed since logging began.
    
    Also logs the time since the last call to this function.
    """
    global start_time, last_log_time
    current_time = time.time()
    elapsed_time = current_time - start_time
    since_last_log = current_time - last_log_time
    log_text = 'Elapsed time from start: %f, from last logged time: %f' % (
        elapsed_time, since_last_log)
    logger.info(log_text)
    last_log_time = current_time
