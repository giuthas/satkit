#!/usr/bin/env python3
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
Various helper utilities related to plotting.
"""

import matplotlib.pyplot as plt


def get_colors_in_sequence(number: int) -> list[str]:
    """
    Get colors in a perceptual sequence.

    NOTE: This may or may not end up working for color lists of length other
    than 6 and 7.

    Parameters
    ----------
    number : int
        How many colors to get.

    Returns
    -------
    list[str]
        Names of the colors.
    """
    colors = plt.rcParams['axes.prop_cycle'].by_key()['color'][0:number]
    match number:
        case 6:
            colors = sorted(colors)
            colors = [colors[0], colors[2], colors[1],
                      colors[3], colors[5], colors[4]]
        case 7:
            colors = sorted(colors)
            colors = [colors[0], colors[2], colors[4],
                      colors[3], colors[1], colors[5], colors[6]]
        case _:
            colors = sorted(colors)
    return colors
