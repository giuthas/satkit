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
Tools for working with simulated tongue contours.
"""


from typing import Optional, Union

import numpy as np

from satkit.external_class_extensions import (
    enum_union, ListablePrintableEnum, ValueComparedEnumMeta)


class SimulationContourVowel(
        ListablePrintableEnum, metaclass=ValueComparedEnumMeta):
    """
    Currently available simulated vowel contours.
    """
    AE = 'æ'
    I = 'i'


class SimulationContourConsonant(
        ListablePrintableEnum, metaclass=ValueComparedEnumMeta):
    """
    Currently available simulated consonant contours.
    """


SimulationContourSoundEnum = enum_union(
    [SimulationContourVowel, SimulationContourConsonant],
    "SimulationContourEnum")


def generate_contour(
        sound: Optional[Union[str, SimulationContourSoundEnum]] = None,
        number_of_points: Optional[int] = 42
) -> np.ndarray:
    """
    Generate a radial contour for the requested sound.

    Parameters
    ----------
    sound : SimulationContourEnum, optional
        The requested sound, by default SimulationContourVowel.AE

    number_of_points : Optional[int], optional
        Future option for generating a different number of interpolation
        points, by default 42

    Returns
    -------
    np.ndarray
        The contour with axes [(r, phi), (number_of_points)].

    Raises
    ------
    NotImplementedError
        Currently raised if number_of_points != 42
    ValueError
        Raised if an unavailable sound is requested.
    """
    if sound is None:
        sound = SimulationContourVowel.AE
    elif isinstance(sound, str):
        sound = SimulationContourSoundEnum(sound)

    if number_of_points != 42:
        raise NotImplementedError(
            "Using a different number of interpolation "
            "points is not yet implemented.")

    match sound:
        case SimulationContourVowel.I:
            r = [64, 76, 81, 86, 90, 94, 97, 100, 102, 103,
                 104, 104, 103, 102, 100, 98, 96.5, 95, 92, 88,
                 82, 74, 65, 60, 57, 54, 52, 50.5, 49, 47.5,
                 46, 45, 44, 43, 42.5, 42, 42, 42, 42, 42,
                 42, 42]
        case SimulationContourVowel.AE:
            r = [64, 65, 66, 68, 70, 72.5, 75, 77.5, 80, 83,
                 86, 87.5, 88, 88, 88, 88, 88, 88, 88, 87,
                 86, 84.5, 83, 82, 80, 78, 76, 73.5, 71, 68.5,
                 66, 64, 62, 60.5, 59, 58, 57, 56, 55, 54.5,
                 54, 54]
        case _:
            raise ValueError(
                f"Tongue contour requested for undefined sound: {sound}.")

    # rotate the [-1.1776, 1.1776] sector by -0.4 radians
    phi = np.linspace(15, -87.5, number_of_points, True)
    phi = phi*np.pi/180

    return np.stack([r, phi], 0)


def contour_point_perturbations(
        contour: np.ndarray,
        reference_contour: Optional[np.ndarray] = None,
        perturbation: Optional[float] = 1.0,
        interleave: Optional[bool] = False
) -> np.ndarray:
    """
    Perturb a contour by the given amount at each point at a time.

    Parameters
    ----------
    contour : np.ndarray
        The contour to be perturbed.
    reference_contour : Optional[np.ndarray], optional
        The contour to interleave with the perturbed contour. If None, the
        original contour is used instead, by default None
    perturbation : Optional[float], optional
        How much the perturbed point should be moved in the r direction, by
        default 1.0
    interleave : Optional[bool], optional
        If every other contour in the result should be the reference contour,
        by default False

    Returns
    -------
    np.ndarray
        Each row is a contour. Either with [perturbed at [0], perturbed at [1],
        etc] or [reference, perturbed at [0], reference, perturbed at [1],
        reference, etc, reference] if interleave == True.
    """
    r = contour[0, :]
    phi = contour[1, :]
    n = contour.shape[1]

    perturbations = np.identity(n=n)*perturbation
    perturbed_r_stack = np.add(perturbations, r)

    if interleave and reference_contour is None:
        reference_contour = contour

    if interleave:
        reference_r = reference_contour[0, :]
        reference_r_stack = np.tile(reference_r, n+1)
        reference_r_stack.shape = [n+1, n]

        interleaved = np.empty(
            [reference_r_stack.shape[0]+perturbed_r_stack.shape[0],
             2,
             reference_r_stack.shape[1]])

        interleaved[::2, 0, :] = reference_r_stack
        interleaved[1::2, 0, :] = perturbed_r_stack
        interleaved[:, 1, :] = phi

        return interleaved

    phis = np.tile(phi, n)
    phis.shape = [n, n]
    return np.stack([perturbed_r_stack, phis], 1)
