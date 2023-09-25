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
from metrics.pd import ImageMask

import nestedtext
import numpy as np
from icecream import ic
from satkit.constants import SATKIT_FILE_VERSION, Suffix
from satkit.data_structures import Modality, Recording, RecordingSession
from .save_and_load_helpers import nested_text_converters

_saver_logger = logging.getLogger('satkit._saver')


def save_modality_data(modality: Modality) -> str:
    """
    Save the data of a Modality.

    This saves only ModalityData.data and ModalityData.timevector.

    Returns the filename of the 
    """
    _saver_logger.debug("Saving data for %s." % modality.name)
    suffix = modality.name.replace(" ", "_")
    filename = f"{modality.recording.basename}.{suffix}{Suffix.DATA}"
    filepath = modality.recording.path/filename

    np.savez(
        filepath, data=modality.data, sampling_rate=modality.sampling_rate,
        timevector=modality.timevector)

    _saver_logger.debug("Wrote file %s." % (filename))
    return filename


def save_modality_meta(modality: Modality) -> str:
    """
    Save meta data and annotations for a Modality.

    Saved data includes sampling frequency and any processing metadata that is
    needed to reconstruct the Modality. 
    """
    _saver_logger.debug("Saving meta for %s." % modality.name)
    suffix = modality.name.replace(" ", "_")
    filename = f"{modality.recording.basename}.{suffix}"
    filename += Suffix.META
    filepath = modality.recording.path/filename

    meta = OrderedDict()
    meta['object_type'] = type(modality).__name__
    meta['name'] = modality.name
    meta['format_version'] = SATKIT_FILE_VERSION

    parameters = modality.get_meta().copy()
    meta['parameters'] = parameters

    try:
        nestedtext.dump(meta, filepath, converters=nested_text_converters)
        _saver_logger.debug("Wrote file %s." % (filename))
    # except nestedtext.NestedTextError as e:
    #     e.terminate()
    except OSError as e:
        _saver_logger.critical(e)

    return filename


def save_recording_meta(recording: Recording, modalities_saves: dict) -> str:
    """
    Save Recording meta.

    The meta dict should contain at least a list of the modalities this recording
    has and their saving locations.
    """
    _saver_logger.debug(
        "Saving meta for recording %s." % recording.basename)
    filename = f"{recording.basename}{'.Recording'}{Suffix.META}"
    filepath = recording.path/filename

    meta = OrderedDict()
    meta['object_type'] = type(recording).__name__
    meta['name'] = recording.basename
    meta['format_version'] = SATKIT_FILE_VERSION
    meta['parameters'] = recording.meta_data.dict()
    meta['modalities'] = modalities_saves

    try:
        nestedtext.dump(meta, filepath, converters=nested_text_converters)
        _saver_logger.debug("Wrote file %s." % (filename))
    # except nestedtext.NestedTextError as e:
    #     e.terminate()
    except OSError as e:
        _saver_logger.critical(e)

    return filename


def save_modalities(recording: Recording) -> str:
    """
    Save derived data Modalities for a single Recording.

    Returns a dictionary of the data and meta paths of the Modalities.
    """
    recording_meta = {}
    for modality_name in recording.modalities:
        modality_meta = {}
        modality = recording.modalities[modality_name]
        if modality.is_derived_modality:
            modality_meta['data_name'] = save_modality_data(modality)
            modality_meta['meta_name'] = save_modality_meta(modality)
        else:
            modality_meta['data_name'] = str(modality.data_path.name)
            if modality.meta_path:
                modality_meta['meta_name'] = str(modality.meta_path.name)
            else:
                modality_meta['meta_name'] = None
        recording_meta[modality_name] = modality_meta
    return recording_meta


def save_recordings(
        recordings: list[Recording],
        save_excluded: bool = True) -> list[str]:
    """
    Save derived data modalities for each Recording.
    """
    metafiles = []
    for recording in recordings:
        if save_excluded or not recording.excluded:
            modalities_saves = save_modalities(recording)
            metafile = save_recording_meta(recording, modalities_saves)
            metafiles.append(metafile)

    return metafiles


def save_recording_session_meta(
        session: RecordingSession, recording_meta_files: list) -> str:
    """
    Save recording session metadata.

    The meta dict should contain at least a list of the recordings in this
    session and their saving locations.
    """
    _saver_logger.debug(
        "Saving meta for session %s." % session.name)
    filename = f"{session.name}{'.Session'}{Suffix.META}"
    filepath = session.path/filename

    meta = OrderedDict()
    meta['object_type'] = type(session).__name__
    meta['name'] = session.name
    meta['format_version'] = SATKIT_FILE_VERSION

    parameters = OrderedDict()
    parameters['path'] = str(session.path)
    parameters['datasource'] = session.datasource._value_

    meta['parameters'] = parameters
    meta['recordings'] = recording_meta_files

    try:
        nestedtext.dump(meta, filepath, converters=nested_text_converters)
        _saver_logger.debug("Wrote file %s." % (filename))
    except OSError as e:
        _saver_logger.critical(e)

    return filename


def save_recording_session(session: RecordingSession):
    """
    Save a recording session.
    """
    _saver_logger.debug(
        "Saving recording session %s." % session.name)
    recording_meta_files = save_recordings(session.recordings)
    save_recording_session_meta(session, recording_meta_files)
