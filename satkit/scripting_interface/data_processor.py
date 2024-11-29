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
Process data: Add metrics and statistics.

This is the mechanism for avoiding reading and re-reading raw data like
ultrasound or video data that should only be read once, processed in as many
ways as needed, and then expunged from memory to avoid running out of memory.
"""

import datetime
import logging
from dataclasses import dataclass
from multiprocessing import Pool
from typing import Callable

from satkit.data_structures import Modality, Recording, Session

_logger = logging.getLogger('satkit.scripting')


@dataclass
class Operation:
    """
    An operation to be applied to a Modality with given arguments.
    """
    processing_function: Callable
    modality: Modality
    arguments: dict


def process_modalities(
        recordings: list[Recording] | Session,
        processing_functions: dict) -> None:
    """
    Apply processing functions to Modalities.

    Arguments: 
    recordings is a list of Recordings to be processed. The results of applying
        the functions get added to the Recordings as new Modalities and
        Statistics.
    processing_functions is a dictionary containing three keys:1
        'function' is a callable used to process a Recording,
        'modality' is the Modality passed to the function, and 
        'arguments' is a dict of arguments for the function.
    """

    # calculate the metrics
    for recording in recordings:
        if recording.excluded:
            continue

        for key in processing_functions:
            (function, modalities, arguments) = processing_functions[key]
            # TODO: Version 1.0: add a mechanism to change the arguments for
            # different modalities.
            for modality in modalities:
                function(
                    recording,
                    modality,
                    **arguments)

    _logger.info('Modalities processed at %s.', str(datetime.datetime.now()))


def process_statistics_in_recordings(
        session: Session,
        processing_functions: dict) -> None:
    """
    Apply processing functions to Statistics.

    Arguments:
    recordings is a list of Recordings to be processed. The results of applying
        the functions get added to the Recordings as new Statistics.
    processing_functions is a dictionary containing three keys:
        'function' is a callable used to process a Recording,
        'statistic' is the Statistic passed to the function, and
        'arguments' is a dict of arguments for the function.
    """

    for key in processing_functions:
        (function, statistics, arguments) = processing_functions[key]
        # TODO: Version 1.0: add a mechanism to change the arguments for
        # different modalities.
        for statistic in statistics:
            function(
                session,
                statistic,
                **arguments)

    _logger.info('Modalities processed at %s.', str(datetime.datetime.now()))


def multi_process_data(
        recordings: list[Recording],
        operation: Operation) -> None:

    arguments = [
        {'recording': recording,
         'modality': operation.modality,
         **operation.arguments} for recording in recordings]

    _logger.info('Starting data run at %s.', str(datetime.datetime.now()))
    with Pool() as pool:
        pool.map(operation.processing_function, arguments)

    _logger.info('Data run ended at %s.', str(datetime.datetime.now()))
