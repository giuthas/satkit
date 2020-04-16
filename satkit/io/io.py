#
# Copyright (c) 2019-2020 Pertti Palo, Scott Moisik, and Matthew Faytak.
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
from contextlib import closing
import csv
import json
import logging
import pickle


_io_logger = logging.getLogger('satkit.io')    

def save2pickle(data, filename):
    """
    Saves a (token_metadata_list, data) tuple to a .pickle file.

    """
    with closing(open(filename, 'bw')) as outfile:
        pickle.dump(data, outfile)
        _io_logger.debug('Wrote data to pickle file ' + filename + '.')
        

def load_pickled_data(filename):
    """
    Loads a (token_metadata_list, data) tuple from a .pickle file and
    returns the tuple.

    """
    data = None
    with closing(open(filename, 'br')) as infile:
        data = pickle.load(infile)
        _io_logger.debug('Read data from pickle file ' + filename + '.')

    return data


def save_data_2json(data, filename):
    """
    THIS FUNCTION HAS NOT BEEN IMPLEMENTED YET.
    """
    # Can possibly be implemented with something like the example below
    # (see also
    # https://stackoverflow.com/questions/26646362/numpy-array-is-not-json-serializable)
    # but to be used as a save-load pair, this will also need Decoder to interpret
    # json to numpy.
    #
    # class NumpyEncoder(json.JSONEncoder):
    #     def default(self, obj):
    #         if isinstance(obj, np.ndarray):
    #             return obj.tolist()
    #         return json.JSONEncoder.default(self, obj)
        
    # a = np.array([[1, 2, 3], [4, 5, 6]])
    # print(a.shape)
    # json_dump = json.dumps({'a': a, 'aa': [2, (2, 3, 4), a], 'bb': [2]}, cls=NumpyEncoder)
    # print(json_dump)

    _io_logger.critical('The function save_data_2json has not yet been implemented.')
    with closing(open(filename, 'w')) as outfile:
        json.dump(data, outfile)


def load_json_data(filename):
    """
    THIS FUNCTION HAS NOT BEEN IMPLEMENTED YET.
    """

    _io_logger.critical('The function load_json_data has not yet been implemented.')
    data = None
    with closing(open(filename, 'r')) as infile:
        data = json.load(infile)

    return data


def write_metadata_to_csv(meta, filename):
    """
    Write the metadata dict into a .csv file so that it can easily 
    be read by humans and machines.
    """
    # Finally dump all the metadata into a csv-formated file.
    with closing(open(filename, 'w')) as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=meta[0].keys())

        writer.writeheader()
        map(writer.writerow, meta)
        _io_logger.debug('Wrote metadata to file ' + filename + '.')


def save_prompt_freq(prompt_freqs):
    """
    NOT IN USE YET.
    Save frequency count of each prompt in a .csv file. 
    """
    with closing(open('prompt_freqs.csv', 'w')) as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['prompt', 'frequency'])
        for prompt in sorted(prompt_freqs.keys()):
            writer.writerow([prompt, prompt_freqs[prompt]])
        _io_logger.debug('Wrote prompt frequency counts to file ' + filename + '.')

