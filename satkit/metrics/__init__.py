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
from .ofreg import of
from .calculate_aggregate_images import add_aggregate_images
from .calculate_distance_matrices import add_distance_matrices
from .calculate_pd import add_pd
from .calculate_spline_metric import add_spline_metric

from .downsample_metric import downsample_metrics_in_session, downsample_metrics

from .aggregate_image import AggregateImage, AggregateImageParameters
from .distance_matrix import DistanceMatrix, DistanceMatrixParameters
from .pd import PD, PdParameters, ImageMask
from .spline_metric import (SplineMetric, SplineMetricParameters,
                            SplineDiffsEnum, SplineNNDsEnum, SplineShapesEnum)

# TODO: Decide if it is worth it to use typing.Annotated to document this
# metrics is a mapping between a modality name and its actual type and the
# validator model for its parameters.
metrics = {
    'PD': (PD, PdParameters),
    'SplineMetric': (SplineMetric, SplineMetricParameters),
}

statistics = {
    'AggregateImage': (AggregateImage, AggregateImageParameters),
    'DistanceMatrix': (DistanceMatrix, DistanceMatrixParameters),
}