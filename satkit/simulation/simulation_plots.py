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
Plotting routines for simulation results.
"""

from typing import Optional

import numpy as np

from matplotlib.axes import Axes
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt

from satkit.utility_functions import polar_to_cartesian, cartesian_to_polar
from .contour_tools import contour_point_perturbations


def display_contour(
        axes: Axes,
        contour: np.ndarray,
        display_indeces: Optional[bool] = False,
        offset: Optional[float] = 0,
        origin_offset: Optional[tuple[float, float]] = (0.0, 0.0),
        color: Optional[str] = None,
        polar: Optional[bool] = True) -> None:
    """
    Plot a contour.

    Parameters
    ----------
    axes : Axes
        Axes to plot.
    contour : np.ndarray
        The contour to plot
    display_indeces : Optional[bool], optional
        Should indeces be displayed, by default False
    offset : Optional[float], optional
        Radial offset of the index texts, by default 0
    origin_offset: Optional[tuple[float, float]]
        Offset of the contour origin in cartesian coordinates, 
        by default (0.0, 0.0)
    color : Optional[str], optional
        Color to display both the contour and the indeces in, by default None
    """
    if polar:
        contour = polar_to_cartesian(contour)

    origin_offset = np.array(origin_offset).reshape((2, 1))
    contour = np.add(origin_offset, contour)

    if color:
        line = axes.plot(contour[1, :], contour[0, :], color=color)
    else:
        line = axes.plot(contour[1, :], contour[0, :])
    color = line[0].get_color()

    if display_indeces:
        for i in range(contour.shape[1]):
            axes.text(contour[1, i]-offset, contour[0, i],
                      str(i+1), color=color, fontsize=12)


def _metric_values_to_rays(
        contour: np.ndarray,
        metric_values: dict[str, np.ndarray],
        origin_offset: Optional[tuple[float, float]] = (0.0, 0.0),
        relative: Optional[bool] = False,
) -> list[np.ndarray]:
    """
    Helper function to transform metric values to ray segments.

    This implicitly is used by contour_ray_plot to generate the segments and is
    not precisely meant for public use.

    Parameters
    ----------
    contour : np.ndarray
        Contour to plot on.
    metric_values : dict[str, np.ndarray]
        Metric values to plot by perturbation values.
    origin_offset : Optional[tuple[float, float]], optional
        Cartesian offset for the origin, by default (0.0, 0.0)
    relative : Optional[bool], optional
        True for calculating the ray magnitude as ratio of metric value and
        metric reference value; False for ray magnitude as difference between
        metric value and reference., by default False

    Returns
    -------
    list[np.ndarray]
        List of np.ndarrays to feed to LineCollection.
    """
    if relative:
        ray_r = metric_values + contour[0, :]
    else:
        ray_r = metric_values + contour[0, :]
    rays = np.stack([ray_r, contour[1, :]])

    rays = polar_to_cartesian(rays)
    rays_cart = np.add(origin_offset, rays)

    contour_cart = polar_to_cartesian(contour)
    contour_cart = np.add(origin_offset, contour_cart)

    segments = [np.stack(
        [contour_cart[::-1, i], rays_cart[::-1, i]], axis=0)
        for i in range(contour_cart.shape[1])
    ]

    return segments


def contour_ray_plot(
    axes: Axes,
    contour: np.ndarray,
    metric_values: dict[str, np.ndarray],
    metric_reference_value: float,
    scale: Optional[float] = 1,
    origin_offset: Optional[tuple[float, float]] = (0.0, 0.0),
    relative: Optional[bool] = False,
    color_threshold: Optional[tuple[float, float]] = None,
    colors: Optional[list[tuple[float, float, float, float]]] = None
) -> None:
    """
    Plot metric values as rays on a contour.

    Parameters
    ----------
    axes : Axes
        Axes to plot on.
    contour : np.ndarray
        Contour to plot on.
    metric_values : dict[str, np.ndarray]
        Metric values to plot by perturbation values.
    metric_reference_value : float
        Metric value to use as reference.
    scale : Optional[float], optional
        Scaling factor for the rays, by default 1
    origin_offset : Optional[tuple[float, float]], optional
        Cartesian offset for the origin, by default (0.0, 0.0)
    relative : Optional[bool], optional
        True for calculating the ray magnitude as ratio of metric value and
        metric reference value; False for ray magnitude as difference between
        metric value and reference., by default False
    color_threshold :  Optional[tuple(float, float)]
        Threshold to switch from the first to the second color in plotting the
        rays if a second color is specified (see below). Specified in metric's
        units relative to the `metric_reference_value`. If only one float is
        given instead of tuple of two, it will be used symmetrically as
        +/-color_threshold. By default None
    colors : Optional[list[tuple[float,float,float,float]]]
        One or two RGB or RGBA tuples: e.g. [(0.1, 0.1, 0.1, 1.0)] to specify a
        single color. Arbitrary color strings, etc, are not allowed, by default
        None
    """
    # making sure that array operations work as expected.
    if color_threshold is not None:
        color_threshold = np.array(color_threshold)
    origin_offset = np.array(origin_offset).reshape((2, 1))

    if relative:
        metric_values = np.log10(metric_values / metric_reference_value)
        metric_values = scale * metric_values
        if color_threshold is not None:
            color_threshold = scale * color_threshold
    else:
        metric_values = (metric_values - metric_reference_value)*scale
        if color_threshold is not None:
            color_threshold = color_threshold*scale

    contour_cart = polar_to_cartesian(contour)
    contour_cart = np.add(origin_offset, contour_cart)
    axes.plot(contour_cart[1, :], contour_cart[0, :], color='grey')

    segments = _metric_values_to_rays(
        contour=contour, metric_values=metric_values,
        relative=relative, origin_offset=origin_offset)

    if colors is None:
        line_segments = LineCollection(segments, linestyles='solid')
        axes.add_collection(line_segments)
    elif color_threshold is None:
        line_segments = LineCollection(
            segments, linestyles='solid', colors=colors[0])
        axes.add_collection(line_segments)
    elif color_threshold is not None and len(colors) == 2:
        if len(color_threshold) < 2:
            if relative:
                raise NotImplementedError(
                    "For relative=True, you need to provide "
                    "the upper and lower color_threshold")
            color_threshold = (color_threshold, -color_threshold)
        line_segments = LineCollection(
            segments,
            linestyles='solid',
            colors=colors[1]
        )
        axes.add_collection(line_segments)

        metric_values[metric_values > color_threshold[0]] = color_threshold[0]
        metric_values[metric_values < color_threshold[1]] = color_threshold[1]
        segments = _metric_values_to_rays(
            contour=contour, metric_values=metric_values,
            relative=relative, origin_offset=origin_offset)
        line_segments = LineCollection(
            segments,
            linestyles='solid',
            colors=colors[0]
        )
        axes.add_collection(line_segments)


def plot_metric_on_contour(
        axes: Axes,
        contour: np.ndarray,
        metric_values: dict[str, np.ndarray],
        origin_offset: Optional[tuple[float, float]] = (0.0, 0.0),
        display_indeces: Optional[bool] = False,
        index_offset: Optional[float] = 0,
        color: Optional[str] = None) -> None:
    """
    Plot metric values on contour by changing colour of the markers.

    Parameters
    ----------
    axes : Axes
        Axes to plot on.
    contour : np.ndarray
        Contour to plot (on).
    metric_values : dict[str, np.ndarray]
        Metric values to plot.
    origin_offset : Optional[tuple[float, float]], optional
        Cartesian offset of the origin, by default (0.0, 0.0)
    display_indeces : Optional[bool], optional
        Should node indeces be displayed, by default False
    index_offset : Optional[float], optional
        Radial offset of the index texts, by default 0
    color : Optional[str], optional
        Color to display the indeces in, by default None
    """
    contour = polar_to_cartesian(contour)
    origin_offset = np.array(origin_offset).reshape((2, 1))
    contour = np.add(origin_offset, contour)

    metric_values = metric_values - np.min(metric_values)
    metric_values = metric_values/np.max(metric_values)

    for i in range(contour.shape[1]):
        axes.plot(contour[1, i], contour[0, i],
                  marker='o',
                  color=(metric_values[i], metric_values[i], metric_values[i]),
                  markeredgecolor='grey')

    if display_indeces:
        for i in range(contour.shape[1]):
            axes.text(contour[1, i]-index_offset, contour[0, i],
                      str(i+1), color=color, fontsize=12)


def display_indeces_on_contours(
        axes: Axes,
        contour1: np.ndarray,
        contour2: np.ndarray,
        outside: Optional[bool] = True,
        offset: Optional[float] = 0,
        color: Optional[str] = None,
        polar: Optional[bool] = True) -> None:
    """
    Display indeces on two contours.

    The indeces are displayed either on the inside or outside of both contours
    to avoid overlapping between the text and the contours.

    Parameters
    ----------
    axes : Axes
        Axes to plot on.
    contour1 : np.ndarray
        First contour.
    contour2 : np.ndarray
        Second contour.
    outside : Optional[bool], optional
        Should the indeces be on the outside or the inside, by default True
    offset : Optional[float], optional
        Radial offset of the index text, by default 0
    color : Optional[str], optional
        Color to use for the text, by default None
    """
    if not polar:
        contour = cartesian_to_polar(contour)

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


def plot_contour_segment(
        axes: Axes,
        contour: np.ndarray,
        index: int,
        show_index: Optional[bool] = False,
        offset: Optional[float] = 0,
        color: Optional[str] = None,
        polar: Optional[bool] = True,) -> None:
    """
    Plot a segment of the contour.

    Contour for [index-1:index+2] (two vertices +/-1 around the index) will be
    plotted.

    Parameters
    ----------
    axes : Axes
        Axes to plot on.
    contour : np.ndarray
        Contour whose segment will be plotted.
    index : int
        Index around which to plot. 
    show_index : Optional[bool], optional
        Should the index number be displayed, by default False
    offset : Optional[float], optional
        Radial offset of the center of the segment, by default 0
    color : Optional[str], optional
        Color to plot the segment in, by default None
    polar : Optional[bool], optional
        contour is in polar coordinates, by default True

    Raises
    ------
    IndexError
        If index is out of bounds of the contour.
    """
    if polar:
        contour = polar_to_cartesian(contour)

    if index == 0:
        contour_segment = contour[:, :2]
    elif index < contour.shape[1]:
        contour_segment = contour[:, index-1:index+2]
    elif index == contour.shape[1]:
        contour_segment = contour[:, index-1:]
    else:
        raise IndexError("Index out of bounds index=" + str(index) +
                         ", shape=" + str(contour.shape))

    if color:
        line = axes.plot(contour_segment[1, :],
                         contour_segment[0, :],
                         color=color)
    else:
        line = axes.plot(contour_segment[1, :],
                         contour_segment[0, :])
    color = line[0].get_color()

    if show_index:
        text_coords = polar_to_cartesian(contour[:, index] + [offset, 0])
        axes.text(text_coords[1], text_coords[0],
                  str(index+1), color=color, fontsize=12,
                  horizontalalignment='center', verticalalignment='center')


def display_fan(
        axes: Axes,
        contour: np.ndarray,
        color: Optional[str] = None,
        polar: Optional[bool] = True) -> None:
    """
    Display the radial fan for the contour.

    Parameters
    ----------
    axes : Axes
        Axes to plot on.
    contour : np.ndarray
        The contour whose fan will be plotted. However, the contour itself will
        not be plotted.
    color : Optional[str], optional
        Color to plot the fan in, by default None
    polar : Optional[bool], optional
        contour is in polar coordinates, by default True
    """
    if polar:
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
    """
    Demonstrate two contours and perturbations on the first contour.

    Parameters
    ----------
    contour_1 : np.ndarray
        Contour on both parts of the plot.
    contour_2 : np.ndarray
        Contour only on the first part of the plot.
    """
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
    _, axes = plt.subplots(1, 2, figsize=(6.4, 4.8), sharey=True,
                           gridspec_kw=gridspec_keywords)

    for ax in axes:
        ax.set_aspect('equal')
    display_fan(axes[0], contour_1)
    display_fan(axes[0], contour_2)
    display_contour(axes[0], contour_1, display_indeces=False,
                    offset=3.5, color=main_color)
    display_contour(axes[0], contour_2, display_indeces=False,
                    offset=-1, color=accent_color)
    display_indeces_on_contours(
        axes[0], contour_1, contour_2, offset=4, color=accent_color2)

    display_contour(axes[1], contour_1, color=main_color)
    perturbed_positive = contour_point_perturbations(contour_1.copy(), 2)
    perturbed_negative = contour_point_perturbations(contour_1.copy(), -2)
    for i in range(perturbed_positive.shape[0]):
        plot_contour_segment(
            axes[1], perturbed_positive[i, :, :], index=i,
            show_index=True, offset=2, color=accent_color)
        plot_contour_segment(
            axes[1], perturbed_negative[i, :, :], index=i,
            show_index=False, offset=2, color=accent_color2)

    axes[0].set_ylim((-10, 120))
    axes[1].set_ylim((-10, 120))
    axes[0].set_xlim((-70, 25))
    axes[1].set_xlim((-70, 25))

    plt.show()


def plot_distance_metric_against_perturbation_point(
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
