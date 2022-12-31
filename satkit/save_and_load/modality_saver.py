import logging
from typing import List

import nestedtext
from satkit.data_structures import Modality, Recording

_modality_saver_logger = logging.getLogger('satkit.modality_saver')

def save_modality_data(modality: Modality) -> str:
    """
    Save the data of a Modality.

    This saves only ModalityData.data and ModalityData.timevector.
    """
    _modality_saver_logger.debug("Saving data for %s."%modality.name)
    suffix = modality.name.replace(" ", "_")
    filename = f"{modality.recording.basename}.{suffix}"
    _modality_saver_logger.debug("Wrote file %s."%(filename))

    return filename

def save_modality_meta(modality: Modality) -> str:
    """
    Save meta data and annotations for a Modality.

    Saved data includes sampling frequency and any processing metadata that is
    needed to reconstruct the Modality. 
    """
    _modality_saver_logger.debug("Saving meta for %s."%modality.name)
    suffix = modality.name.replace(" ", "_")
    filename = f"{modality.recording.basename}.{suffix}"
    filename += "meta"
    _modality_saver_logger.debug("Wrote file %s."%(filename))

    return filename
    

def save_recording_meta(recording: Recording, meta: dict) -> str:
    """
    Save Recording meta.

    The meta dict should contain at least a list of the modalities this recording
    has and their saving locations.
    """
    _modality_saver_logger.debug("Saving meta for recording %s."%recording.basename)
    filename = f"{recording.basename}.satkit_meta"
    filepath = recording.path/filename
    try:
        nestedtext.dump(meta, filepath)
    except nestedtext.NestedTextError as error:
        error.terminate()
    _modality_saver_logger.debug("Wrote file %s."%(filename))

    return filename

def save_derived_modalities(recording: Recording):
    """
    Save derived data modalities for a single Recording.
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
            modality_meta['meta'] = {
                'sampling_rate': modality.sampling_rate
                }
            if hasattr(modality, 'meta'):
                modality_meta['meta'].update(modality.meta)
                modality_meta['meta']['meta_file'] = str(modality_meta['meta']['meta_file']) 
                modality_meta['meta_path'] = str(modality_meta['meta']['meta_file'])   
        recording_meta[modality_name] = modality_meta
    save_recording_meta(recording, recording_meta)

def save_derived_data(recordings: List[Recording], save_excluded: bool=True):
    """
    Save derived data modalities for each Recording.
    """
    for recording in recordings:
        if save_excluded or not recording.excluded:
            save_derived_modalities(recording)
