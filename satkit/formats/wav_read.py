
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import satkit.audio_processing as satkit_audio
# wav file handling
import scipy.io.wavfile as sio_wavfile
from satkit.datastructures.data_structures import ModalityData


# TODO: break into two different functions: one that runs beep detection and one that doesn't.
def read_wav(path: Path, detect_beep: bool=False):
    """
    Read wavfile from path.

    Positional argument:
    path -- Path of the wav file

    Keyword argument:
    detect_beep -- Should 1kHz beep detection be run. Changes return values (see below).

    Returns a ModalityData instance that contains the wav frames, a timevector, and
    the sampling rate. 

    Also returns the time of a 1kHz go-signal and a guess about if the file contains 
    speech if detect_beep = True.
    """
    (wav_fs, wav_frames) = sio_wavfile.read(path)

    timevector = np.linspace(0, len(wav_frames),
                                    len(wav_frames),
                                    endpoint=False)
    timevector = timevector/wav_fs
    data = ModalityData(wav_frames, wav_fs, timevector)

    if detect_beep:
        # use a high-pass filter for removing the mains frequency (and anything below it)
        # from the recorded sound.
        go_signal, has_speech = satkit_audio.detect_beep_and_speech(
            wav_frames, 
            wav_fs, 
            satkit_audio.MainsFilter.mains_filter['b'],
            satkit_audio.MainsFilter.mains_filter['a'],
            path
        )

        return data, go_signal, has_speech
    else:
        return data
