#
# Copyright (c) 2019-2024
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
Publish AggregateImages and DistanceMatrices as image files.
"""
from PIL import Image

from satkit.data_structures import Session
from satkit.data_structures.base_classes import DataAggregator


def publish_aggregate_images(
        session: Session, image_name: str, image_format: str = ".png") -> None:
    """
    Publish AggregateImages as image files.

    Parameters
    ----------
    session : Session
        Session containing the Recordings whose AggregateImages are being saved.
    image_name : str
        Name of the AggregateImage to publish.
    image_format : str
        File format to use, by default ".png".
    """
    for recording in session:
        _publish_image(recording, image_name, image_format)


def publish_distance_matrix(
        session: Session, distance_matrix_name: str, image_format: str = ".png"
) -> None:
    """
    Publish DistanceMatrix as an image file.

    Parameters
    ----------
    session : Session
        Session containing the DistanceMatrix which is being saved.
    distance_matrix_name : str
        Name of the DistanceMatrix to publish.
    image_format : str
        File format to use, by default ".png".
    """
    _publish_image(session, distance_matrix_name, image_format)


def _publish_image(
        container: DataAggregator,
        statistic_name: str,
        image_format: str = ".png") -> None:
    if statistic_name in container.statistics:
        statistic = container.statistics[statistic_name]
        raw_data = statistic.data
        im = Image.fromarray(raw_data)
        im = im.convert('L')
        name = container.name
        path = container.recorded_path
        image_file = path / (name + image_format)
        im.save(image_file)
