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
from pathlib import Path
from typing import Optional

from satkit.constants import Datasource
from satkit.data_structures import Recording
# Local packages
from satkit.modalities import Video

_AAA_video_logger = logging.getLogger('satkit.AAA_video')


def add_video(recording: Recording, preload: bool = False,
              datasource: Optional[Datasource] = None,
              path: Optional[Path] = None) -> None:
    """
    Create a RawUltrasound Modality and add it to the Recording.

    Parameters
    ----------
    recording : Recording
        _description_
    preload : bool, optional
        Should we load the data when creating the modality or not. Defaults to
        False to prevent massive memory consumption. See also error below.
    path : Optional[Path], optional
        _description_, by default None

    Raises
    ------
    NotImplementedError
        Preloading video data has not been implemented yet. If you really,
        really want to, this is the function where to do that.
    """
    if not path:
        video_file = (recording.path/recording.basename).with_suffix(".avi")
    else:
        video_file = path

    # This is the correct value for fps for a de-interlaced
    # video according to Alan, and he should know having
    # written AAA.
    if datasource is Datasource.AAA:
        meta = {
            'FramesPerSec': 59.94,
            'preload': preload,
        }
    else:
        message = "Trying to create a video Modality, but don't "
        message += "know what to set as frame rate for non-AAA videos."
        raise NotImplementedError(message)

    if video_file.is_file():
        video = Video(
            owner=recording,
            data_path=video_file,
            meta=meta
        )
        recording.addModality(video)
        _AAA_video_logger.debug(
            "Added RawUltrasound to Recording representing %s.",
            recording.path.name)
    else:
        notice = 'Note: ' + str(video_file) + " does not exist."
        _AAA_video_logger.debug(notice)
