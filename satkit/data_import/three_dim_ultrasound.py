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
from copy import deepcopy
from datetime import datetime
from pathlib import Path, PureWindowsPath
from typing import Optional

# Numpy and scipy
import numpy as np
# from numpy.matlib import repmat
import scipy.io
from satkit.data_structures import Recording

_3D4D_ultra_logger = logging.getLogger('satkit.ThreeD_ultrasound')


def read_3D_meta_from_mat_file(mat_file):
    """
    Read a RASL .mat file and return relevant contents as a dict.

    Positional argument:
    mat_file -- either a pathlib Path object representing the .mat 
        file or a string of the same.

    Returns -- an array of dicts that contain the following fields:
        'trial_number': number of the recording within this session,
        'prompt': prompt displayed to the participant,
        'date_and_time': a datetime object of the time recording 
            started, and
        'dat_filename': string representing the name of the .dat 
            sound file.
    """
    mat = scipy.io.loadmat(str(mat_file), squeeze_me=True)
    meta = []
    for element in mat['officialNotes']:
        # Apparently squeeze_me=True is a bit too strident and
        # somehow looses the shape of the most interesting level
        # in the loadmat call. Not using it is not a good idea
        # though so we do this:
        element = element.item()
        if len(element) > 5:
            # We try this two ways, because at least once filename
            # and date fields were in reversed order inside the
            # .mat file.
            try:
                date_and_time = datetime.strptime(
                    element[4], "%d-%b-%Y %H:%M:%S")
                file_path = element[5]
            except ValueError:
                date_and_time = datetime.strptime(
                    element[5], "%d-%b-%Y %H:%M:%S")
                file_path = element[4]

            meta_token = {
                'trial_number': element[0],
                'prompt': element[1],
                'date_and_time': date_and_time,
                'dat_filename': PureWindowsPath(file_path).name
            }
            meta.append(meta_token)
    return meta


def generateMeta(rows):
    """
    Parse a RASL .mat file's rows and return relevant contents as a dict.

    Positional argument:
    mat_file -- either a pathlib Path object representing the .mat
        file or a string of the same.

    Returns -- an array of dicts that contain the following fields:
        'trial_number': number of the recording within this session,
        'prompt': prompt displayed to the participant,
        'date_and_time': a datetime object of the time recording
            started, and
        'dat_filename': string representing the name of the .dat
            sound file.
    """
    meta = []
    for row in rows:
        date_and_time = datetime.strptime(
            row['US File Name'], "%Y%m%d%H%M%S")

        meta_token = {
            'trial_number': row['number_portion'],
            'prompt': row['Stimulus'],
            'date_and_time': date_and_time,
            'dat_filename': row['sound_filename'],
            'sound_filename': row['sound_filename']
        }
        meta.append(meta_token)
    return meta


def add_rasl_3D_ultrasound(recording: Recording, preload: bool,
                           path: Optional[Path] = None) -> None:
    """Create a RawUltrasound Modality and add it to the Recording."""
