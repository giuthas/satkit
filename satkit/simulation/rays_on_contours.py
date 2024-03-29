#!/usr/bin/env python3
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
"""
Plot metric rays on contours for different perturbations.
"""

from typing import Optional

# from icecream import ic

import numpy as np

from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar

from satkit.plot_and_publish.plot_utilities import get_colors_in_sequence
from satkit.simulation import (
    Comparison, ComparisonMember,
    display_contour,
    contour_ray_plot,
)


def distance_metric_rays_on_contours(
    contours: dict[str, np.ndarray],
    metrics: dict[Comparison, dict[str, np.ndarray]],
    metric_name: str,
    baselines: dict[Comparison, float],
    number_of_perturbations: int,
    pdf: PdfPages,
    figsize=tuple[float, float],
    nrows: Optional[int] = 2,
    contour_rows: Optional[int] = 2,
    scale: Optional[float] = 1,
    color_threshold: Optional[list[float]] = None,
) -> None:
    """
    Plot a distance metric values on contours.

    Parameters
    ----------
    contours : dict[str, np.ndarray]
        Contours by name to plot the metrics on.
    metrics : dict[str, dict[str, np.ndarray]]
        Metric values to plot, by contour name and perturbation value.
    metric_name : str
        Name of the metric to be plotted.
    baselines : dict[str, float]
        Baseline values for each contour.
    number_of_perturbations : int
        How many perturbation values there are.
    pdf : PdfPages
        pdf to plot into.
    figsize : tuple[float, float]
        size of the figure
    nrows : Optional[int], optional
        number of subplot rows in the plot, by default 1
    contour_rows : Optional[int], optional
        number of contour rows in the subplots, by default 2
    scale : Optional[float], optional
        Scaling factor for the metric values, by default 1
    color_threshold :  Optional[float]
        Threshold to switch from the first to the second color in plotting the
        rays. Specified in metric's units relative to the
        `metric_reference_value`, by default None
    """
    # TODO once Comparisons are sortable, clean this function.
    plt.style.use('tableau-colorblind10')
    if color_threshold is not None:
        colors = get_colors_in_sequence(2)

    gridspec_keywords = {
        'wspace': 0.0,
        'hspace': 0.0,
        # 'top': .95,
        # 'bottom': 0.05,
    }

    comparisons = metrics.keys()
    ncols = len(comparisons)//nrows
    _, axes = plt.subplots(nrows=nrows,
                           ncols=ncols,
                           figsize=figsize,
                           sharey=True,
                           sharex=True,
                           gridspec_kw=gridspec_keywords)

    for ax in axes.flatten():
        ax.set_aspect('equal')
        ax.set_yticks([])
        ax.set_xticks([])
        font_properties = fm.FontProperties(size=9)
        scale_bar = AnchoredSizeBar(
            ax.transData,
            size=.1*scale, label=f'0.1 {metric_name}',
            loc='upper left',
            pad=.5,
            color=plt.rcParams['axes.prop_cycle'].by_key()['color'][0],
            frameon=False,
            size_vertical=1,
            label_top=True,
            fontproperties=font_properties)
        ax.add_artist(scale_bar)
        # ax.set_xlim([-80, 250])
        # ax.set_ylim([-10, 250])

    # axes[0, 0].set_title(f"[æ] to [æ], {metric_name} = 0")
    axes[0, 0].set_title("[æ] to [æ]")
    axes[1, 0].set_xlabel(f"{metric_name} = 0")
    # axes[0, 1].set_title(f"[i] to [i], {metric_name} = 0")
    axes[0, 1].set_title("[i] to [i]")
    axes[1, 1].set_xlabel(f"{metric_name} = 0")

    reference = baselines[Comparison(
        first='æ', second='i', perturbed=ComparisonMember.FIRST)]
    # axes[0, 2].set_title(f"[æ] to [i], {metric_name} = {reference[0]:.2f}")
    axes[0, 2].set_title("[æ] to [i]")
    axes[1, 2].set_xlabel(f"{metric_name} = {reference[0]:.2f}")

    reference = baselines[Comparison(
        first='i', second='æ', perturbed=ComparisonMember.FIRST)]
    # axes[0, 3].set_title(f"[i] to [æ], {metric_name} = {reference[0]:.2f}")
    axes[0, 3].set_title("[i] to [æ]")
    axes[1, 3].set_xlabel(f"{metric_name} = {reference[0]:.2f}")

    axes[0, 0].set_ylabel("baseline to perturbed")
    axes[1, 0].set_ylabel("perturbed to baseline")

    for j, comparison in enumerate(metrics):
        row = j % nrows
        column = j//nrows
        metric_dict = metrics[comparison]
        baseline = baselines[comparison]
        for i, perturbation in enumerate(metric_dict):
            p_row = i // (number_of_perturbations//contour_rows)
            p_column = i % (number_of_perturbations//contour_rows)
            origin_offset = np.array([0+125*p_row, 0+100*p_column])
            axes[row, column].text(
                origin_offset[1]-10, origin_offset[0]-15,
                f"{perturbation} mm",
                horizontalalignment='center',)
            if comparison.first == comparison.second:
                if comparison.perturbed == ComparisonMember.SECOND:
                    contour_ray_plot(
                        axes=axes[row, column],
                        contour=contours[comparison.first],
                        metric_values=metric_dict[perturbation],
                        metric_reference_value=baseline,
                        scale=scale,
                        origin_offset=origin_offset,
                        color_threshold=color_threshold,
                        colors=colors,)
                else:
                    contour_ray_plot(
                        axes=axes[row, column],
                        contour=contours[comparison.first],
                        metric_values=metric_dict[perturbation],
                        metric_reference_value=baseline,
                        scale=scale,
                        origin_offset=origin_offset,
                        color_threshold=color_threshold,
                        colors=colors,)
            else:
                if comparison.perturbed == ComparisonMember.SECOND:
                    display_contour(
                        axes[row, column],
                        contours[comparison.first],
                        origin_offset=origin_offset,
                        color='lightgrey')
                    contour_ray_plot(
                        axes=axes[row, column],
                        contour=contours[comparison.second],
                        metric_values=metric_dict[perturbation],
                        metric_reference_value=baseline,
                        scale=scale,
                        origin_offset=origin_offset,
                        relative=False,
                        color_threshold=color_threshold,
                        colors=colors,)
                else:
                    display_contour(
                        axes[row, column],
                        contours[comparison.second],
                        origin_offset=origin_offset,
                        color='lightgrey')
                    contour_ray_plot(
                        axes=axes[row, column],
                        contour=contours[comparison.first],
                        metric_values=metric_dict[perturbation],
                        metric_reference_value=baseline,
                        scale=scale,
                        origin_offset=origin_offset,
                        relative=False,
                        color_threshold=color_threshold,
                        colors=colors,)
    # plt.colorbar()
    # plt.show()
    plt.tight_layout()
    pdf.savefig(plt.gcf())


def shape_metric_rays_on_contours(
    contours: dict[str, np.ndarray],
    metrics: dict[str, dict[str, np.ndarray]],
    metric_name: str,
    baselines: dict[str, float],
    number_of_perturbations: int,
    pdf: PdfPages,
    figsize: tuple[float, float],
    nrows: Optional[int] = 1,
    contour_rows: Optional[int] = 2,
    scale: Optional[float] = 1,
    color_threshold: Optional[list[float]] = None,
) -> None:
    """
    Plot shape metric values on contours.

    Parameters
    ----------
    contours : dict[str, np.ndarray]
        Contours by name to plot the metrics on.
    metrics : dict[str, dict[str, np.ndarray]]
        Metric values to plot, by contour name and perturbation value.
    metric_name : str
        Name of the metric to be plotted.
    baselines : dict[str, float]
        Baseline values for each contour.
    number_of_perturbations : int
        How many perturbation values there are.
    pdf : PdfPages
        pdf to plot into.
    figsize : tuple[float, float]
        size of the figure
    nrows : Optional[int], optional
        number of subplot rows in the plot, by default 1
    contour_rows : Optional[int], optional
        number of contour rows in the subplots, by default 2
    scale : Optional[float], optional
        Scaling factor for the metric values, by default 1
    color_threshold :  Optional[float]
        Threshold to switch from the first to the second color in plotting the
        rays. Specified in metric's units relative to the
        `metric_reference_value`, by default None
    """
    plt.style.use('tableau-colorblind10')
    if color_threshold is not None:
        colors = get_colors_in_sequence(2)

    gridspec_keywords = {
        'wspace': 0.0,
        'hspace': 0.0,
    }

    contour_names = metrics.keys()
    ncols = len(contour_names)
    _, axes = plt.subplots(nrows=nrows,
                           ncols=ncols,
                           figsize=figsize,
                           sharey=True,
                           sharex=True,
                           gridspec_kw=gridspec_keywords)

    for ax in axes.flatten():
        ax.set_aspect('equal')
        ax.set_yticks([])
        ax.set_xticks([])
        font_properties = fm.FontProperties(size=9)
        scale_bar = AnchoredSizeBar(
            ax.transData,
            size=scale*np.log10(2), label='log10(2)',
            loc='upper left',
            pad=.5,
            color=plt.rcParams['axes.prop_cycle'].by_key()['color'][0],
            frameon=False,
            size_vertical=1,
            label_top=True,
            fontproperties=font_properties)
        ax.add_artist(scale_bar)

    for j, contour_name in enumerate(metrics):
        reference = baselines[contour_name]
        axes[j].set_title(f"[{contour_name}]")
        axes[j].set_xlabel(f"{metric_name} = {reference[0]:.2f}")
        metric_dict = metrics[contour_name]
        baseline = baselines[contour_name]
        for i, perturbation in enumerate(metric_dict):
            p_row = i // (number_of_perturbations//contour_rows)
            p_column = i % (number_of_perturbations//contour_rows)
            origin_offset = np.array([0+125*p_row, 0+100*p_column])
            axes[j].text(
                origin_offset[1]-10, origin_offset[0]+25,
                f"{perturbation} mm",
                horizontalalignment='center',)
            contour_ray_plot(
                axes=axes[j],
                contour=contours[contour_name],
                metric_values=metric_dict[perturbation],
                metric_reference_value=baseline,
                scale=scale,
                origin_offset=origin_offset,
                relative=True,
                color_threshold=color_threshold,
                colors=colors,)
    plt.tight_layout()
    pdf.savefig(plt.gcf())
