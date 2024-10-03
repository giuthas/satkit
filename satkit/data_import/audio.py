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
import logging
from pathlib import Path
from typing import Optional

from satkit.configuration import data_run_params
from satkit.data_structures import Recording, FileInformation
from satkit.import_formats import read_wav, read_wav_and_detect_beep
from satkit.modalities import MonoAudio

_generic_io_logger = logging.getLogger('satkit.data_structures')


def add_audio(
        recording: Recording,
        preload: bool = True,
        path: Optional[Path] = None) -> None:
    """
    Create a MonoAudio Modality and add it to the Recording.

    Parameters
    ----------
    recording : Recording
        _description_
    preload : bool, optional
        _description_, by default True
    path : Optional[Path], optional
        _description_, by default None
    detect_beep : bool, optional
        _description_, by default False
    """
    if not path:
        ult_wav_file = (recording.path/recording.basename).with_suffix(".wav")
    else:
        ult_wav_file = path

    if ult_wav_file.is_file():
        file_info = FileInformation(
            recorded_path=Path(""),
            recorded_data_file=ult_wav_file.name
        )
        if preload and data_run_params['flags']['detect_beep']:
            data, go_signal, has_speech = read_wav_and_detect_beep(
                ult_wav_file)
            waveform = MonoAudio(
                recording=recording,
                file_info=file_info,
                parsed_data=data,
                go_signal=go_signal,
                has_speech=has_speech
            )
            recording.add_modality(waveform)
        elif preload:
            data = read_wav(ult_wav_file)
            waveform = MonoAudio(
                recording=recording,
                file_info=file_info,
                parsed_data=data,
            )
            recording.add_modality(waveform)
        else:
            waveform = MonoAudio(
                recording=recording,
                file_info=file_info,
            )
            recording.add_modality(waveform)
        _generic_io_logger.debug(
            "Added MonoAudio to Recording representing %s.",
            recording.path.name)
    else:
        notice = 'Note: ' + str(ult_wav_file) + " does not exist. Excluding."
        _generic_io_logger.warning(notice)
        recording.exclude()
