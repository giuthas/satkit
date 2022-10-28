import logging
from pathlib import Path
from typing import Optional

import formats
from data_structures import Recording
from modalities import MonoAudio

_generic_io_logger = logging.getLogger('satkit.data_structures')

def add_audio(recording: Recording, preload: bool,
                path: Optional[Path]=None) -> None:
    """Create a MonoAudio Modality and add it to the Recording."""
    if not path:
        ult_wav_file = (recording.path/recording.basename).with_suffix(".wav")
    else:
        ult_wav_file = path

    if ult_wav_file.is_file():
        if preload:
            data, go_signal, has_speech = formats.wavread(ult_wav_file, detect_beep=True)
            waveform = MonoAudio(
                recording=recording,
                data_path=ult_wav_file,
                parsed_data = data
            )
            recording.add_modality(waveform)
        else:
            waveform = MonoAudio(
                recording=recording,
                data_path=ult_wav_file
            )
            recording.add_modality(waveform)
        _generic_io_logger.debug(
            "Added MonoAudio to Recording representing %s.",
            recording.path.name)
    else:
        notice = 'Note: ' + str(ult_wav_file) + " does not exist. Excluding."
        _generic_io_logger.warning(notice)
        recording.exclude()


