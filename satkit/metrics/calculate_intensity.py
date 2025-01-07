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

import logging

# Numpy and scipy
import numpy as np

# local modules
from satkit.data_structures import Modality

_pd_logger = logging.getLogger('satkit.intensity')


def calculate_intensity(parent_modality: Modality) -> np.ndarray:
    """
    Calculate overall intensity on the Modality as a function of time.

    Parameters
    ----------
    parent_modality : Modality
        Modality containing grayscale data.

    Returns
    -------
    np.ndarray
        Overall intensity as a function of time.
    """
    data = parent_modality.data
    return np.sum(data, axis=(1, 2))
    # TODO: Compare this to the PD similarity matrix used by Gabor et al.
