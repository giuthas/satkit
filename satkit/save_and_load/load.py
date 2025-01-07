#
# Copyright (c) 2019-2025
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
"""
Functions for loading previously saved/seen data.
"""

import logging
from pathlib import Path
from typing import Any, TextIO

import numpy as np
import nestedtext

from satkit.configuration import PathStructure
from satkit.constants import SatkitConfigFile, SatkitSuffix
from satkit.data_import import (
    modality_adders, add_splines, load_session_config
)
from satkit.data_structures import (
    ModalityData, Recording, Session, SessionConfig
)
from satkit.data_structures.metadata_classes import FileInformation
from satkit.metrics import metrics, statistics

from .save_and_load_schemas import (
    DataContainerListingLoadSchema, DataContainerLoadSchema,
    RecordingLoadSchema, SessionLoadSchema
)

_logger = logging.getLogger('satkit.recording_loader')


def _load_data_container_data_and_meta(
    path: Path,
    data_container_schema: DataContainerListingLoadSchema,
) -> tuple[FileInformation, DataContainerLoadSchema, Any]:
    """
    Load file information, meta data, and actual data for a DataContainer.
    
    Only a helper function, not for general use.
    """
    file_info = FileInformation(
        satkit_path=Path(""),
        satkit_data_file=data_container_schema.data_name,
        satkit_meta_file=data_container_schema.meta_name,
    )
    meta_path = path / data_container_schema.meta_name
    data_path = path / data_container_schema.data_name

    raw_input = nestedtext.load(meta_path)
    meta = DataContainerLoadSchema.model_validate(raw_input)

    saved_data = np.load(data_path)

    return file_info, meta, saved_data


def load_derived_modality(
        recording: Recording,
        path: Path,
        modality_schema: DataContainerListingLoadSchema
) -> None:
    """
    Load a saved derived Modality meta and data, and add them to the Recording.

    Parameters
    ----------
    recording : Recording
        The Recording the Modality will be added to.
    path : Path
        This is the path to the save files.
    modality_schema : DataContainerListingLoadSchema
        This contains the name of the meta and data files.
    """
    if not modality_schema.meta_name:
        _logger.info(
            "Looks like %s doesn't have a metafile for one of the Modalities.",
            modality_schema.data_name)
        _logger.info(
            "Assuming the Modality to be batch loaded, so skipping.")
        return

    file_info, meta, saved_data = _load_data_container_data_and_meta(
        path, modality_schema)
    
    modality_data = ModalityData(
        saved_data['data'], sampling_rate=saved_data['sampling_rate'],
        timevector=saved_data['timevector'])

    modality_constructor, parameter_schema = metrics[meta.object_type]
    for key in meta.parameters:
        if meta.parameters[key] == 'None':
            meta.parameters[key] = None
    parameters = parameter_schema(**meta.parameters)
    modality = modality_constructor(
        owner=recording,
        file_info=file_info,
        parsed_data=modality_data,
        metadata=parameters)

    recording.add_modality(modality=modality)


def load_statistic(
        owner: Recording | Session,
        path: Path,
        statistic_schema: DataContainerListingLoadSchema
) -> None:
    """
    Load a saved Statistic meta and data, and add them to the Recording.

    Parameters
    ----------
    owner : Recording
        The Recording the Statistic will be added to.
    path : Path
        This is the path to the save files.
    statistic_schema : DataContainerListingLoadSchema
        This contains the name of the meta and data files.
    """
    if not statistic_schema.meta_name:
        _logger.info(
            "Looks like %s doesn't have a metafile for one of the Statistics.",
            statistic_schema.data_name)
        _logger.info(
            "Assuming the Statistic to be batch loaded, so skipping.")
        return

    file_info, meta, saved_data = _load_data_container_data_and_meta(
        path, statistic_schema)

    statistic_data = saved_data['data']

    statistic_constructor, parameter_schema = statistics[meta.object_type]
    for key in meta.parameters:
        if meta.parameters[key] == 'None':
            meta.parameters[key] = None
    parameters = parameter_schema(**meta.parameters)
    statistic = statistic_constructor(
        owner=owner,
        file_info=file_info,
        parsed_data=statistic_data,
        metadata=parameters)

    owner.add_statistic(statistic=statistic)


def read_recording_meta(
        filepath: str | Path | TextIO
) -> RecordingLoadSchema:
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
        A Recording object with most of its modalities loaded. Modalities like
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
    # data has previously been loaded satkit can decide itself what to do with
    # it and there is an easy place where to add processing
    # session/participant/whatever specific config. could also add guessing
    # based on what is present as the final fall back or as the option tried if
    # no meta and config has the wrong guess.

    meta_path = filepath.with_suffix(SatkitSuffix.META)
    if meta_path.is_file():
        # this is a list of Modalities, each with a data path and meta path
        meta = read_recording_meta(filepath)
    else:
        # TODO: need to hand to the right kind of importer here.
        raise NotImplementedError(
            "Can't yet jump to a previously unloaded recording here.")

    # TODO: new directory structure
    file_info = FileInformation(
        recorded_path=Path(""),
        satkit_path=Path(""),
        satkit_meta_file=meta_path.name)
    recording = Recording(meta.parameters, file_info=file_info)

    for modality in meta.modalities:
        if modality in modality_adders:
            adder = modality_adders[modality]
            path = meta.parameters.path / meta.modalities[modality].data_name
            adder(recording, path=path)
        else:
            load_derived_modality(
                recording,
                path=meta.parameters.path,
                modality_schema=meta.modalities[modality])
    for statistic in meta.statistics:
        load_statistic(
            recording,
            path=meta.parameters.path,
            statistic_schema=meta.statistics[statistic])

    return recording


def load_recordings(
        directory: Path, recording_metafiles: list[str] | None = None
) -> list[Recording]:
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
            "*.Recording" + str(SatkitSuffix.META))

    recordings = [load_recording(directory / name)
                  for name in recording_metafiles]

    add_splines(recordings, directory)

    return recordings


def load_recording_session(
        directory: Path | str,
        session_config_path: Path | None = None
) -> Session:
    """
    Load a recording session from a directory.

    Parameters
    ----------
    directory: Path
        Root directory of the data.
    session_config_path : Path | None
        Path to the session configuration file. By default, None.

    Returns
    -------
    Session
        The loaded Session object.
    """
    if isinstance(directory, str):
        directory = Path(directory)

    if not session_config_path:
        session_config_path = directory / SatkitConfigFile.SESSION

    filename = f"{directory.parts[-1]}{'.Session'}{SatkitSuffix.META}"
    filepath = directory / filename

    raw_input = nestedtext.load(filepath)
    meta = SessionLoadSchema.model_validate(raw_input)

    if session_config_path.is_file():
        paths, session_config = load_session_config(
            directory, session_config_path)
    else:
        paths = PathStructure(root=directory)
        session_config = SessionConfig(data_source=meta.parameters.datasource)

    recordings = load_recordings(directory, meta.recordings)

    # TODO: don't really know if the current FileInformation handles the
    # duality of config from user and saved meta too well.
    file_info = FileInformation(
        satkit_meta_file=filename,
        satkit_path=directory,
        recorded_path=directory,
        recorded_meta_file=session_config_path.name)
    session = Session(
        name=meta.name, paths=paths,
        config=session_config,
        file_info=file_info,
        recordings=recordings)

    return session
