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

from pathlib import Path

import numpy as np
# scikit-video for io and processing of video data.
import skvideo.io
from satkit.data_structures import ModalityData


def read_avi(path: Path, meta: dict, time_offset: float) -> ModalityData:
    """
    Read wavfile from path.

    Positional arguments:
    path -- Path of the wav file
    meta -- a dict containing the following keys:
        NumVectors -- number of scanlines in the data
        PixPerVector -- number of pixels on a scanline

    Keyword argument:
    detect_beep -- Should 1kHz beep detection be run. Changes return values (see below).

    Returns a ModalityData instance that contains the wav frames, a timevector, and
    the sampling rate. 

    Also adds the 'no_frames', 'width', and 'height' keys and values to the meta dict.
    """
    data = skvideo.io.vread(str(path))

    meta['no_frames'] = data.shape[0]
    meta['width'] = data.shape[1]
    meta['height'] = data.shape[2]
    video_time = np.linspace(
        0, meta['no_frames'],
        num=meta['no_frames'],
        endpoint=False)
    timevector = video_time / \
        meta['FramesPerSec'] + time_offset
    # this should be added for PD and similar time vectors:
    # + .5/self.meta['framesPerSec']
    # while at the same time dropping a suitable number
    # (most likely = timestep) of timestamps

    return ModalityData(data, meta['FramesPerSec'], timevector)
