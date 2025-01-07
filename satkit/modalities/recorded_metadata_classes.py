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
Metadata for recorded (external) data.
"""

from satkit.data_structures import ModalityMetaData


class RawUltrasoundMeta(ModalityMetaData):
    """
    Metadata for RawUltrasound data.

    num_vectors -- number of scanlines in a frame
    pix_Ver_vector -- number of pixels in a scanline
    zero_offset --
    bits_per_pixel -- byte length of a single pixel in the .ult file
    angle -- angle in radians between two scanlines
    kind -- type of probe used
    pixels_per_mm -- depth resolution of a scanline
    frames_per_sec -- frame rate of ultrasound recording
    """
    angle: float
    frames_per_sec: float
    num_vectors: int
    pix_per_vector: int
    pixels_per_mm: float
    zero_offset: float
    kind: int
    bits_per_pixel: int
