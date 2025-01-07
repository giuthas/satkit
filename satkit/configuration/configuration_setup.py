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
"""Main configuration for SATKIT."""

import logging
from pathlib import Path

from .configuration_parsers import (
    load_main_config, load_gui_params, load_publish_params,
    load_run_params  # , load_plot_params
)
from .configuration_models import (
    GuiConfig, MainConfig, DataRunConfig, PublishConfig
)

_logger = logging.getLogger('satkit.configuration_setup')


class Configuration:
    """
    Main configuration class of SATKIT.    
    """

    # TODO
    # - reload

    # TODO: implement an update method as well
    # as save functionality.

    def __init__(
            self,
            configuration_file: Path | str | None = None
    ) -> None:
        """
        Init the main configuration object. 

        Run only once. Updates should be done with methods of the class.

        Parameters
        -------
        configuration_file : Union[Path, str, None]
            Path to the main configuration file.
        """
        # TODO: deal with the option that configuration_file is None

        self._main_config_yaml = load_main_config(configuration_file)
        self._main_config = MainConfig(**self._main_config_yaml.data)

        self._data_run_yaml = load_run_params(
            self._main_config.data_run_parameter_file)
        self._data_run_config = DataRunConfig(**self._data_run_yaml.data)

        self._gui_yaml = load_gui_params(self._main_config.gui_parameter_file)
        self._gui_config = GuiConfig(**self._gui_yaml.data)

        # self._plot_yaml = load_plot_params(config['plotting_parameter_file'])
        # self._plot_config = PlotConfig(**self._plot_yaml.data)

        self._publish_yaml = load_publish_params(
            self._main_config.publish_parameter_file)
        # ic(self._publish_yaml.data)
        self._publish_config = PublishConfig(**self._publish_yaml.data)

    def __repr__(self) -> str:
        return (
            f"Configuration(\nmain_config={self._main_config.model_dump()})"
            f"\ndata_run={self._data_run_config.model_dump()}"
            f"\ngui={self._gui_config.model_dump()}"
            f"\npublish={self._publish_config.model_dump()})"
        )

    @property
    def main_config(self) -> MainConfig:
        """Main config options."""
        return self._main_config

    @property
    def data_run_config(self) -> DataRunConfig:
        """Config options for a data run."""
        return self._data_run_config

    @property
    def gui_config(self) -> GuiConfig:
        """Gui config options."""
        return self._gui_config

    @property
    def publish_config(self) -> PublishConfig:
        """Result publishing configuration options."""
        return self._publish_config

    def update_from_file(
            self, configuration_file: Path | str
    ) -> None:
        """
        Update the configuration from a file.

        Parameters
        ----------
        configuration_file : Union[Path, str]
            File to read the new options from.

        Raises
        ------
        NotImplementedError
            This hasn't been implemented yet.
        """
        raise NotImplementedError(
            "Updating configuration from a file has not yet been implemented.")
        # main_config.update(**config_dict)

    def save_to_file(
            self, file: Path | str
    ) -> None:
        """
        Save configuration to a file.

        Parameters
        ----------
        file : Union[Path, str]
            File to save to.

        Raises
        ------
        NotImplementedError
            This hasn't been implemented yet.
        """
        raise NotImplementedError(
            "Saving configuration to a file has not yet been implemented.")
