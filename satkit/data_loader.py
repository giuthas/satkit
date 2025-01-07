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
"""
Import a Session from a directory or call the loader for previously saved data.
"""

import logging
import sys
from pathlib import Path

from satkit.audio_processing import MainsFilter
from satkit.configuration import Configuration, PathStructure
from satkit.constants import (
    Datasource, SourceSuffix, SatkitSuffix, SatkitConfigFile)
from satkit.data_import import (
    generate_aaa_recording_list, load_session_config)
from satkit.data_structures import (
    FileInformation, Session, SessionConfig)
from satkit.save_and_load import load_recording_session

logger = logging.getLogger('satkit.scripting')

# TODO 1.0: change the name of this file to data_importer and move it to a more
# appropriate submodule.


def load_data(path: Path, configuration: Configuration) -> Session:
    """
    Handle loading data from individual files or a previously saved session.

    Parameters
    ----------
    path : Path
        Directory or SATKIT metafile to read the Session from.
    configuration : Configuration
        Satkit configuration.
    Returns
    -------
    Session
        The generated Session object with the exclusion list applied.
    """
    if configuration.main_config.mains_frequency:
        MainsFilter.generate_mains_filter(
            44100,
            configuration.main_config.mains_frequency)
    else:
        MainsFilter.generate_mains_filter(44100, 50)

    if not path.exists():
        logger.critical(
            'File or directory does not exist: %s.', path)
        logger.critical('Exiting.')
        sys.exit()
    elif path.is_dir():
        session = read_recording_session_from_dir(
            recorded_data_path=path,
            detect_beep=configuration.data_run_config.flags.detect_beep
        )
    elif path.suffix == '.satkit_meta':
        session = load_recording_session(path)
    else:
        logger.error(
            'Unsupported filetype: %s.', path)
        sys.exit()

    for recording in session:
        recording.after_modalities_init()

    return session


def read_recording_session_from_dir(
        recorded_data_path: Path,
        detect_beep: bool = False
) -> Session:
    """
    Wrapper for reading data from a directory full of files.

    Having this as a separate method allows subclasses to change
    arguments or even the parser.

    Note that to make data loading work in a consistent way,
    this method just returns the data and saving it in an
    instance variable is left for the caller to handle.
    """
    containing_dir = recorded_data_path.parts[-1]

    session_config_path = recorded_data_path / SatkitConfigFile.SESSION
    session_meta_path = recorded_data_path / (containing_dir + '.Session' +
                                              SatkitSuffix.META)
    if session_meta_path.is_file():
        return load_recording_session(recorded_data_path, session_config_path)

    file_info = FileInformation(
        recorded_path=recorded_data_path,
        recorded_meta_file=session_config_path.name)
    if session_config_path.is_file():
        paths, session_config = load_session_config(
            recorded_data_path, session_config_path)

        if session_config.data_source == Datasource.AAA:
            recordings = generate_aaa_recording_list(
                directory=recorded_data_path,
                import_config=session_config,
                detect_beep=detect_beep
            )

            session = Session(
                name=containing_dir, paths=paths, config=session_config,
                file_info=file_info, recordings=recordings)
            return session

        if session_config.data_source == Datasource.RASL:
            raise NotImplementedError(
                "Loading RASL data hasn't been implemented yet.")

    if list(recorded_data_path.glob('*' + SourceSuffix.AAA_ULTRA)):
        recordings = generate_aaa_recording_list(
            directory=recorded_data_path,
            detect_beep=detect_beep
        )

        paths = PathStructure(root=recorded_data_path)
        session_config = SessionConfig(data_source=Datasource.AAA)

        session = Session(
            name=containing_dir, paths=paths, config=session_config,
            file_info=file_info, recordings=recordings)
        return session

    logger.error(
        'Could not find a suitable importer: %s.', recorded_data_path)
