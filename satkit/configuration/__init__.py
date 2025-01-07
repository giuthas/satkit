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
This is the configuration interface for reading and saving configuration data.

Direct use of config_dict, data_run_params, gui_params, and publish_params
(from configuration_parsers) is deprecated since v0.8. Instead, use the
interface provided by Configuration.
"""

from .configuration_parsers import (
    parse_config, PathValidator)
from .configuration_models import (
    ExclusionList, DataRunConfig, DownsampleParams, FindPeaksScipyArguments,
    GuiConfig, MainConfig, PathStructure, PeakDetectionParams,
    PointAnnotationParams, SearchPattern, SplineConfig, SplineDataConfig,
    SplineImportConfig, TimeseriesNormalisation)
from .configuration_setup import Configuration
from .exclusion_list_functions import (
    apply_exclusion_list, load_exclusion_list, remove_excluded_recordings
)
