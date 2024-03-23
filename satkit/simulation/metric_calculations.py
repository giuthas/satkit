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
This module contains functions used to apply metrics to simulated data.
"""

from dataclasses import dataclass
from typing import Annotated, Callable, Optional

# from icecream import ic

import numpy as np

from .contour_tools import contour_point_perturbations

MetricFunction = Annotated[
    Callable[[np.ndarray], np.ndarray],
    "Metrics need to accept one np.ndarray as argument and "
    "return a np.ndarray. This is only an alias for 'Metric'"
]


@dataclass(frozen=True, eq=True)
class Comparison:
    """
    Defines a comparison between two contours: baseline and perturbed.
    """
    baseline: str
    perturbed: str

    def __repr__(self) -> str:
        return (f"Comparison: baseline={self.baseline}, "
                f"perturbed={self.perturbed}")


def get_dyadic_metric_baseline(
        metric: MetricFunction,
        contour_1: np.ndarray,
        contour_2: np.ndarray) -> np.ndarray:
    """
    Get the metric comparing contour_1 to contour_2 and vice versa.

    Parameters
    ----------
    metric : MetricFunction
        The metric function. Should accept a 2D np.ndarray as its argument and
        return an np.ndarray. This can be generated with functools.partial from
        standard SATKIT metrics.        
    contour_1 : np.ndarray
        First contour.
    contour_2 : np.ndarray
        Second contour.

    Returns
    -------
    np.ndarray
        This array has only two values: the value of metric when comparing
        contour_1 to contour_2, and vice versa.
    """
    baseline_stack = np.stack([contour_1, contour_2, contour_1])
    return metric(baseline_stack)


def calculate_perturbed_metric_series(
        metric: MetricFunction,
        contour_to_perturb: np.ndarray,
        reference_contour: Optional[np.ndarray] = None,
        perturbations: Optional[tuple[float]] = (1.0),
        interleave: Optional[bool] = False
) -> dict[str, np.ndarray]:
    """
    Generate a series of perturbed contours and calculate the metric on them.

    This function is usually not called directly but only implicitly by
    calculate_metric_series_for_contours and
    calculate_metric_series_for_comparisons.

    Parameters
    ----------
    metric : MetricFunction
        The metric function. Should accept a 2D np.ndarray as its argument and
        return an np.ndarray. This can be generated with functools.partial from
        standard SATKIT metrics.
    contour_to_perturb : np.ndarray
        The contour the perturbations will be applied to.
    reference_contour : Optional[np.ndarray], optional
        A reference contour to compare the perturbed ones with. If None, the
        contour_to_perturb will be used instead. By default None
    perturbations : Optional[tuple[float]], optional
        Tuple of perturbations to apply in absolute r values, by default (1.0)
    interleave : Optional[bool], optional
        Should the reference contour be interleaved with the perturbed
        contours. Use this for pairwise metrics like ANND or MPBPD when
        comparisons with baseline are wanted. By default False

    Returns
    -------
    dict[str, np.ndarray]
        A dictionary of the results. Keys are the perturbation values and
        values are the series resulting from applying the metric with one value
        for each application.
    """
    results = {}
    for perturbation in perturbations:
        perturbed = contour_point_perturbations(
            contour_to_perturb.copy(),
            reference_contour,
            perturbation,
            interleave=interleave
        )
        results[perturbation] = metric(
            perturbed
        )
    return results


def calculate_metric_series_for_contours(
        metric: MetricFunction,
        contours: dict[str, np.ndarray],
        perturbations: Optional[tuple[float]] = (1.0)
) -> dict[str, dict[str, np.ndarray]]:
    """
    Calculate the metric for each contour while perturbing each point.

    Parameters
    ----------
    metric : MetricFunction
        The metric to calculate.
    contours : dict[str, np.ndarray]
        A dict of the contours.
    perturbations : Optional[tuple[float]], optional
        A tuple of perturbations to apply, by default (1.0)

    Returns
    -------
    dict[str, dict[str, np.ndarray]]
        The outer dictionary's keys are same as those in contours, the inner
        dictionary's keys are perturbation values.
    """
    result_dicts = {}
    for contour_key in contours:
        result_dicts[contour_key] = calculate_perturbed_metric_series(
            metric=metric,
            contour_to_perturb=contours[contour_key],
            reference_contour=contours[contour_key],
            perturbations=perturbations,
            interleave=True
        )
    return result_dicts


def calculate_metric_series_for_comparisons(
        metric: MetricFunction,
        contours: dict[str, np.ndarray],
        comparisons: list[Comparison],
        perturbations: Optional[list[float]] = (1.0),
        interleave: Optional[bool] = True
) -> dict[Comparison, dict[str, np.ndarray]]:
    """
    Calculate the metric between the specified comparisons.

    The comparisons define a contour to use as is or as a baseline and a
    contour to run perturbations on. They may be the same contour, in which
    case the comparison is between the baseline and its perturbed versions.

    Parameters
    ----------
    metric : MetricFunction
        The metric function to apply.
    contours : dict[str, np.ndarray]
        The contours to run the metric on.
    comparisons : list[Comparison]
        List of which contours to compare with which.
    perturbations : Optional[list[float]], optional
        Tuple of perturbation sizes to apply, by default (1.0)

    Returns
    -------
    dict[Comparison, dict[str, np.ndarray]]
        The outer dictionary is indexed with the Comparisons made and the inner
        one with the original keys of the contours dictionary.
    """
    result_dicts = {}
    for comparison in comparisons:
        result_dicts[comparison] = calculate_perturbed_metric_series(
            metric=metric,
            contour_to_perturb=contours[comparison.perturbed],
            reference_contour=contours[comparison.baseline],
            perturbations=perturbations,
            interleave=interleave
        )
    return result_dicts
