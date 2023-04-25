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
