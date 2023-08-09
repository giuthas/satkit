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
from satkit.data_structures import Modality, Recording

_recording_saver_logger = logging.getLogger('satkit.recording_saver')

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

    meta = modality.get_meta().copy()
    meta['object type'] = "Recording"
    meta['name'] = modality.name

    nestedtext.dump(meta, filepath)
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

    meta['object type'] = "Recording"
    meta['name'] = recording.basename

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


def save_recordings(
    recordings: List[Recording], 
    save_excluded: bool=True) -> List[str]:
    """
    Save derived data modalities for each Recording.
    """
    metafiles = []
    for recording in recordings:
        if save_excluded or not recording.excluded:
            recording_meta = save_modalities(recording)
            metafile = save_recording_meta(recording, recording_meta)
            metafiles.append(metafile)

    return metafiles
