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
from pathlib import Path
from pprint import pprint
from typing import List

import nestedtext
import numpy as np
from pydantic import BaseModel
from satkit.configuration import config
from satkit.constants import Suffix
from satkit.data_import import add_audio, add_video, add_aaa_raw_ultrasound, generate_ultrasound_recording
from satkit.data_structures import Modality, Recording

_recording_loader_logger = logging.getLogger('satkit.recording_loader')

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
    # or config[''] in that order and document this behaviour. this way if the
    # data has previosly been loaded satkit can decide itself what to do with it
    # and there is an easy place where to add processing
    # session/participant/whatever specific config. could also add guessing
    # based on what is present as the final fall back or as the option tried if
    # no meta and config has the wrong guess.

    metapath = filepath.with_suffix(Suffix.META)
    if metapath.is_file():
        meta = read_recording_meta(filepath)
    else:
        # TODO: need to hand to the right kind of importer here.
        raise NotImplementedError("Can't yet jump to a previously unloaded recording here.")
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
        