#
# Copyright (c) 2019-2023
# Pertti Palo, Scott Moisik, Matthew Faytak, and Motoki Saito.
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
from typing import Optional, TextIO, Union

import numpy as np
import nestedtext
from icecream import ic

from satkit.constants import SatkitSuffix
from satkit.data_import import modality_adders
from satkit.data_import.AAA_splines import add_splines
from satkit.data_structures import ModalityData, Recording, RecordingSession
from satkit.metrics import metrics

from .save_and_load_helpers import (
    ModalityListingLoadschema, ModalityLoadSchema, RecordingLoadSchema,
    RecordingSessionLoadSchema)

_recording_loader_logger = logging.getLogger('satkit.recording_loader')


def load_derived_modality(
        recording: Recording,
        path: Path,
        modality_schema: ModalityListingLoadschema) -> None:
    """
    Load a saved derived Modality meta and data and add them to the Recording. 

    Parameters
    ----------
    path : Path
        This is the path to the save files.
    modality_schema : ModalityListingLoadschema
        This contains the name of the meta and data files.
    """
    if not modality_schema.meta_name:
        _recording_loader_logger.info(
            "Looks like %s doesn't have a metafile for one of the Modalities.",
            modality_schema.data_name)
        _recording_loader_logger.info(
            "Assuming the Modality to be batch loaded, so skipping.")
        return
    meta_path = path/modality_schema.meta_name
    data_path = path/modality_schema.data_name

    raw_input = nestedtext.load(meta_path)
    meta = ModalityLoadSchema.model_validate(raw_input)

    saved_data = np.load(data_path)

    modality_data = ModalityData(
        saved_data['data'], sampling_rate=saved_data['sampling_rate'],
        timevector=saved_data['timevector'])

    metric, paremeter_schema = metrics[meta.object_type]
    for key in meta.parameters:
        if meta.parameters[key] == 'None':
            meta.parameters[key] = None
    parameters = paremeter_schema(**meta.parameters)
    modality = metric(recording=recording,
                      parsed_data=modality_data, parameters=parameters)

    recording.add_modality(modality=modality)


def read_recording_meta(
        filepath: Union[str, Path, TextIO]) -> RecordingLoadSchema:
    """
    Read a Recording's saved metadata, validate it, and return it.

    Parameters
    ----------
    filepath : Union[str, Path, TextIO]
        This is passed to nestedtext.load.

    Returns
    -------
    RecordingLoadSchema
        The validated metadata.
    """
    raw_input = nestedtext.load(filepath)
    meta = RecordingLoadSchema.model_validate(raw_input)
    return meta


def load_recording(filepath: Path) -> Recording:
    """
    Load a recording from given Path.

    Parameters
    ----------
    filepath : Path
        Path to Recording's saved metadata.

    Returns
    -------
    Recording
        A Recording object with most of it's modalities loaded. Modalities like
        Splines that maybe stored in one file for several recordings aren't yet
        loaded at this point.

    Raises
    ------
    NotImplementedError
        If there is no previously saved metadata for the recording. This maybe
        handled by a future version of SATKIT, if it should prove necessary.
    """
    # decide which loader we will be using based on either filepath.satkit_meta
    # or config[''] in that order and document this behaviour. this way if the
    # data has previosly been loaded satkit can decide itself what to do with
    # it and there is an easy place where to add processing
    # session/participant/whatever specific config. could also add guessing
    # based on what is present as the final fall back or as the option tried if
    # no meta and config has the wrong guess.

    metapath = filepath.with_suffix(SatkitSuffix.META)
    if metapath.is_file():
        # this is a list of Modalities, each with a data path and meta path
        meta = read_recording_meta(filepath)
    else:
        # TODO: need to hand to the right kind of importer here.
        raise NotImplementedError(
            "Can't yet jump to a previously unloaded recording here.")

    recording = Recording(meta.parameters)

    for modality in meta.modalities:
        if modality in modality_adders:
            adder = modality_adders[modality]
            path = meta.parameters.path/meta.modalities[modality].data_name
            adder(recording, path=path)
        else:
            load_derived_modality(
                recording,
                path=meta.parameters.path,
                modality_schema=meta.modalities[modality])

    return recording


def load_recordings(directory: Path, recording_metafiles: Optional
                    [list[str]]) -> list[Recording]:
    """
    Load (specified) Recordings from directory.

    Parameters
    ----------
    directory : Path
        Path to the directory.
    recording_metafiles : Optional[list[str]]
        Names of the Recording metafiles. If omitted, all Recordings in the
        directory will be loaded.

    Returns
    -------
    list[Recording]
        List of the loaded Recordings.
    """
    if not recording_metafiles:
        recording_metafiles = directory.glob(
            "*.Recording"+str(SatkitSuffix.META))

    recordings = [load_recording(directory / name)
                  for name in recording_metafiles]

    add_splines(recordings, directory)

    return recordings


def load_recording_session(directory: Union[Path, str]) -> RecordingSession:
    """
    Load a recording session from a directory.

    Parameters
    ----------
    directory: Path
        The directory path.

    Returns
    -------
    Session
        The loaded RecordingSession object.
    """
    if isinstance(directory, str):
        directory = Path(directory)

    filename = f"{directory.parts[-1]}{'.RecordingSession'}{SatkitSuffix.META}"
    filepath = directory/filename

    raw_input = nestedtext.load(filepath)
    meta = RecordingSessionLoadSchema.model_validate(raw_input)

    recordings = load_recordings(directory, meta.recordings)

    session = RecordingSession(
        name=meta.name, path=meta.parameters.path,
        datasource=meta.parameters.datasource, recordings=recordings)

    return session
