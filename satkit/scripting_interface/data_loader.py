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
import logging
from pathlib import Path
from typing import List

from satkit.configuration import data_run_params
from satkit.data_import import generate_aaa_recording_list
from satkit.data_structures import Recording

logger = logging.getLogger('satkit.scripting')

# TODO: change the name of this file to data_importer and move it to a more
# appropriete submodule.

def load_data(path: Path, exclusion_file: Path) -> List[Recording]:
    """Handle loading data from individual files or a previously saved session."""
    if not path.exists():
        logger.critical(
            'File or directory does not exist: %s.', path)
        logger.critical('Exiting.')
        quit()
    elif path.is_dir():
        recordings = read_data_from_files(path, exclusion_file)
    elif path.suffix == '.satkit_meta':
        recordings = satkit_io.load_satkit_data(path)
    else:
        logger.error(
            'Unsupported filetype: %s.', path)
    
    return recordings

def read_data_from_files(path: Path, exclusion_file: Path):
    """
    Wrapper for reading data from a directory full of files.

    Having this as a separate method allows subclasses to change
    arguments or even the parser.

    Note that to make data loading work the in a consistent way,
    this method just returns the data and saving it in a
    instance variable is left for the caller to handle.
    """
    if exclusion_file:
        data_run_params['data properties']['exclusion list'] = exclusion_file

    recordings = generate_aaa_recording_list(path)
    return recordings

