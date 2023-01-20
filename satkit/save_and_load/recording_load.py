import logging
from pathlib import Path
from pprint import pprint
from typing import List

import nestedtext
import numpy as np
from pydantic import BaseModel
from satkit.configuration import config
from satkit.constants import Suffix
from satkit.data_import import generate_ultrasound_recording
from satkit.data_import.add_AAA_raw_ultrasound import add_aaa_raw_ultrasound
from satkit.data_import.add_audio import add_audio
from satkit.data_import.add_video import add_video
from satkit.data_structures import Modality, Recording

_recording_loader_logger = logging.getLogger('satkit.modality_saver')

class ModalityPaths(BaseModel):
    data_path: str
    meta_path: str

class RecordingMeta(BaseModel):
    modalities: List[ModalityPaths]

def read_recording_meta(filepath) -> dict:
    raw_input = nestedtext.load(filepath)
    meta = RecordingMeta.parse_obj(raw_input)
    return meta

def load_recording(filepath: Path) -> Recording:

    # decide which loader we will be using based on either filepath.satkit_meta
    # or config[''] in that order an document this behaviour. this way if the
    # data has previosly been loaded satkit can decide itself what to do with it
    # and there is an easy place where to add processing
    # session/participant/whatever specific config. could also add guessing
    # based on what is present as the final fall back or as the option tried if
    # no meta and config has the wrong guess.

    meta = read_recording_meta(filepath)
    recording = generate_ultrasound_recording(meta['basename'], Path(meta['path']))
    add_audio(recording, meta['wav_preload'])
    add_aaa_raw_ultrasound(recording, meta['ult_preload'])
    add_video(recording, meta['video_preload'])
    
    

def load_recordings(directory: Path) -> List[Recording]:
    """
    Load Recordings from directory.
    """
    recording_metafiles = directory.glob("*.Recording"+str(Suffix.META))

    recordings = [load_recording(file) for file in recording_metafiles]
    return recordings
        