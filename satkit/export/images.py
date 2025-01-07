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
Export various images.

Raw and interpolated ultrasound frames, AggregateImages. and DistanceMatrices.
"""
import logging
from pathlib import Path

import numpy as np
from PIL import Image

from satkit.data_structures import Recording, Session
from satkit.data_structures.base_classes import DataAggregator, DataContainer
from satkit.interpolate_raw_uti import to_fan_2d
from satkit.metrics import (
    AggregateImage, DistanceMatrix
)
from satkit.modalities import RawUltrasound

from .metadata import (
    export_aggregate_image_meta,
    export_distance_matrix_meta,
    export_ultrasound_frame_meta
)

_logger = logging.getLogger('satkit.export')


def _export_data_as_image(
        data: DataContainer | np.ndarray,
        path: Path,
        image_format: str = ".png",
        interpolation_params: dict | None = None,
) -> Path:
    if path.is_dir() and not isinstance(data, DataContainer):
        raise ValueError("Data must be DataContainer if path is a directory.")
    elif path.is_dir():
        filename = data.name.replace(" ", "_")
        filepath = path / filename
    else:
        filepath = path

    if isinstance(data, DataContainer):
        raw_data = data.data
    else:
        raw_data = data

    if interpolation_params is not None:
        raw_data = to_fan_2d(raw_data, **interpolation_params)

    im = Image.fromarray(raw_data)
    im = im.convert('L')
    im.save(filepath.with_suffix(image_format))
    _logger.info("Wrote file %s.", filepath)
    return filepath


def _publish_image(
        container: DataAggregator,
        statistic_name: str,
        image_format: str = ".png"
) -> Path | None:
    if statistic_name in container.statistics:
        statistic = container.statistics[statistic_name]
        raw_data = statistic.data
        im = Image.fromarray(raw_data)
        im = im.convert('L')
        name = container.name
        path = container.recorded_path
        image_file = path / (name + image_format)
        im.save(image_file)
        _logger.info("Wrote file %s.", image_file)
        return image_file


def export_aggregate_image_and_meta(
        image: AggregateImage,
        session: Session,
        recording: Recording,
        path: Path,
        image_format: str = ".png",
        interpolation_params: dict | None = None
) -> None:
    """
    Export AggregateImage to an image file and meta to a text file.

    Parameters
    ----------
    image : AggregateImage
        The AggregateImage to be exported.
    session : Session
        Session the AggregateImage belongs to.
    recording : Recording
        Recording that the AggregateImage belongs to.
    path : Path
        Path to save the image and meta file.
    image_format : str, optional
        File format to save the image in, by default ".png"
    interpolation_params : dict | None
        Dictionary of interpolation parameters to be passed to `to_fan_2d`, by
        default None. If none, export raw image instead.
    """
    filepath = _export_data_as_image(
        image, path, image_format, interpolation_params)

    export_aggregate_image_meta(
        filename=filepath.with_suffix(".txt"),
        session=session,
        recording=recording,
        aggregate_meta=image.metadata,
        interpolation_params=interpolation_params
    )


def export_distance_matrix_and_meta(
        matrix: DistanceMatrix,
        session: Session,
        path: Path,
        image_format: str = ".png"
) -> None:
    path = _export_data_as_image(matrix, path, image_format)

    export_distance_matrix_meta(
        filename=path.with_suffix(".txt"),
        session=session,
        distance_matrix_meta=matrix.metadata,
    )


def export_ultrasound_frame_and_meta(
        filepath: str | Path,
        session: Session,
        recording: Recording,
        selection_index: int,
        selection_time: float,
        ultrasound: RawUltrasound,
        image_format: str = ".png",
        interpolation_params: dict | None = None
) -> None:
    """
    Write ultrasound frame metadata to a human-readable text file.

    The purpose of this function is to generate a file documenting an extracted
    ultrasound frame, so that it can be found again in its original context.

    Parameters
    ----------
    filepath : str | Path
        Filename or path for the ultrasound frame to export. Format is deduced
        from the file suffix.
    session : Session
        Session that the frame belongs to.
    recording : Recording
        Recording that the frame belongs to.
    selection_index : int
        Index of the frame within the ultrasound video.
    selection_time : float
        Time in seconds of the frame within the **recording**. This is relative
        to what ever -- most likely the beginning of audio -- is being used as
        t=0s.
    ultrasound : RawUltrasound
        The RawUltrasound from which a frame is to be exported.
    image_format : str, optional
        File format to save the image in, by default ".png"
    interpolation_params : dict | None
        Dictionary of interpolation parameters to be passed to `to_fan_2d`, by
        default None. If none, export raw image instead.
    """
    frame = ultrasound.raw_image(selection_index)
    if filepath.is_dir():
        filename = ultrasound.name.replace(" ", "_")
        filepath = filepath / filename
    filepath = _export_data_as_image(
        frame, filepath, image_format, interpolation_params)

    # figure.savefig(filepath, bbox_inches=bbox_inches, pad_inches=pad_inches)
    _logger.debug("Wrote file %s.", filepath)

    export_ultrasound_frame_meta(
        filename=filepath,
        session=session,
        recording=recording,
        selection_index=selection_index,
        selection_time=selection_time,
    )
