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
import logging
from pathlib import Path
from typing import Optional

from satkit.audio_processing import MainsFilter
from satkit.configuration import (
    config_dict, data_run_params, PathStructure, SessionConfig)
from satkit.constants import (
    Datasource, SourceSuffix, SatkitSuffix, SatkitConfigFile)
from satkit.data_import import (
    generate_aaa_recording_list, load_session_config)
from satkit.data_structures import RecordingSession
from satkit.save_and_load import load_recording_session

logger = logging.getLogger('satkit.scripting')

# TODO: change the name of this file to data_importer and move it to a more
# appropriete submodule.


def load_data(
        path: Path, exclusion_file: Optional[Path] = None) -> RecordingSession:
    """
    Handle loading data from individual files or a previously saved session.

    Parameters
    ----------
    path : Path
        Directory or SATKIT metafile to read the RecordingSession from.
    exclusion_file : Optional[Path], optional
        Path to an optional exclusion list, by default None

    Returns
    -------
    RecordingSession
        The generated RecordingSession object with the exclusion list applied.
    """
    # TODO: this seems like a potentially problematic way of setting the
    # exclusion file without any verification.
    if exclusion_file:
        data_run_params['data properties']['exclusion list'] = exclusion_file

    if config_dict['mains frequency']:
        MainsFilter.generate_mains_filter(
            44100,
            config_dict['mains frequency'])
    else:
        MainsFilter.generate_mains_filter(44100, 50)

    if not path.exists():
        logger.critical(
            'File or directory does not exist: %s.', path)
        logger.critical('Exiting.')
        quit()
    elif path.is_dir():
        session = read_recording_session_from_dir(path)
    elif path.suffix == '.satkit_meta':
        session = load_recording_session(path)
    else:
        logger.error(
            'Unsupported filetype: %s.', path)

    return session


def read_recording_session_from_dir(
        path: Path) -> RecordingSession:
    """
    Wrapper for reading data from a directory full of files.

    Having this as a separate method allows subclasses to change
    arguments or even the parser.

    Note that to make data loading work in a consistent way,
    this method just returns the data and saving it in an
    instance variable is left for the caller to handle.
    """
    containing_dir = path.parts[-1]

    session_import_config = path / SatkitConfigFile.SESSION
    session_meta_path = path / (containing_dir + '.RecordingSession' +
                                SatkitSuffix.META)
    if session_meta_path.is_file():
        return load_recording_session(directory=path)

    if session_import_config.is_file():
        session_config = load_session_config(session_import_config)

        if session_config.data_source == Datasource.AAA:
            recordings = generate_aaa_recording_list(path, session_config)

            return RecordingSession(
                name=containing_dir, config=session_config,
                recordings=recordings)

        if session_config.data_source == Datasource.RASL:
            raise NotImplementedError(
                "Loading RASL data hasn't been impmelented yet.")

    if list(path.glob('*' + SourceSuffix.AAA_ULTRA)):
        recordings = generate_aaa_recording_list(path)

        paths = PathStructure(data_path=path)
        session_config = SessionConfig(data_source=Datasource.AAA, paths=paths)
        return RecordingSession(
            name=containing_dir, config=session_config,
            recordings=recordings)

    logger.error(
        'Could not find a suitable importer: %s.', path)
