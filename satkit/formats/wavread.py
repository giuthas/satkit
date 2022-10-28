
import numpy as np
import satkit.audio_processing as satkit_audio
# wav file handling
import scipy.io.wavfile as sio_wavfile
from satkit.data_structures import ModalityData


def read_wav(path):
    (wav_fs, wav_frames) = sio_wavfile.read(path)

    # use a high-pass filter for removing the mains frequency (and anything below it)
    # from the recorded sound.
    go_signal, has_speech = satkit_audio.detect_beep_and_speech(
        wav_frames, 
        wav_fs, 
        satkit_audio.MainsFilter.filter['b'],
        satkit_audio.MainsFilter.filter['a'],
        path
    )

    timevector = np.linspace(0, len(wav_frames),
                                    len(wav_frames),
                                    endpoint=False)
    timevector = timevector/wav_fs
    return ModalityData(wav_frames, timevector, wav_fs), go_signal, has_speech
