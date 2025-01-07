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
"""
Data and metadata importing.
"""

from .AAA_recordings import (generate_aaa_recording_list,
                             generate_ultrasound_recording)
from .RASL_3D_ultrasound_recordings import (generate_3D_ultrasound_recording,
                                            generate_rasl_recording_list)
from .session_import_config import load_session_config

from .audio import add_audio
from .video import add_video
from .AAA_raw_ultrasound import add_aaa_raw_ultrasound
from .three_dim_ultrasound import add_rasl_3D_ultrasound
from .AAA_splines import add_splines

# TODO: Decide if it is worth it to use typing.Annotated to document this
# modality_adders is a mapping between a modality name and a function to add
# that modality to a single recording.
#
# This does not belong here because splines may be in a
# single file for many recordings.
# 'Splines': add_splines,
modality_adders = {
    'MonoAudio': add_audio,
    'RawUltrasound': add_aaa_raw_ultrasound,
    'ThreeD_Ultrasound': add_rasl_3D_ultrasound,
    'Video': add_video
}
