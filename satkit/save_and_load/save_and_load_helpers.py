from datetime import datetime
from pathlib import Path, PosixPath, WindowsPath
from typing import Union

from pydantic import BaseModel, DirectoryPath

from satkit.constants import Datasource, SavedObjectTypes
from satkit.data_structures import RecordingMetaData


nested_text_converters = {
    datetime: str,
    PosixPath: str,
    WindowsPath: str,
    Path: str
}


class ModalityLoadSchema(BaseModel):
    """
    Loading schema for a saved Modality.

    Modality is defined in the data_structures module.
    """
    object_type: str
    name: str
    format_version: str
    parameters: dict


class ModalityListingLoadschema(BaseModel):
    """
    Loading schema for the Modality listing in a saved Rercording.
    """
    data_name: str
    meta_name: Union[str, None]


class RecordingLoadSchema(BaseModel):
    """
    Loading schema for a saved Recording.

    Recording is defined in the data_structures module.
    """
    object_type: SavedObjectTypes = SavedObjectTypes.RECORDING
    name: str
    format_version: str
    parameters: RecordingMetaData
    modalities: dict[str, ModalityListingLoadschema]


class RecordingSessionParameterLoadSchema(BaseModel):
    """
    Loading schema for a saved RecordingSession.

    RecordingSession is defined in the data_structures module.
    """
    path: DirectoryPath
    datasource: Datasource


class RecordingSessionLoadSchema(BaseModel):
    """
    Loading schema for a saved RecordingSession.

    RecordingSession is defined in the data_structures module.
    """
    object_type: SavedObjectTypes = SavedObjectTypes.RECORDING_SESSION
    name: str
    format_version: str
    parameters: RecordingSessionParameterLoadSchema
    recordings: list[str]
