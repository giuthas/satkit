#
# Copyright (c) 2019-2022 Pertti Palo, Scott Moisik, Matthew Faytak, and Motoki Saito.
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
import glob
import logging
import os
from pathlib import Path
from typing import Optional

# Local packages
from satkit.audio_processing import MainsFilter
from satkit.configuration import (config, data_run_params,
                                  set_exclusions_from_file)
from satkit.data_import.add_AAA_raw_ultrasound import (add_aaa_raw_ultrasound,
                                                       parse_aaa_promptfile)
from satkit.data_import.add_audio import add_audio
from satkit.data_import.add_video import add_video
from satkit.data_structures import Recording

_AAA_logger = logging.getLogger('satkit.AAA')

#
# The logic here is to do a as much as we can with minimal arguments.
# Therefore, generate_recording_list uses helpers to read all the meta
# and all the Data that it can without using any other arguments.
#
# Next step is to decorate that list with single file passes
# like the exclusion list and splines.
#

def generate_aaa_recording_list(
    directory: Path, 
    config: Optional[dict]=None):
    """
    Produce an array of Recordings from an AAA export directory.

    Prepare a list of Recording objects from the files exported by AAA
    into the named directory. File existence is tested for,
    and if crucial files are missing from a given recording it will be
    excluded.

    Each recording meta file (.txt, not US.txt) will
    be represented by a Recording object regardless of whether a complete
    set of files was found for the recording. Exclusion is marked with
    recording.excluded rather than not listing the recording. Log
    file will show reasons of exclusion.

    The processed files are
    recording meta: .txt,
    ultrasound meta: US.txt or .param,
    ultrasound: .ult, and
    audio waveform: .wav.

    Additionally these will be added, but missing files are considered
    non-fatal
    TextGrid: .textgrid, and
    avi video: .avi.

    directory -- the path to the directory to be processed.
    Returns an array of Recording objects sorted by date and time
        of recording.
    """

    # this is equivalent with the following:
    # sorted(glob.glob(directory + '/.' +  '/*US.txt'))
    ult_meta_files = sorted(glob.glob(directory + '/*US.txt'))
    if len(ult_meta_files) == 0:
        ult_meta_files = sorted(glob.glob(directory + '/*.param'))

    if config['mains frequency']:
        MainsFilter.generate_mains_filter(
            44100, 
            config['mains frequency'])
    else:
        MainsFilter.generate_mains_filter(44100, 50)
    

    # this takes care of *.txt and *US.txt overlapping. Goal
    # here is to include also failed recordings with missing
    # ultrasound data in the list for completeness.
    ult_prompt_files = [prompt_file
                        for prompt_file in glob.glob(directory + '/*.txt')
                        if not prompt_file in ult_meta_files
                        ]
    ult_prompt_files = sorted(ult_prompt_files)

    # strip file extensions off of filepaths to get the base names
    base_paths = [os.path.splitext(prompt_file)[0]
                  for prompt_file in ult_prompt_files]
    basenames = [Path(path).name for path in base_paths]
    recordings = [
        generate_ultrasound_recording(basename, Path(directory))
        for basename in basenames
    ]

    set_exclusions_from_file(
        data_run_params['data properties']['exclusion list'], 
        recordings)


    for recording in recordings: 
        if not recording.excluded:
            add_modalities(recording)

    return sorted(recordings, key=lambda token: token.meta_data.time_of_recording)


def generate_ultrasound_recording(basename: str, directory: Path):
    """
    Generate an UltrasoundRecording without Modalities.

    Arguments:
    basename -- name of the files to be read without type extensions but
        with path.

    KeywordArguments:
    directory -- path to files

    Returns an AaaUltrasoundRecording without any modalities.
    """

    _AAA_logger.info(
        "Building Recording object for %s in %s.", basename, directory)

    meta = parse_aaa_promptfile((directory/basename).with_suffix('.txt'))

    textgrid = directory/basename
    textgrid = textgrid.with_suffix('.TextGrid')

    if textgrid.is_file():
        recording = Recording(
            meta_data=meta,
            path=directory,
            basename=basename,
            textgrid_path=textgrid
        )
    else:
        recording = Recording(
            meta_data=meta,
            path=directory,
            basename=basename
        )

    return recording


def add_modalities(recording: Recording, wav_preload: bool=True, ult_preload: bool=False,
                    video_preload: bool=False):
    """
    Add audio and raw ultrasound data to the recording.

    Keyword arguments:
    wavPreload -- boolean indicating if the .wav file is to be read into
        memory on initialising. Defaults to True.
    ultPreload -- boolean indicating if the .ult file is to be read into
        memory on initialising. Defaults to False. Note: these
        files are, roughly one to two orders of magnitude
        larger than .wav files.
    videoPreload -- boolean indicating if the .avi file is to be read into
        memory on initialising. Defaults to False. Note: these
        files are, yet again, roughly one to two orders of magnitude
        larger than .ult files.

    Throws KeyError if TimeInSecsOfFirstFrame is missing from the
    meta file: [directory]/basename + .txt.
    """
    _AAA_logger.info("Adding modalities to recording for %s.",
        recording.basename)

    add_audio(recording, wav_preload)
    add_aaa_raw_ultrasound(recording, ult_preload)
    add_video(recording, video_preload)




