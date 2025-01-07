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
Perturbation series plots.
"""

from typing import Optional

import numpy as np

import matplotlib.pyplot as plt

from satkit.metrics.spline_metric import SplineShapesEnum
from satkit.metrics.tongue_shape_analysis import spline_shape_metric
from satkit.plot_and_publish.plot_utilities import get_colors_in_sequence

from .contour_tools import contour_point_perturbations
from .metric_calculations import Comparison, ComparisonSoundPair
from .simulation_plots import plot_distance_metric_against_perturbation_point


def annd_perturbation_series_like_to_like_plot(
        annd_dict: dict[Comparison, dict[str, np.ndarray]],
        columns: list[str],
) -> None:
    """
    Make the first part of the perturbation series plot for ANND.

    This part is the like-to-like plots: each contour to its own perturbed
    version or vice versa.

    Parameters
    ----------
    annd_dict : dict[Comparison, dict[str, np.ndarray]]
        ANND analysis results by Comparisons and perturbations.
    columns : list[str]
        Order of contours to go through. Used to access the results from
        annd_dict.
    """
    plt.style.use('tableau-colorblind10')
    colors = get_colors_in_sequence(6)

    gridspec_keywords = {
        'wspace': 0.0,
        'hspace': 0.0,
        # 'top': .95,
        # 'bottom': 0.05,
    }
    _, axes = plt.subplots(nrows=2, ncols=len(columns),
                           figsize=(12, 3),
                           sharex=True, sharey='row',
                           gridspec_kw=gridspec_keywords)

    filtered_annd_dict = {key.first: annd_dict[key]
                          for key in annd_dict if key.first == key.second}

    for i, sound in enumerate(columns):
        (lines, labels) = plot_distance_metric_against_perturbation_point(
            axes[0:2, i], filtered_annd_dict[sound], colors=colors)

        axes[0, i].set_title(f"ANND: [{sound}] to itself")
        axes[1, i].set_xlabel("Point of perturbation")
        axes[0, i].axhline(0, linestyle=":", color="lightgray")
        axes[1, i].axhline(0, linestyle=":", color="lightgray")

    axes[0, 0].set_ylabel("Baseline\nto perturbed")
    axes[1, 0].set_ylabel("Perturbed\nto baseline")

    axes[0, len(columns)-1].legend(lines, labels, bbox_to_anchor=(
        1, 0.6), loc="upper left")


def annd_perturbation_series_crosswise_plot(
    annd_dict: dict[Comparison, dict[str, np.ndarray]],
    annd_baseline: np.ndarray,
    columns: list[ComparisonSoundPair]
) -> None:
    """
    Make the first part of the perturbation series plot for ANND.

    Parameters
    ----------
    annd_dict : dict[Comparison, dict[str, np.ndarray]]
        ANND analysis results by Comparisons and perturbations.
    annd_baseline : np.ndarray
        baselines for the ANND comparisons.
    columns : list[ComparisonSoundPair]
        Order of contour pairs to go through. Used to access the results from
        annd_dict.
    """
    plt.style.use('tableau-colorblind10')
    colors = get_colors_in_sequence(6)

    gridspec_keywords = {
        'wspace': 0.0,
        'hspace': 0.0,
        # 'top': .95,
        # 'bottom': 0.05,
    }
    _, axes = plt.subplots(2, 2, figsize=(12, 3),
                           sharex=True, sharey='row',
                           gridspec_kw=gridspec_keywords)

    filtered_annd_dict = {
        ComparisonSoundPair(first=key.first, second=key.second): annd_dict[key]
        for key in annd_dict if key.first != key.second}

    for i, sound_pair in enumerate(columns):
        (lines, labels) = plot_distance_metric_against_perturbation_point(
            axes[:, i], filtered_annd_dict[sound_pair], colors=colors)

        axes[0, i].set_ylabel(
            f"ANND: [{sound_pair.first}] to [{sound_pair.second}]")
        axes[1, i].set_xlabel("Point of perturbation")
        axes[0, i].axhline(annd_baseline[1], linestyle=":", color="lightgray")
        axes[1, i].axhline(annd_baseline[0], linestyle=":", color="lightgray")

    axes[0, 0].set_ylabel("Baseline\nto perturbed")
    axes[1, 0].set_ylabel("Perturbed\nto baseline")

    axes[0, len(columns)-1].legend(lines, labels, bbox_to_anchor=(
        1, 0.6), loc="upper left")


def mci_perturbation_series_plot(
        contours: dict[str, np.ndarray],
        figsize: tuple[float, float],
        perturbations: Optional[list[float]] = (1.0),
) -> None:
    """
    Make a perturbation series plot for MCI.

    Parameters
    ----------
    contours : dict[str, np.ndarray]
        Contours by name to plot the metrics on.
    figsize : tuple[float, float]
        size of the figure
    perturbations : Optional[list[float]], optional
        perturbation values to use, by default (1.0)
    """
    plt.style.use('tableau-colorblind10')
    gridspec_keywords = {
        'wspace': 0.0,
        'hspace': 0.0,
        # 'left': .05
        # 'top': .95,
        # 'bottom': 0.05,
    }
    figure, axes = plt.subplots(nrows=len(perturbations),
                                ncols=len(contours),
                                figsize=figsize,
                                sharex=True, sharey=True,
                                gridspec_kw=gridspec_keywords)

    ref_mci = [0, 0]

    for j, contour_name in enumerate(contours):
        for i, perturbation in enumerate(perturbations):
            perturbed = contour_point_perturbations(
                contour=contours[contour_name].copy(),
                perturbation=perturbation,
                interleave=False)

            data = np.append(np.expand_dims(
                contours[contour_name], 0), perturbed, axis=0)
            mci = spline_shape_metric(
                data,
                metric=SplineShapesEnum.MODIFIED_CURVATURE,
                notice_base="MCI simulation: "
            )

            ref_mci[0] = mci[0]
            ratio = mci[1:]/mci[0]
            perturbation_points = list(range(1, ratio.shape[0]+1))

            label = f'perturbation={perturbation}'
            line = axes[i, j].plot(perturbation_points, ratio,
                                   label=label)[0]
            axes[i, j].legend(
                [line], [label],
                loc='upper right',
                handlelength=0,
                handletextpad=0)
        axes[0, j].set_title(
            f"Change in MCI for [{contour_name}] relative to {mci[0]:.1f}")

    figure.text(0.05, 0.5, r"log$_{10}$(Perturbed MCI / Reference MCI)",
                ha="center", va="center", rotation=90)

    for i in range(len(contours)):
        axes[-1, i].set_xlabel("Point of perturbation")

    for ax in axes.flatten():
        ax.set_yscale("log")
        ax.axhline(2, linestyle="--", color="lightgray")
        ax.axhline(.5, linestyle="--", color="lightgray")
        ax.axhline(1, linestyle=":", color="lightgray")
