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

# Built in packages
import logging
import sys
from pathlib import Path
from typing import List, Tuple

# Numpy and scipy
import numpy as np
# dicom reading
import pydicom
from satkit.data_structures import ModalityData

# TODO change the logger name
_3D4D_ultra_logger = logging.getLogger('satkit.ThreeD_ultrasound')

def read_3d_ultrasound_dicom(
    path: Path,
    meta: dict,
    time_offset: float) -> ModalityData:
    """
    Read 3D ultrasound dicom from path.

    Positional arguments:
    path -- Path of the wav file
    meta -- a dict containing the following keys:
        NumVectors -- number of scanlines in the data
        PixPerVector -- number of pixels on a scanline

    Returns a ModalityData instance that contains the wav frames, 
    a timevector, and the sampling rate. 

    Also adds the 'no_frames' key and value to the meta dict.
    """

    ds = pydicom.dcmread(path)
    # There are other options, but we don't deal with them just yet.
    # TODO Before 1.0: fix the above. see loadPhillipsDCM.m on how.
    if len(ds.SequenceOfUltrasoundRegions) == 3:
        type = ds[0x200d, 0x3016][1][0x200d, 0x300d].value
        if type == 'UDM_USD_DATATYPE_DIN_3D_ECHO':
            data, sampling_rate, scale = _parse_3D_ultra(ds, meta)
        else:
            _3D4D_ultra_logger.critical(
                "Unknown DICOM ultrasound type: " + type + " in "
                + path + ".")
            _3D4D_ultra_logger.critical('Exiting.')
            sys.exit()
    else:
        _3D4D_ultra_logger.critical(
            "Do not know what to do with data with "
            + str(len(ds.SequenceOfUltrasoundRegions)) + " regions in "
            + path + ".")
        _3D4D_ultra_logger.critical('Exiting.')
        sys.exit()

    # Before 1.0: 'NumVectors' and 'PixPerVector' are bad names here.
    # They come from the AAA ultrasound side of things and should be
    # replaced, but haven't been yet as I'm in a hurry to get PD
    # running on 3d4d ultrasound.
    meta['no_frames'] = data.shape[0]
    meta['NumVectors'] = data.shape[1]
    meta['PixPerVector'] = data.shape[2]

    # TODO Before 1.0: unify the way scaling works across the data.
    # here we have an attribute, in AAA ultrasound we have meta
    # keys.


    ultra3D_time = np.linspace(
        0, meta['no_frames'],
        num=meta['no_frames'],
        endpoint=False)
    timevector = ultra3D_time / sampling_rate + time_offset

    return ModalityData(data, sampling_rate, timevector)


def _parse_3D_ultra(ds, meta) -> Tuple[np.ndarray, float, List[float]]:
    ultra_sequence = ds[0x200d, 0x3016][1][0x200d, 0x3020][0]

    # data dimensions
    numberOfFrames = int(ultra_sequence[0x200d, 0x3010].value)
    shape = [int(token) for token in ds[0x200d, 0x3301].value]
    frameSize = np.prod(shape)
    shape.append(numberOfFrames)

    # data scale in real space-time
    scale = [float(token) for token in ds[0x200d, 0x3303].value]
    sampling_rate = float(ds[0x200d, 0x3207].value)

    # The starting index for the non-junk data
    # no junk from pydicom at the beginning. only at end of each frame
    # s = 32

    # Get the number of junk data points between each frame
    interval = (
        len(ultra_sequence[0x200d, 0x300e].value)-frameSize*numberOfFrames)
    interval = int(interval/numberOfFrames)

    data = np.frombuffer(
        ultra_sequence[0x200d, 0x300e].value, dtype=np.uint8)

    # TODO Make sure that the data is in the order expected by everybody else:
    # first dimension is time, then as they are in 2d ultra and z is the last
    # one. also check that the direction of data is correct: axis going the way
    # they should.
    data.shape = (numberOfFrames, frameSize+interval)
    data = np.take(data, np.arange(frameSize)+32, axis=1)
    shape.reverse()
    data.shape = shape

    return data, sampling_rate, scale

    # this should be unnecessary now
    # _data = np.transpose(data)
