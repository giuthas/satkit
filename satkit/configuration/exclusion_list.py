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

# Built in packages
import csv
import logging
from contextlib import closing
from pathlib import Path

from strictyaml import load

_io_logger = logging.getLogger('satkit.io')

def set_exclusions_from_csv_file(filename, recordings):
    """
    Read list of files (that is, recordings) to be excluded from processing
    and mark them as excluded in the array of recording objects.
    """
    if filename is not None:
        _io_logger.debug(
            "Setting exclusions from file %s.", filename)
        with closing(open(filename, 'r', encoding='utf-8')) as csvfile:
            reader = csv.reader(csvfile, delimiter='\t')
            # Throw away the second field - it is a comment for human readers.
            exclusion_list = [row[0] for row in reader if row]
            _io_logger.info('Read exclusion list %s with %s names.', 
                            filename, str(len(exclusion_list)))
    else:
        _io_logger.debug(
            "No exclusion file. Using an empty list.")
        exclusion_list = []

    # mark as excluded
    [recording.exclude() for recording in recordings
     if recording.basename in exclusion_list]


def read_exclusion_list_from_yaml(filepath: Path) -> dict:
    """
    Read the exclusion list from filepath.
    
    If no exclusion list file is present, return an empty array
    after warning the user.
    """
    if filepath.is_file():
        with closing(open(filepath, 'r')) as yaml_file:
            yaml = load(yaml_file.read())
            exclusion_dict = yaml.data
    else:
        exclusion_dict = {}
        print(f"Did not find the exclusion list at {filepath}. Proceeding anyhow.")
    return exclusion_dict

def apply_yaml_exclusion_list(table: list[dict], exclusion_path: Path) -> None:

    exclusion_list = read_exclusion_list_from_yaml(exclusion_path)

    if not exclusion_list:
        return

    for entry in table:
        filename = entry['filename']
        if filename in exclusion_list['files']:
            print(f'Excluding {filename}: File is in exclusion list.')
            entry['excluded'] = True

        # The first condition sees if the whole prompt is excluded, 
        # the second condition checks if any parts of the prompt 
        # match exclucion criteria (for example excluding 'foobar ...' 
        # based on 'foobar').
        prompt = entry['prompt']
        if (prompt in exclusion_list['prompts'] or
            [element for element in exclusion_list['parts of prompts'] if(element in prompt)]):
            print(f'Excluding {filename}. Prompt: {prompt} matches exclusion list.')
            entry['excluded'] = True


def read_file_exclusion_list_from_csv(filename):
    """
    Read list of files (that is, recordings) to be excluded from processing.
    """
    if filename is not None:
        with closing(open(filename, 'r', encoding = 'utf-8')) as csvfile:
            reader = csv.reader(csvfile, delimiter='\t')
            # Throw away the second field - it is a comment for human readers.
            exclusion_list = [row[0] for row in reader]
            _io_logger.info('Read exclusion list {filename} with {length} names.', 
                        filename = filename, length = str(len(exclusion_list)))
    else:
        exclusion_list = []

    return exclusion_list
