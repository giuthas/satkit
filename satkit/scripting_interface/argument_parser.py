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
Commandline argument parser.
"""

import argparse
import warnings


def widen_help_formatter(formatter, total_width=140, syntax_width=35):
    """Return a wider HelpFormatter for argparse, if possible."""
    try:
        # https://stackoverflow.com/a/5464440
        # beware: "Only the name of this class is considered a public API."
        kwargs = {'width': total_width, 'max_help_position': syntax_width}
        formatter(None, **kwargs)
        return lambda prog: formatter(prog, **kwargs)
    except TypeError:
        warnings.warn(
            "Widening argparse help formatter failed. "
            "Falling back on default settings.")
    return formatter


class SatkitArgumentParser:
    """
    This class is the root class for SATKIT commandline interfaces.

    This class is not fully functional by itself: It does not read files
    nor run any processing on files.
    """

    def __init__(self, description):
        """
        Set up a commandline interface with the given description.

        Sets up the parsers and runs it, and also sets up logging. Description
        is what this version will be called if called with -h or --help.
        """
        self.description = description
        self.parser = argparse.ArgumentParser(
            description=self.description,
            formatter_class=widen_help_formatter(
                argparse.HelpFormatter, total_width=80, syntax_width=35))
        self._add_positional_arguments()
        self._add_optional_arguments()
        self.args = self.parser.parse_args()

    def _add_optional_arguments(self):
        """Adds optional arguments."""

        helptext = (
            'Open the SATKIT annotator. '
            'Defaults to True.'
        )
        self.parser.add_argument("-a", "--annotator",
                                 dest="annotator",
                                 default=True,
                                 action=argparse.BooleanOptionalAction,
                                 help=helptext)

        helptext = (
            'Use the given main configuration file. '
            'Other files will be specified by the main config file.'
        )
        self.parser.add_argument("-c", "--configuration",
                                 dest="configuration_filename",
                                 help=helptext, metavar="file")

        helptext = (
            'Should an ultrasound frame be displayed by the annotator. '
            'Set to False if the .ult files are not available.'
        )
        self.parser.add_argument("--displayUltraFrame", dest="displayTongue",
                                 default=True,
                                 action=argparse.BooleanOptionalAction,
                                 help=helptext)

        self.parser.add_argument(
            "-e", "--exclusion_list", dest="exclusion_filename",
            help="Exclusion list of data files that should be ignored.",
            metavar="file")

        helptext = (
            'Destination directory for generated figures.'
        )
        self.parser.add_argument("-f", "--figures", dest="figure_dir",
                                 default="figures",
                                 help=helptext, metavar="dir")

        helptext = (
            'Save metrics to file. '
            'Supported type is .pickle. '
            'Saving to .json, .csv., and .m may be possible in the future.'
        )
        self.parser.add_argument("-o", "--output", dest="output_filename",
                                 help=helptext, metavar="file")

        helptext = (
            'Should we publish figures into a pdf file.'
        )
        self.parser.add_argument("-p", "--publish", dest="publish",
                                 default=False,
                                 action=argparse.BooleanOptionalAction,
                                 help=helptext)
        helptext = (
            'Set verbosity of console output. Range is [0, 3], default is 1, '
            'larger values mean greater verbosity.'
        )
        self.parser.add_argument("-v", "--verbose",
                                 type=int, dest="verbose",
                                 default=1,
                                 help=helptext,
                                 metavar="verbosity")

    def _add_positional_arguments(self):
        """Setup basic commandline parsing and the file loading argument."""
        # mutually exclusive with reading previous results from a file
        helptext = (
            'Path containing the data to be read.'
            'Supported types are .pickle files, and directories '
            'containing files exported from AAA. '
            'Loading from .m, .json, and .csv are in the works.')
        self.parser.add_argument("load_path", help=helptext)
