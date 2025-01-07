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
This package is for simulating data and plotting simulation results.

Currently, it deals with only simulated tongue contour data.
"""
from .contour_tools import (
    SimulationContourConsonant, SimulationContourVowel,
    SimulationContourSoundEnum,
    generate_contour, contour_point_perturbations
)
from .metric_calculations import (
    Comparison, ComparisonMember, ComparisonSoundPair, MetricFunction,
    calculate_metric_series_for_comparisons,
    calculate_metric_series_for_contours,
    get_distance_metric_baselines,
    get_shape_metric_baselines
)

from .simulation_plots import (
    display_contour, display_fan, display_indeces_on_contours,
    plot_contour_segment, make_demonstration_contour_plot,
    plot_metric_on_contour, contour_ray_plot,
    plot_distance_metric_against_perturbation_point
)

from .rays_on_contours import (
    distance_metric_rays_on_contours,
    shape_metric_rays_on_contours
)

from .perturbation_series_plots import (
    annd_perturbation_series_like_to_like_plot,
    annd_perturbation_series_crosswise_plot,
    mci_perturbation_series_plot
)
