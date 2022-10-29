
from contextlib import closing
from pathlib import Path
from typing import Tuple

import numpy as np
# scikit-video for io and processing of video data.
import skvideo.io
# wav file handling
from satkit.data_structures import ModalityData


def read_avi(path: Path, meta: dict, time_offset: float) -> Tuple[np.ndarray, np.ndarray, float]:
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

    return (data, timevector, meta['FramesPerSec'])
