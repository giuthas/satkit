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
Functions for reading splines from different formats.
"""

from contextlib import closing
from pathlib import Path

import numpy as np
from satkit.data_structures import ModalityData


def read_splines(
        path: Path,
        meta: dict,
        time_offset: float) -> ModalityData:
    # TODO: edit the below to import splines instead of ultrasound data
    with closing(open(path, 'rb')) as ult_file:
        ult_data = ult_file.read()
        ultra = np.fromstring(ult_data, dtype=np.uint8)
        ultra = ultra.astype("float32")

        meta['no_frames'] = int(
            len(ultra) /
            (meta['NumVectors'] * meta['PixPerVector']))
        data = ultra.reshape(
            (meta['no_frames'],
                meta['NumVectors'],
                meta['PixPerVector']))

        # TODO The following transpose and flip are done to match
        # interpolate_raw_uti.py expectations. Need to check if those
        # expectations could be altered.

        # Re-order indeces to time, height (along scanline), width
        data = np.transpose(data, (0, 2, 1))
        # Flip height dimension
        data = np.flip(data, 1)

        ultra_time = np.linspace(
            0, meta['no_frames'],
            num=meta['no_frames'],
            endpoint=False)
        timevector = ultra_time / \
            meta['FramesPerSec'] + time_offset
        # this should be added for PD and similar time vectors: +
        # .5/self.meta['framesPerSec'] while at the same time dropping a
        # suitable number of timestamps

    return ModalityData(data, meta['FramesPerSec'], timevector)
