
from contextlib import closing
from pathlib import Path
from typing import Tuple

import numpy as np
import satkit.audio_processing as satkit_audio
# wav file handling
import scipy.io.wavfile as sio_wavfile
from satkit.data_structures import ModalityData


def read_ult(path, meta, time_offset) -> Tuple[np.ndarray, np.ndarray, float]:
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

    Also adds the 'no_frames' key and value to the meta dict.
    """
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

        ultra_time = np.linspace(
            0, meta['no_frames'],
            num=meta['no_frames'],
            endpoint=False)
        timevector = ultra_time / \
            meta['FramesPerSec'] + time_offset
        # this should be added for PD and similar time vectors: + .5/self.meta['framesPerSec']
        # while at the same time dropping a suitable number of timestamps

    return (data, timevector, meta['FramesPerSec'])
