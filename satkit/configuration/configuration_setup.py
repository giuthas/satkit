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
import logging
from pathlib import Path
from typing import Union

# TODO: implement an update method as well
# as save functionality.

from .configuration_parsers import (
    parse_config, config_dict, data_run_params, gui_params, publish_params
)
from .configuration_models import MainConfig

_logger = logging.getLogger('satkit.configuration_setup')
main_config = None
data_run_config = None
gui_config = None
publish_config = None


def setup_configuration(
        configuration_file: Union[Path, str, None] = None) -> None:
    parse_config(configuration_file)
    global main_config
    if main_config is None:
        main_config = MainConfig(**config_dict)
    else:
        raise NotImplementedError(
            "Updating configuration from a file has not yet been implemented.")
        # main_config.update(**config_dict)
