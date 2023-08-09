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
import logging
from typing import List

import nestedtext
import numpy as np
from satkit.constants import Suffix
from satkit.data_structures import Session

from save_and_load.recording_save import save_recordings

_session_saver_logger = logging.getLogger('satkit.session_saver')

def save_recording_session_meta(session: Session, meta: dict) -> str:
    """
    Save recording session metadata.

    The meta dict should contain at least a list of the recordings in this
    session and their saving locations.
    """
    _session_saver_logger.debug("Saving meta for session %s."%session.basename)
    filename = f"{session.basename}{'.Recording'}{Suffix.META}"
    filepath = session.path/filename

    meta['object type'] = "Session"
    meta['name'] = session.name
    meta['path'] = str(session.path)

    nestedtext.dump(meta, filepath)
    _session_saver_logger.debug("Wrote file %s."%(filename))

    return filename

def save_recording_session(session: Session):
    """
    Save a recording session.
    """
    _session_saver_logger.debug("Saving recording session %s."%session.basename)
    recording_meta_files = save_recordings(session.recordings)
    save_recording_session_meta(session, recording_meta_files)
