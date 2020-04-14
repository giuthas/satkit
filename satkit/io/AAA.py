#
# Copyright (c) 2019-2020 Pertti Palo.
#
# This file is part of Pixel Difference toolkit 
# (see https://github.com/giuthas/pd/).
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

# Built in packages
from contextlib import closing
import csv
import glob
import logging
import os
import os.path


_AAA_logger = logging.getLogger('sap.AAA')

def read_prompt(filename):
    """
    Read an AAA .txt (not US.txt) file and return the 
    prompt, recording date and participant name.
    """
    with closing(open(filename, 'r')) as promptfile:
        lines = promptfile.read().splitlines()
        prompt = lines[0]
        date = lines[1]
        # could also do datetime as below, but there doesn't seem to be any reason to so.
        # date = datetime.strptime(lines[1], '%d/%m/%Y %H:%M:%S')
        participant = lines[2].split(',')[0]

        _AAA_logger.debug("Read prompt file " + filename + ".")
        return(prompt, date, participant)


def read_file_exclusion_list(filename):
    """
    Read list of files (that is, recordings) to be excluded from processing.
    """
    if filename is not None:
        with closing(open(filename, 'r')) as csvfile:
            reader = csv.reader(csvfile, delimiter='\t')
            # Throw away the second field - it is a comment for human readers.
            exclusion_list = [row[0] for row in reader]
            _AAA_logger.info('Read exclusion list ' + filename + ' with ' +
                           str(len(exclusion_list)) + ' names.')
    else:
        exclusion_list = []

    return exclusion_list


def parse_ult_meta(filename):
    """
    Return all metadata from an AAA US.txt file as dictionary.
    """
    with closing(open(filename, 'r')) as metafile:
        meta = {}
        for line in metafile:
            (key, value_str) = line.split("=")
            try:
                value = int(value_str)
            except ValueError:
                value = float(value_str)
            meta[key] = value

        _AAA_logger.debug("Read and parsed ultrasound metafile " + filename + ".")
        return meta


def get_recording_list(directory, exclusion_list_name = None):
    """
    Prepare a list of files to be processed based on directory
    contents and possible exclusion list. File existence is tested for,
    and if crucial files are missing from a given recording it will be
    excluded.
    
    The function returns a list of metadata dictionaries sorted by
    time and date of recording.

    """
    # directory handling:
    # add a config file for listing the directories and subdirectories where things are
    # default into everything being in the given dir if no config is present
    #
    # like so:
    # ult_directory = os.path.join(directory, ult_subdirectory)

    # File exclusion list is provided by the user.
    file_exclusion_list = read_file_exclusion_list(exclusion_list_name)

    # this is equivalent with the following:
    # sorted(glob.glob(directory + '/.' +  '/*US.txt'))
    ult_meta_files = sorted(glob.glob(directory + '/*US.txt'))

    # this takes care of *.txt and *US.txt overlapping.
    ult_prompt_files = [prompt_file 
                        for prompt_file in glob.glob(directory + '/*.txt') 
                        if not prompt_file in ult_meta_files
                        ]
    ult_prompt_files = sorted(ult_prompt_files)

    # strip file extensions off of filepaths to get the base names
    base_names = [os.path.splitext(prompt_file)[0] for prompt_file in ult_prompt_files]
    meta = [{'base_name': base_name} for base_name in base_names] 

    # iterate over file base names and check for required files
    for i, base_name in enumerate(base_names):
        # Prompt file should always exist and correspond to the base_name because 
        # the base_name list is generated from the directory listing of prompt files.
        meta[i]['ult_prompt_file'] = ult_prompt_files[i]
        (prompt, date, participant) = read_prompt(ult_prompt_files[i])
        meta[i]['prompt'] = prompt
        meta[i]['date'] = date
        meta[i]['participant'] = participant

        if base_name in file_exclusion_list:
            notice = base_name + " is in the exclusion list."
            _AAA_logger.info(notice)
            meta[i]['excluded'] = True
        else:
            meta[i]['excluded'] = False

        # Candidates for filenames. Existence tested below.
        ult_meta_file = os.path.join(base_name + "US.txt")
        ult_wav_file = os.path.join(base_name + ".wav")
        ult_file = os.path.join(base_name + ".ult")

        # check if assumed files exist, and arrange to skip them if any do not
        if os.path.isfile(ult_meta_file):
            meta[i]['ult_meta_file'] = ult_meta_file
            meta[i]['ult_meta_exists'] = True
        else: 
            notice = 'Note: ' + ult_meta_file + " does not exist."
            _AAA_logger.warning(notice)
            meta[i]['ult_meta_exists'] = False
            meta[i]['excluded'] = True
            
        if os.path.isfile(ult_wav_file):
            meta[i]['ult_wav_file'] = ult_wav_file
            meta[i]['ult_wav_exists'] = True
        else:
            notice = 'Note: ' + ult_wav_file + " does not exist."
            _AAA_logger.warning(notice)
            meta[i]['ult_wav_exists'] = False
            meta[i]['excluded'] = True
            
        if os.path.isfile(ult_file):
            meta[i]['ult_file'] = ult_file
            meta[i]['ult_exists'] = True
        else:
            notice = 'Note: ' + ult_file + " does not exist."
            _AAA_logger.warning(notice)
            meta[i]['ult_exists'] = False
            meta[i]['excluded'] = True        

        # TODO this needs to be moved to a decorator function
        # if 'water swallow' in prompt:
        #     notice = 'Note: ' + base_names[i] + ' prompt is a water swallow.'
        #     _AAA_logger.info(notice)
        #     meta[i]['type'] = 'water swallow'
        #     meta[i]['excluded'] = True        
        # elif 'bite plate' in prompt:
        #     notice = 'Note: ' + base_names[i] + ' prompt is a bite plate.'
        #     _AAA_logger.info(notice)
        #     meta[i]['type'] = 'bite plate'
        #     meta[i]['excluded'] = True        
        # else:
        #     meta[i]['type'] = 'regular trial'


    meta = sorted(meta, key=lambda token: token['date'])

    return meta


