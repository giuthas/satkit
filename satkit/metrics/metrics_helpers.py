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
Functions used by several metrics in their calculation.
"""

import numpy as np


def calculate_timevector(
        original_timevector: np.ndarray, timestep: int) -> np.ndarray:
    """
    Calculater the timevector of a derived Modality.

    Parameters
    ----------
    original_timevector : np.ndarray
        Timevector of the Modality that the metric is calculated on.
    timestep : int
        Timestep used in calculating the metric.

    Returns
    -------
    np.ndarray
        The calculated timevector which will be shorter than the original.

    Raises
    ------
    ValueError
        If timestep is smaller than 1.
    """
    if timestep < 1:
        raise ValueError("Timestep has to be a positive integer.")
    if timestep == 1:
        half_step_early = original_timevector[0:-1]
        half_step_late = original_timevector[1:]
        timevector = np.divide(half_step_early+half_step_late, 2.0)
    elif timestep % 2 == 1:
        begin = timestep // 2
        end = -(timestep // 2 + 1)
        half_step_early = original_timevector[begin:end]
        half_step_late = original_timevector[begin+1:end+1]
        timevector = (half_step_early+half_step_late)/2
    else:
        timevector = original_timevector[timestep//2:-timestep//2]

    return timevector
