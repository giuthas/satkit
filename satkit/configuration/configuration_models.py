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
These are the code friendly wrappers for the configuration structures.

configuration_parsers contains the actual parsing of strictyaml into
comment-retaining dictionary-like structures. Here those structures get parsed
into pydantic models that know what their fields actually are.

This two level structure is maintained so that in some version after SATKIT 1.0
we can implement configuration round tripping with preserved comments.
"""

import logging
from pathlib import Path
from typing import Optional

from satkit.helpers.base_model_extensions import UpdatableBaseModel

_logger = logging.getLogger('satkit.configuration_models')


class MainConfig(UpdatableBaseModel):
    epsilon: float
    mains_frequency: float
    data_run_parameter_file: Path
    gui_parameter_file: Path
    publish_parameter_file: Optional[Path]

# data run params
    # time_limit_schema = Map({
    #                         "tier": Str(),
    #                         "interval": IntervalCategoryValidator(),
    #                         Optional("label"): Str(),
    #                         "boundary": IntervalBoundaryValidator(),
    #                         Optional("offset"): Float(),
    #                         })

    # if filepath.is_file():
    #     with closing(
    #             open(filepath, 'r', encoding=DEFAULT_ENCODING)) as yaml_file:
    #         schema = Map({
    #             Optional("output directory"): PathValidator(),
    #             "flags": Map({
    #                 "detect beep": Bool(),
    #                 "test": Bool()
    #             }),
    #             Optional("pd_arguments"): Map({
    #                 "norms": Seq(Str()),
    #                 "timesteps": Seq(Int()),
    #                 Optional("mask_images", default=False): Bool(),
    #                 Optional("pd_on_interpolated_data", default=False): Bool(),
    #                 Optional("release_data_memory", default=True): Bool(),
    #                 Optional("preload", default=True): Bool(),
    #             }),
    #             Optional("peaks"): Map({
    #                 "modality_pattern": Str(),
    #                 Optional("normalisation"): NormalisationValidator(),
    #                 Optional("time_min"): time_limit_schema,
    #                 Optional("time_max"): time_limit_schema,
    #                 Optional("detection_params"): Map({
    #                 Optional('height'): Float(),
    #                 Optional('threshold'): Float(),
    #                     Optional("distance"): Int(),
    #                     Optional("distance_in_seconds"): Float(),
    #                     Optional("prominence"): Float(),
    #                     Optional("width"): Int(),
    #                     Optional('wlen'): Int(),
    #                     Optional('rel_height'): Float(),
    #                     Optional('plateau_size'): Float(),
    #                 }),
    #             }),
    #             Optional("downsample"): Map({
    #                 "modality_pattern": Str(),
    #                 "match_timestep": Bool(),
    #                 "downsampling_ratios": Seq(Int()),
    #             }),
    #             Optional("cast"): Map({
    #                 "pronunciation dictionary": PathValidator(),
    #                 "speaker id": Str(),
    #                 "cast flags": Map({
    #                     "only words": Bool(),
    #                     "file": Bool(),
    #                     "utterance": Bool()
