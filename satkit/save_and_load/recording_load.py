import logging
from pathlib import Path
from pprint import pprint
from typing import List

import nestedtext
import numpy as np
from pydantic import BaseModel, EmailStr
from satkit.constants import Suffix
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
    meta = read_recording_meta(filepath)

def load_recordings(directory: Path) -> List[Recording]:
    """
    Load Recordings from directory.
    """
    recording_metafiles = directory.glob("*.Recording"+str(Suffix.META))

    recordings = [load_recording(file) for file in recording_metafiles]
        