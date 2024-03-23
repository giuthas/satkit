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

from typing import Optional

# from icecream import ic

import numpy as np

from matplotlib.axes import Axes
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt

from satkit.helpers import polar_to_cartesian
from .contour_tools import contour_point_perturbations


def display_contour(
        axes: Axes,
        contour: np.ndarray,
        text: Optional[bool] = False,
        offset: Optional[float] = 0,
        color: Optional[str] = None) -> None:

    contour = polar_to_cartesian(contour)
    if color:
        line = axes.plot(contour[1, :], contour[0, :], color=color)
    else:
        line = axes.plot(contour[1, :], contour[0, :])
    color = line[0].get_color()

    if text:
        for i in range(contour.shape[1]):
            axes.text(contour[1, i]-offset, contour[0, i],
                      str(i+1), color=color, fontsize=12)


def display_text_on_contours(
        axes: Axes,
        contour1: np.ndarray,
        contour2: np.ndarray,
        outside: Optional[bool] = True,
        offset: Optional[float] = 0,
        color: Optional[str] = None) -> None:

    for i in range(contour1.shape[1]):
        if outside:
            r = max(contour1[0, i], contour2[0, i]) + offset
        else:
            r = min(contour1[0, i], contour2[0, i]) - offset

        r_phi_array = np.array([r, contour1[1, i]])
        text_coords = polar_to_cartesian(r_phi_array)

        axes.text(text_coords[1], text_coords[0],
                  str(i+1), color=color, fontsize=12,
                  horizontalalignment='center', verticalalignment='center')


def draw_contour_segment(
        axes: Axes,
        contour: np.ndarray,
        index: int,
        text: Optional[bool] = False,
        offset: Optional[float] = 0,
        color: Optional[str] = None,) -> None:

    if index == 0:
        contour_segment = polar_to_cartesian(contour[:, :2])
    elif index < contour.shape[1]:
        contour_segment = polar_to_cartesian(contour[:, index-1:index+2])
    elif index == contour.shape[1]:
        contour_segment = polar_to_cartesian(contour[:, index-1:])
    else:
        raise ValueError("Index out of bounds index=" + str(index) +
                         ", shape=" + str(contour.shape))

    if color:
        line = axes.plot(contour_segment[1, :],
                         contour_segment[0, :],
                         color=color)
    else:
        line = axes.plot(contour_segment[1, :],
                         contour_segment[0, :])
    color = line[0].get_color()

    if text:
        text_coords = polar_to_cartesian(contour[:, index] + [offset, 0])
        axes.text(text_coords[1], text_coords[0],
                  str(index+1), color=color, fontsize=12,
                  horizontalalignment='center', verticalalignment='center')


def display_fan(axes, contour: np.ndarray, color: Optional[str] = None) -> None:
    contour = polar_to_cartesian(contour)
    if color:
        for i in range(contour.shape[1]):
            axes.plot([0, contour[1, i]], [0, contour[0, i]], color=color)
    else:
        for i in range(contour.shape[1]):
            axes.plot([0, contour[1, i]], [
                      0, contour[0, i]], color='lightgray')


def make_demonstration_contour_plot(
        contour_1: np.ndarray, contour_2: np.ndarray) -> None:
    plt.style.use('tableau-colorblind10')
    main_color = plt.rcParams['axes.prop_cycle'].by_key()['color'][0]
    accent_color = plt.rcParams['axes.prop_cycle'].by_key()['color'][1]
    accent_color2 = plt.rcParams['axes.prop_cycle'].by_key()['color'][2]

    gridspec_keywords = {
        'wspace': 0.0,
        # 'hspace': 0.0,
        # 'top': .95,
        # 'bottom': 0.05,
    }
    #  top=1.-0.5/(nrow+1), bottom=0.5/(nrow+1),
    #  left=0.5/(ncol+1), right=1-0.5/(ncol+1))
    _, axes = plt.subplots(1, 2, figsize=(6.4, 4.8), sharey=True,
                           gridspec_kw=gridspec_keywords)
    for ax in axes:
        ax.set_aspect('equal')
    display_fan(axes[0], contour_1)
    display_fan(axes[0], contour_2)
    display_contour(axes[0], contour_1, text=False,
                    offset=3.5, color=main_color)
    display_contour(axes[0], contour_2, text=False,
                    offset=-1, color=accent_color)
    display_text_on_contours(
        axes[0], contour_1, contour_2, offset=4, color=accent_color2)

    display_contour(axes[1], contour_1, color=main_color)
    perturbed_positive = contour_point_perturbations(contour_1.copy(), 2)
    perturbed_negative = contour_point_perturbations(contour_1.copy(), -2)
    for i in range(perturbed_positive.shape[0]):
        draw_contour_segment(
            axes[1], perturbed_positive[i, :, :], index=i,
            text=True, offset=2, color=accent_color)
        draw_contour_segment(
            axes[1], perturbed_negative[i, :, :], index=i,
            text=False, offset=2, color=accent_color2)

    axes[0].set_ylim((-10, 120))
    axes[1].set_ylim((-10, 120))
    axes[0].set_xlim((-70, 25))
    axes[1].set_xlim((-70, 25))

    plt.show()


def plot_dyadic_metric_against_perturbation_point(
        axes: list[Axes], data: dict[str, np.ndarray],
        label_stem: Optional[str] = 'perturbation=',
        colors: Optional[list[str]] = None
) -> tuple[list[Line2D], list[str]]:
    """
    Plot metric as function of perturbation point's number.

    Parameters
    ----------
    axes : list[Axes]
        List of axes to plot on. This should be of length 2.
    data : dict[str, np.ndarray]
        Dict keys are perturbation values and arrays are interleaved
        baseline_to_perturbed and perturbed_to_baseline metric values.
    label_stem : Optional[str], optional
        Used in generating line labels, by default 'perturbation='

    Returns
    -------
    tuple[list[Line2D], list[str]]
        List of lines and list of labels for legend creation.
    """
    lines = []
    labels = []
    i = 0
    color = None
    for perturbation in data:
        baseline_to_perturbed = data[perturbation][::2]
        perturbed_to_baseline = data[perturbation][1::2]
        x_values = list(range(1, baseline_to_perturbed.shape[0]+1))

        if colors is not None:
            color = colors[i]
            i += 1
        lines.append(
            axes[0].plot(
                x_values, baseline_to_perturbed,
                label=label_stem + str(perturbation),
                color=color
            )[0]
        )
        axes[1].plot(
            x_values, perturbed_to_baseline,
            label=label_stem + str(perturbation),
            color=color
        )
        labels.append(f"{label_stem}{perturbation}")

    return (lines, labels)
