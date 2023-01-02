import logging
from typing import List

import nestedtext
import numpy as np
from satkit.constants import Suffix
from satkit.data_structures import Modality, Recording

_recording_saver_logger = logging.getLogger('satkit.modality_saver')

def save_modality_data(modality: Modality) -> str:
    """
    Save the data of a Modality.

    This saves only ModalityData.data and ModalityData.timevector.

    Returns the filename of the 
    """
    _recording_saver_logger.debug("Saving data for %s."%modality.name)
    suffix = modality.name.replace(" ", "_")
    filename = f"{modality.recording.basename}.{suffix}{Suffix.DATA}"
    filepath = modality.recording.path/filename

    np.savez(filepath, data=modality.data, timevector=modality.timevector)

    _recording_saver_logger.debug("Wrote file %s."%(filename))
    return filename

def save_modality_meta(modality: Modality) -> str:
    """
    Save meta data and annotations for a Modality.

    Saved data includes sampling frequency and any processing metadata that is
    needed to reconstruct the Modality. 
    """
    _recording_saver_logger.debug("Saving meta for %s."%modality.name)
    suffix = modality.name.replace(" ", "_")
    filename = f"{modality.recording.basename}.{suffix}"
    filename += Suffix.META
    filepath = modality.recording.path/filename

    nestedtext.dump(modality.get_meta(), filepath)
    _recording_saver_logger.debug("Wrote file %s."%(filename))

    return filename

def save_recording_meta(recording: Recording, meta: dict) -> str:
    """
    Save Recording meta.

    The meta dict should contain at least a list of the modalities this recording
    has and their saving locations.
    """
    _recording_saver_logger.debug("Saving meta for recording %s."%recording.basename)
    filename = f"{recording.basename}{'.Recording'}{Suffix.META}"
    filepath = recording.path/filename

    nestedtext.dump(meta, filepath)
    _recording_saver_logger.debug("Wrote file %s."%(filename))

    return filename

def save_modalities(recording: Recording) -> str:
    """
    Save derived data modalities for a single Recording.

    Returns a dictionary of the data and meta paths of the recordings.
    """
    recording_meta = {}
    for modality_name in recording.modalities:
        modality_meta = {}
        modality = recording.modalities[modality_name]
        if modality.is_derived_modality:
            modality_meta['data_path'] = save_modality_data(modality)
            modality_meta['meta_path'] = save_modality_meta(modality)
        else:
            modality_meta['data_path'] = str(modality.data_path)
            modality_meta['meta_path'] = str(modality.meta_path)
        recording_meta[modality_name] = modality_meta
    return recording_meta

def save_recordings(recordings: List[Recording], save_excluded: bool=True):
    """
    Save derived data modalities for each Recording.
    """
    for recording in recordings:
        if save_excluded or not recording.excluded:
            recording_meta = save_modalities(recording)
            save_recording_meta(recording, recording_meta)
