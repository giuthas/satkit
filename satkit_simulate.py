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
Simulate data and run metrics on it with plotting.

Original version for Ultrafest 2024.
"""

from functools import partial
from pathlib import Path
from typing import Optional

# from icecream import ic

import numpy as np

from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar

from satkit.metrics import (
    SplineNNDsEnum, SplineShapesEnum
)
from satkit.metrics.calculate_spline_metric import (
    # spline_diff_metric,
    spline_nnd_metric, spline_shape_metric
)

from satkit.simulation import (
    Comparison, ComparisonMember,
    generate_contour, contour_point_perturbations,
    calculate_metric_series_for_comparisons,
    calculate_metric_series_for_contours,
    # display_fan,
    display_contour,
    get_distance_metric_baselines,
    get_shape_metric_baselines,
    # make_demonstration_contour_plot,
    # plot_metric_on_contour,
    contour_ray_plot,
    plot_distance_metric_against_perturbation_point
)


def get_colors_in_sequence(number: int) -> list[str]:
    """
    Not fully implemented!

    Get colors in a perceptual sequence.

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
    if number == 6:
        colors = sorted(colors)
        colors = [colors[0], colors[2], colors[1],
                  colors[3], colors[5], colors[4]]
    return colors


def make_annd_perturbation_series_plot(
        annd_dict: dict[Comparison, dict[str, np.ndarray]],
        pdf: PdfPages
) -> None:
    """
    Make the first part of the perturbation series plot for ANND.

    Parameters
    ----------
    annd_dict : dict[Comparison, dict[str, np.ndarray]]
        ANND analysis results by Comparisons and perturbations.
    pdf : PdfPages
        pdf to write the plot into.
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

    for comparison in annd_dict:
        if comparison.first == 'ae' and comparison.second == 'ae':
            (lines, labels) = plot_distance_metric_against_perturbation_point(
                axes[0:2, 0], annd_dict[comparison], colors=colors)
        elif comparison.first == 'i' and comparison.second == 'i':
            plot_distance_metric_against_perturbation_point(
                axes[0:2, 1], annd_dict[comparison], colors=colors)
    axes[0, 0].set_title("ANND: [æ] to itself")
    axes[0, 0].set_ylabel("Baseline\nto perturbed")
    axes[1, 0].set_ylabel("Perturbed\nto baseline")

    axes[0, 1].set_title("ANND: [i] to itself")

    axes[1, 0].set_xlabel("Point of perturbation")
    axes[1, 1].set_xlabel("Point of perturbation")

    axes[0, 0].axhline(0, linestyle=":", color="lightgray")
    axes[1, 0].axhline(0, linestyle=":", color="lightgray")
    axes[0, 1].axhline(0, linestyle=":", color="lightgray")
    axes[1, 1].axhline(0, linestyle=":", color="lightgray")

    axes[0, 1].legend(lines, labels, bbox_to_anchor=(
        1, 0.6), loc="upper left")

    # plt.show()

    plt.tight_layout()
    pdf.savefig(plt.gcf())


def make_annd_perturbation_series_plot_2(
        annd_dict: dict[Comparison, dict[str, np.ndarray]],
        annd_baseline: np.ndarray,
        pdf: PdfPages
) -> None:
    """
    Make the first part of the perturbation series plot for ANND.

    Parameters
    ----------
    annd_dict : dict[Comparison, dict[str, np.ndarray]]
        ANND analysis results by Comparisons and perturbations.
    annd_baseline : np.ndarray
        baselines for the ANND comparisons.
    pdf : PdfPages
        pdf to write the plot into.
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

    for comparison in annd_dict:
        if comparison.first == 'ae' and comparison.second == 'i':
            (lines, labels) = plot_distance_metric_against_perturbation_point(
                axes[::-1, 1], annd_dict[comparison], colors=colors)
        elif comparison.first == 'i' and comparison.second == 'ae':
            plot_distance_metric_against_perturbation_point(
                axes[:, 0], annd_dict[comparison], colors=colors)

    axes[0, 0].set_ylabel("[æ] to [i]")
    axes[1, 0].set_ylabel("[i] to [æ]")

    axes[0, 0].set_title("ANND: perturbed [æ]")
    axes[0, 1].set_title("ANND: Perturbed [i]")

    axes[1, 0].set_xlabel("Point of perturbation")
    axes[1, 1].set_xlabel("Point of perturbation")

    axes[0, 0].axhline(annd_baseline[1], linestyle=":", color="lightgray")
    axes[1, 0].axhline(annd_baseline[0], linestyle=":", color="lightgray")
    axes[0, 1].axhline(annd_baseline[1], linestyle=":", color="lightgray")
    axes[1, 1].axhline(annd_baseline[0], linestyle=":", color="lightgray")

    axes[0, 1].legend(lines, labels, bbox_to_anchor=(
        1, 0.6), loc="upper left")
    plt.tight_layout()
    pdf.savefig(plt.gcf())


def make_mci_perturbation_series_plot(
        contour_1: np.ndarray,
        contour_2: np.ndarray,
        perturbations: Optional[list[float]] = (1.0)
) -> None:
    """
    Make a perturbation series plot for MCI.

    Parameters
    ----------
    contour_1 : np.ndarray
        First contour.
    contour_2 : np.ndarray
        Second contour.
    perturbations : Optional[list[float]], optional
        perturbation values to use, by default (1.0)
    """
    plt.style.use('tableau-colorblind10')

    gridspec_keywords = {
        'wspace': 0.0,
        'hspace': 0.0,
        # 'top': .95,
        # 'bottom': 0.05,
    }
    figure, axes = plt.subplots(2, 2, figsize=(12, 3),
                                sharex=True, sharey='row',
                                gridspec_kw=gridspec_keywords)

    ref_mci = [0, 0]

    lines = []
    labels = []
    for step in perturbations:
        perturbed = contour_point_perturbations(
            contour_1.copy(), step, interleave=False)
        data = np.append(np.expand_dims(contour_1, 0), perturbed, axis=0)
        mci = spline_shape_metric(
            data,
            metric=SplineShapesEnum.MODIFIED_CURVATURE,
            notice_base="ISSP 2024 simulation: "
        )

        ref_mci[0] = mci[0]
        diff = mci[1:]/mci[0]
        time = list(range(1, diff.shape[0]+1))

        if abs(step) < 1.5:
            axes[0, 0].plot(time, diff,
                            label='perturbation=' + str(step))
        lines.append(
            axes[1, 0].plot(time, diff,
                            label='perturbation=' + str(step))[0])
        labels.append(f"perturbation={step}")
    axes[0, 0].set_title(f"Change in MCI for [æ] relative to {mci[0]:.1f}")

    for step in perturbations:
        perturbed = contour_point_perturbations(
            contour_2.copy(), step, interleave=False)
        data = np.append(np.expand_dims(contour_2, 0), perturbed, axis=0)
        mci = spline_shape_metric(
            data,
            metric=SplineShapesEnum.MODIFIED_CURVATURE,
            notice_base="ISSP 2024 simulation: "
        )

        ref_mci[1] = mci[1]
        diff = mci[1:]/mci[0]
        time = list(range(1, diff.shape[0]+1))

        if abs(step) < 1.5:
            axes[0, 1].plot(time, diff,
                            label='perturbation=' + str(step))
        axes[1, 1].plot(time, diff,
                        label='perturbation=' + str(step))
    axes[0, 1].set_title(f"Change in MCI for [i] relative to {mci[0]:.1f}")

    axes[0, 0].axhline(2, linestyle="--", color="lightgray")
    axes[1, 0].axhline(2, linestyle="--", color="lightgray")
    axes[0, 1].axhline(2, linestyle="--", color="lightgray")
    axes[1, 1].axhline(2, linestyle="--", color="lightgray")

    axes[0, 0].axhline(.5, linestyle="--", color="lightgray")
    axes[1, 0].axhline(.5, linestyle="--", color="lightgray")
    axes[0, 1].axhline(.5, linestyle="--", color="lightgray")
    axes[1, 1].axhline(.5, linestyle="--", color="lightgray")

    axes[0, 0].axhline(1, linestyle=":", color="lightgray")
    axes[1, 0].axhline(1, linestyle=":", color="lightgray")
    axes[0, 1].axhline(1, linestyle=":", color="lightgray")
    axes[1, 1].axhline(1, linestyle=":", color="lightgray")

    axes[0, 0].set_ylabel("Perturbed MCI / Reference MCI")
    axes[1, 0].set_ylabel("Perturbed MCI / Reference MCI")

    axes[1, 0].set_xlabel("Point of perturbation")
    axes[1, 1].set_xlabel("Point of perturbation")
    axes[1, 0].set_yscale("log")
    axes[0, 0].set_yscale("log")

    figure.legend(lines, labels, loc='outside right center')

    plt.show()

    figure.savefig("ultrafest2024/mci_full.png",
                   bbox_inches='tight')


def contours_with_distance_metric(
    contours: dict[str, np.ndarray],
    metrics: dict[Comparison, dict[str, np.ndarray]],
    metric_name: str,
    baselines: dict[Comparison, float],
    number_of_perturbations: int,
    pdf: PdfPages,
    figsize=tuple[float, float],
    nrows: Optional[int] = 2,
    contour_rows: Optional[int] = 2,
    scale: Optional[float] = 1
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
    """
    plt.style.use('tableau-colorblind10')

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

    axes[0, 0].set_title(f"[æ] to [æ], {metric_name} = 0")
    axes[0, 1].set_title(f"[i] to [i], {metric_name} = 0")
    reference = baselines[Comparison(
        first='ae', second='i', perturbed=ComparisonMember.FIRST)]
    axes[0, 2].set_title(f"[æ] to [i], {metric_name} = {reference[0]:.2f}")
    reference = baselines[Comparison(
        first='i', second='ae', perturbed=ComparisonMember.FIRST)]
    axes[0, 3].set_title(f"[i] to [æ], {metric_name} = {reference[0]:.2f}")

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
                        origin_offset=origin_offset)
                else:
                    contour_ray_plot(
                        axes=axes[row, column],
                        contour=contours[comparison.first],
                        metric_values=metric_dict[perturbation],
                        metric_reference_value=baseline,
                        scale=scale,
                        origin_offset=origin_offset)
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
                        relative=False)
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
                        relative=False)
    # plt.colorbar()
    # plt.show()
    plt.tight_layout()
    pdf.savefig(plt.gcf())


def contours_with_shape_metric(
    contours: dict[str, np.ndarray],
    metrics: dict[str, dict[str, np.ndarray]],
    metric_name: str,
    baselines: dict[str, float],
    number_of_perturbations: int,
    pdf: PdfPages,
    figsize: tuple[float, float],
    nrows: Optional[int] = 1,
    contour_rows: Optional[int] = 2,
    scale: Optional[float] = 1
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
    """
    plt.style.use('tableau-colorblind10')

    gridspec_keywords = {
        'wspace': 0.0,
        'hspace': 0.0,
        # 'top': .95,
        # 'bottom': 0.05,
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
            size=10*scale, label=f'10 {metric_name}',
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

    reference = baselines['ae']
    axes[0].set_title(f"[æ], {metric_name} = {reference[0]:.2f}")
    reference = baselines['i']
    axes[1].set_title(f"[i], {metric_name} = {reference[0]:.2f}")

    axes[0].set_ylabel("MCI baseline / MCI perturbed")

    for j, contour_name in enumerate(metrics):
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
                relative=True)
    # plt.colorbar()
    # plt.show()
    plt.tight_layout()
    pdf.savefig(plt.gcf())


def main() -> None:
    """
    Main to create plots for the Ultrafest 2024 paper.
    """
    save_path = Path("ultrafest2024/")
    if not save_path.exists():
        save_path.mkdir()

    sounds = ['ae', 'i']
    contours = {
        sound: generate_contour(sound) for sound in sounds
    }

    # make_demonstration_contour_plot(
    #     contour_1=contours['ae'], contour_2=contours['i'])

    perturbations = [-2, -1, -.5, .5, 1, 2]
    # perturbations = [-2, -1, -.5, -.25, .25, .5, 1, 2]
    annd_call = partial(spline_nnd_metric,
                        metric=SplineNNDsEnum.ANND,
                        timestep=1,
                        notice_base="ISSP 2024 simulation: "
                        )
    comparisons = [
        Comparison(first='ae', second='ae', perturbed='second'),
        Comparison(first='ae', second='ae', perturbed='first'),
        Comparison(first='i', second='i', perturbed='second'),
        Comparison(first='i', second='i', perturbed='first'),
        Comparison(first='ae', second='i', perturbed='second'),
        Comparison(first='ae', second='i', perturbed='first'),
        Comparison(first='i', second='ae', perturbed='second'),
        Comparison(first='i', second='ae', perturbed='first'),
    ]
    annd_results = calculate_metric_series_for_comparisons(
        metric=annd_call,
        contours=contours,
        comparisons=comparisons,
        perturbations=perturbations,
        interleave=True
    )
    annd_baselines = get_distance_metric_baselines(
        metric=annd_call, contours=contours)

    mci_call = partial(spline_shape_metric,
                       metric=SplineShapesEnum.MODIFIED_CURVATURE,
                       notice_base="ISSP 2024 simulation: "
                       )
    mci_results = calculate_metric_series_for_contours(
        metric=mci_call,
        contours=contours,
        perturbations=perturbations
    )
    mci_baselines = get_shape_metric_baselines(
        metric=mci_call,
        contours=contours,
    )

    with PdfPages(save_path/"annd_contours.pdf") as pdf:
        contours_with_distance_metric(contours=contours,
                                      metrics=annd_results,
                                      metric_name="ANND",
                                      baselines=annd_baselines,
                                      number_of_perturbations=len(
                                          perturbations),
                                      pdf=pdf,
                                      figsize=(10.1, 4.6),
                                      scale=200)

    with PdfPages(save_path/"mci_contours.pdf") as pdf:
        contours_with_shape_metric(contours=contours,
                                   metrics=mci_results,
                                   metric_name="MCI/Baseline MCI",
                                   baselines=mci_baselines,
                                   number_of_perturbations=len(
                                       perturbations),
                                   pdf=pdf,
                                   figsize=(7, 3.3),
                                   scale=1)

    # with PdfPages(save_path/"annd_1.pdf") as pdf:
    #     make_annd_perturbation_series_plot(annd_dict=annd_results, pdf=pdf)
    # with PdfPages(save_path/"annd_2.pdf") as pdf:
    #     make_annd_perturbation_series_plot_2(annd_dict=annd_results,
    #                                          annd_baseline=annd_baseline,
    #                                          pdf=pdf)
    # make_mpbpd_perturbation_series_plot(contour_1=contours['ae'],
    #                                     contour_2=contours['i'],
    #                                     steps=[1, 2, 5, 10])
    # make_mci_perturbation_series_plot(contour_1=contours['ae'],
    #                                   contour_2=contours['i'],
    #                                   steps=perturbations)


if __name__ == '__main__':
    main()
