#
# Copyright (c) 2019-2023 Pertti Palo, Scott Moisik, Matthew Faytak, and Motoki Saito.
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
from collections import OrderedDict
import logging
from typing import List

import nestedtext
import numpy as np
from satkit.constants import Suffix, SATKIT_FILE_VERSION
from satkit.data_structures import RecordingSession

from save_and_load.recording_save import save_recordings
from .save_and_load_helpers import nested_text_converters

_session_saver_logger = logging.getLogger('satkit.session_saver')


def save_recording_session_meta(
        session: RecordingSession, recording_meta_files: list) -> str:
    """
    Save recording session metadata.

    The meta dict should contain at least a list of the recordings in this
    session and their saving locations.
    """
    _session_saver_logger.debug(
        "Saving meta for session %s." % session.basename)
    filename = f"{session.basename}{'.Session'}{Suffix.META}"
    filepath = session.path/filename

    meta = OrderedDict()
    meta['object type'] = type(session)
    meta['name'] = session.name
    meta['format version'] = SATKIT_FILE_VERSION

    parameters = OrderedDict()
    parameters['path'] = str(session.path)
    parameters['data source'] = str(session.datasource)

    meta['parameters'] = parameters
    meta['recordings'] = recording_meta_files

    try:
        nestedtext.dump(meta, filepath, converters=nested_text_converters)
        _session_saver_logger.debug("Wrote file %s." % (filename))
    except OSError as e:
        _session_saver_logger.critical(e)

    return filename


def save_recording_session(session: RecordingSession):
    """
    Save a recording session.
    """
    _session_saver_logger.debug(
        "Saving recording session %s." % session.basename)
    recording_meta_files = save_recordings(session.recordings)
    save_recording_session_meta(session, recording_meta_files)
