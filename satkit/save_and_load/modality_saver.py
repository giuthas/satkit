import logging
from typing import List

from satkit.data_structures import Modality, Recording

_modality_saver_logger = logging.getLogger('satkit.modality_saver')

def save_modality_data(modality: Modality):
    """
    Save the data of a Modality.

    This saves only ModalityData.data and ModalityData.timevector.
    """
    _modality_saver_logger.debug("Saving data for %s."%modality.name)

def save_modality_meta(modality: Modality):
    """
    Save meta data and annotations for a Modality.

    Saved data includes sampling frequency and any processing metadata that is
    needed to reconstruct the Modality. 
    """
    _modality_saver_logger.debug("Saving meta for %s."%modality.name)
    

def save_recording_meta(recording: Recording, meta: dict):
    """
    Save Recording meta.

    The meta dict should contain at least a list of the modalities this recording
    has and their saving locations.
    """
    _modality_saver_logger.debug("Saving meta for recording %s."%recording.name)

def save_derived_modalities(recording: Recording):
    """
    Save derived data modalities for a single Recording.
    """
    for modality in recording.modalities:
        if recording.modalities[modality].is_derived_modality:
            save_modality_data(recording.modalities[modality])
            save_modality_meta(recording.modalities[modality])

def save_derived_data(recordings: List[Recording], save_excluded: bool=True):
    """
    Save derived data modalities for each Recording.
    """
    for recording in recordings:
        if save_excluded or not recording.excluded:
            save_derived_modalities(recording)
