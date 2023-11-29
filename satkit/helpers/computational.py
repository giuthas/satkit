#
# Copyright (c) 2019-2023
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
Computation helper functions.
"""

import numpy as np
# from icecream import ic


def cartesian_to_polar(xy_array: np.ndarray) -> np.ndarray:
    """
    Transform an array of 2D Cartesian coordinates to polar coordinates.

    Parameters
    ----------
    xy_array : np.ndarray
        axes order is x-y, splinepoints

        This maybe passed in as 1D array which will then be reshaped into a 2*x
        array. This makes it possible to apply the transformation with
        `np.apply_along_axis`.

    Returns
    -------
    np.ndarray
        axes order is r-phi, splinepoints
    """
    if xy_array.ndim == 1 and xy_array.shape[0] % 2 == 0:
        xy_array = xy_array.reshape((2, xy_array.shape[0]//2))

    r = np.sqrt((xy_array**2).sum(0))
    phi = np.arctan2(xy_array[1, :], xy_array[0, :])
    return np.stack(r, phi)


def polar_to_cartesian(
        r_phi_array: np.ndarray,
        angle_offset: float = 0) -> np.ndarray:
    """
    Transform an array of 2D polar coordinates to Cartesian coordinates.

    Parameters
    ----------
    r_phi_array : np.ndarray
        axes order is r-phi, splinepoints 

        This maybe passed in as 1D array which will then be reshaped into a 2*x
        array. This makes it possible to apply the transformation with 
        `   r_phi = self.data[:, 0:2, :]
            r_phi = r_phi.reshape([self.data.shape[0], -1])
            coords = np.apply_along_axis(
                polar_to_cartesian, 1, r_phi)`

    Returns
    -------
    np.ndarray
        axes order is x-y, splinepoints
    """
    if r_phi_array.ndim == 1 and r_phi_array.shape[0] % 2 == 0:
        r_phi_array = r_phi_array.reshape((2, r_phi_array.shape[0]//2))

    x = r_phi_array[0, :] * np.cos(r_phi_array[1, :]-angle_offset)
    y = r_phi_array[0, :] * np.sin(r_phi_array[1, :]-angle_offset)
    return np.stack((x, y))
