#
# Copyright (c) 2019-2022 Pertti Palo, Scott Moisik, Matthew Faytak, and Motoki Saito.
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

import argparse
import datetime
import logging
import os
import os.path
import sys
import warnings
from pathlib import Path

import satkit.io as satkit_io
import satkit.io.AAA as satkit_AAA
import satkit.io.ThreeD_ultrasound as ThreeD_ultrasound
# local modules
import satkit.plot.pd_annd_plot as pd_annd_plot


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
            "Widening argparse help formatter failed. Falling back on default settings.")
    return formatter


class BaseCLI():
    """
    This class is the root class for SATKIT commandline interfaces.

    This class is not fully functional by itself: It does not read files
    nor run any processing on files.
    """

    def __init__(self, description):
        """
        Setup a commandline interface with the given description.

        Sets up the parsers and runs it, and also sets up logging.
        Description is what this version will be called if called with -h or --help.
        """
        self.description = description
        self._parse_args()
        self._set_up_logging()

    def _add_optional_arguments(self):
        """Adds the optional verbosity argument."""
        helptext = (
            'Set verbosity of console output. Range is [0, 3], default is 1, '
            'larger values mean greater verbosity.'
        )
        self.parser.add_argument("-v", "--verbose",
                                 type=int, dest="verbose",
                                 default=1,
                                 help=helptext,
                                 metavar="verbosity")

    def _init_parser(self):
        """Setup basic commandline parsing and the file loading argument."""
        self.parser = argparse.ArgumentParser(
            description=self.description,
            formatter_class=widen_help_formatter(
                argparse.HelpFormatter, total_width=100, syntax_width=35))

        # mutually exclusive with reading previous results from a file
        helptext = (
            'Path containing the data to be read.'
            'Supported types are .pickle files, and directories '
            'containing files exported from AAA. '
            'Loading from .m, .json, and .csv are in the works.')
        self.parser.add_argument("load_path", help=helptext)

    def _parse_args(self):
        """Create a parser for commandline arguments with argparse and parse the arguments."""
        self._init_parser()
        self._add_optional_arguments()
        self.args = self.parser.parse_args()

    def _set_up_logging(self):
        """Set up logging with the logging module.

        Main thing to do is set the
        level of printed output based on the verbosity argument.
        """
        self.logger = logging.getLogger('satkit')
        self.logger.setLevel(logging.INFO)

        # also log to the console at a level determined by the --verbose flag
        console_handler = logging.StreamHandler()  # sys.stderr

        # Set the level of logging messages that will be printed to
        # console/stderr.
        if not self.args.verbose:
            console_handler.setLevel('WARNING')
        elif self.args.verbose < 1:
            console_handler.setLevel('ERROR')
        elif self.args.verbose == 1:
            console_handler.setLevel('WARNING')
        elif self.args.verbose == 2:
            console_handler.setLevel('INFO')
        elif self.args.verbose >= 3:
            console_handler.setLevel('DEBUG')
        else:
            logging.critical("Unexplained negative argument %s to verbose!",
                str(self.args.verbose))
        self.logger.addHandler(console_handler)

        self.logger.info('Data run started at %s.', str(datetime.datetime.now()))


class RawCLI(BaseCLI):
    """Run metrics on raw ultrasound data."""

    def __init__(self, description, processing_functions, plot=True):
        """
        Setup and run the commandline interface for processing raw ultrasound data.

        description is what this version will be called if the script is called 
            with -h or --help arguments.
        processing_functions is a dict of the callables that will be run on each 
            recording.
        """
        super().__init__(description)
        self._load_data()

        # calculate the metrics
        for recording in self.recordings:
            if recording.excluded:
                continue

            for key in processing_functions:
                (function, modalities) = processing_functions[key]
                # TODO: Version 1.0: add a mechanism to change the arguments for different modalities.
                for modality in modalities:
                    function(
                        recording,
                        modality,
                        preload=True,
                        release_data_memory=True)

        # save before plotting just in case.
        if self.args.output_filename:
            self._save_data()

        # Plot the data into files if asked to.
        if plot:
            self._plot()

        self.logger.info('Data run ended at %s.', str(datetime.datetime.now()))

    def _add_optional_arguments(self):
        """ Adds optional commandline arguments."""
        self.parser.add_argument(
            "-e", "--exclusion_list", dest="exclusion_filename",
            help="Exclusion list of data files that should be ignored.",
            metavar="file")

        helptext = (
            'Save metrics to file. '
            'Supported type is .pickle. '
            'Saving to .json, .csv., and .m may be possible in the future.'
        )
        self.parser.add_argument("-o", "--output", dest="output_filename",
                                 help=helptext, metavar="file")

        helptext = (
            'Destination directory for generated figures.'
        )
        self.parser.add_argument("-f", "--figures", dest="figure_dir",
                                 default="figures",
                                 help=helptext, metavar="dir")

        helptext = (
            'Should an ultrasound frame be displayed by the annotator.'
            'Set to False if the .ult files are not available.'
        )
        self.parser.add_argument("--displayUltraFrame", dest="displayTongue", 
                                default=True, action=argparse.BooleanOptionalAction,
                                help=helptext)

        # Adds the verbosity argument.
        super()._add_optional_arguments()

    def _load_data(self):
        """Handle loading data from individual files or a previously saved session."""
        if not os.path.exists(self.args.load_path):
            self.logger.critical(
                'File or directory does not exist: %s.', self.args.load_path)
            self.logger.critical('Exiting.')
            sys.exit()
        elif os.path.isdir(self.args.load_path):
            # this is the actual list of recordings that gets processed
            # token_list includes meta data contained outwith the ult file
            self.recordings = self._read_data_from_files()
        elif os.path.splitext(self.args.load_path)[1] == '.pickle':
            self.recordings = satkit_io.load_pickled_data(self.args.load_path)
        elif os.path.splitext(self.args.load_path)[1] == '.json':
            self.recordings = satkit_io.load_json_data(self.args.load_path)
        else:
            self.logger.error(
                'Unsupported filetype: %s.', self.args.load_path)

    def _plot(self):
        """
        Wrapper for plotting data.

        Having this as a separate method allows subclasses to change 
        arguments and plotting commands.
        """
        self.logger.info("Drawing FP 2022 plot.")
        pd_annd_plot.draw_fp2022_spaghetti(self.recordings)

    def _read_data_from_files(self):
        """
        Wrapper for reading data from a directory full of files.

        Having this as a separate method allows subclasses to change
        arguments or even the parser.

        Note that to make data loading work the in a consistent way,
        this method just returns the data and saving it in a
        instance variable is left for the caller to handle.
        """
        recordings = satkit_AAA.generate_recording_list(self.args.load_path)

        satkit_io.set_exclusions_from_file(
            self.args.exclusion_filename, recordings)

        for recording in recordings: 
            if not recording.excluded:
                satkit_AAA.add_modalities(recording)

        return recordings

    def _save_data(self):
        if os.path.splitext(self.args.output_filename)[1] == '.pickle':
            satkit_io.save2pickle(
                self.recordings,
                self.args.output_filename)
            self.logger.info(
                "Wrote data to file %s/%s.", os.getcwd(), self.args.output_filename)
        elif os.path.splitext(self.args.output_filename)[1] == '.json':
            self.logger.error(
                'Unsupported filetype: %s.', self.args.output_filename)
        else:
            self.logger.error(
                'Unsupported filetype: %s.', self.args.output_filename)


class RawAndSplineCLI(RawCLI):
    """Run metrics on raw ultrasound and extracted spline data."""

    def __init__(self, description, processing_functions, plot=True):
        """Create a parser for commandline arguments with argparse and parse the arguments.
        """
        super().__init__(description, processing_functions, plot=plot)

    def _read_data_from_files(self):
        """
        Wrapper for reading data from a directory full of files.

        Having this as a separate method allows subclasses to change 
        arguments or even the parser.

        Note that to make data loading work the in a consistent way,
        this method just returns the data and saving it in a 
        instance variable is left for the caller to handle. 
        """
        recordings = super()._read_data_from_files()
        satkit_AAA.add_splines_from_file(recordings, self.args.spline_file)
        return recordings

    def _parse_args(self):
        """Create a parser for commandline arguments with argparse and parse the arguments."""
        super()._init_parser()

        helptext = (
            'Name of the spline file.'
            'Should be a .csv (you may need to change the file ending) file exported from AAA.'
        )
        self.parser.add_argument("spline_file",
                                 help=helptext, metavar="file")

        super()._add_optional_arguments()

        self.args = self.parser.parse_args()


class RawAndVideoCLI(RawCLI):
    """Run metrics on raw ultrasound and extracted spline data."""

    def __init__(self, description, processing_functions, plot=True):
        """Create a parser for commandline arguments with argparse and parse the arguments.
        """
        super().__init__(description, processing_functions, plot=plot)

    def _read_data_from_files(self):
        """
        Wrapper for reading data from a directory full of files.

        Having this as a separate method allows subclasses to change 
        arguments or even the parser.

        Note that to make data loading work the in a consistent way,
        this method just returns the data and saving it in a 
        instance variable is left for the caller to handle. 
        """
        recordings = super()._read_data_from_files()
        return recordings

    def _parse_args(self):
        """Create a parser for commandline arguments with argparse and parse the arguments."""
        super()._init_parser()

        super()._add_optional_arguments()

        self.args = self.parser.parse_args()

    def _plot(self):
        """
        Wrapper for plotting data.

        Having this as a separate method allows subclasses to change 
        arguments and plotting commands.
        """
        self.logger.info("Drawing CAW 2021 plot.")
        pd_annd_plot.CAW_2021_plots(
            self.recordings, self.args.figure_dir)


class Raw3D_CLI(RawCLI):

    def __init__(self, description, processing_functions, plot=True):
        super().__init__(description, processing_functions, plot=plot)

    def _read_data_from_files(self):
        """
        Wrapper for reading data from a directory full of files.

        Having this as a separate method allows subclasses to change
        arguments or even the parser.

        Note that to make data loading work the in a consistent way,
        this method just returns the data and saving it in a
        instance variable is left for the caller to handle.
        """
        recordings = ThreeD_ultrasound.generate_recording_list(
            Path(self.args.load_path))

        satkit_io.set_exclusions_from_file(
            self.args.exclusion_filename, recordings)

        for recording in recordings:
            if not recording.excluded:
                recording.addModalities()
                
        return recordings

    def _plot(self):
        """
        Wrapper for plotting data.

        Having this as a separate method allows subclasses to change
        arguments and plotting commands.
        """
        self.logger.info("Drawing CAW 2021 plots for 3D.")
        pd_annd_plot.CAW_2021_3D_plots(
            self.recordings, self.args.figure_dir)


class Old_Style_3D_CLI(RawCLI):
    """
    This class deals with 3D/4D ultrasound data that does not have a official notes .mat file.
    """

    def __init__(self, description, processing_functions, plot=True):
        super().__init__(description, processing_functions, plot=plot)

    def _read_data_from_files(self):
        """
        Wrapper for reading data from a directory full of files.

        Having this as a separate method allows subclasses to change
        arguments or even the parser.

        Note that to make data loading work the in a consistent way,
        this method just returns the data and saving it in a
        instance variable is left for the caller to handle.
        """
        recordings = ThreeD_ultrasound.generate_recording_list_old_style(
            Path(self.args.load_path))

        satkit_io.set_exclusions_from_file(
            self.args.exclusion_filename, recordings)

        for recording in recordings:
            if not recording.excluded:
                recording.addModalities()

        return recordings

    def _plot(self):
        """
        Wrapper for plotting data.

        Having this as a separate method allows subclasses to change
        arguments and plotting commands.
        """
        self.logger.info("Drawing CAW 2021 plots for 3D.")
        pd_annd_plot.CAW_2021_3D_plots(
            self.recordings, self.args.figure_dir)
