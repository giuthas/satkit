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
import logging

# Numpy and scipy
import numpy as np
import scipy.io.wavfile as sio_wavfile

# local modules
import satkit.io.AAA as satkit_AAA


_annd_logger = logging.getLogger('satkit.annd')    

def parse_line(line):
    # This relies on none of the fields being empty and is necessary to be 
    # able to process AAA's output which sometimes has extra tabs.
    cells = line.split('\t')
    token = {'id': cells[0],
             'date_and_time': cells[1],
             'sample_time': float(cells[2]),
             'prompt': cells[3],
             'nro_spline_points': int(cells[4]),
             'beg': 0,
             'end': 42}
             
    # token['x'] = np.fromiter(cells[8:8+token['nro_spline_points']:2], dtype='float')
    # token['y'] = np.fromiter(cells[9:9+token['nro_spline_points']:2], dtype='float')
    
    #    temp = [token['x'], token['y']]
    #    nans = np.sum(np.isnan(temp), axis=0)
    #    print(token['prompt'])
    #    print('first ' + str(nans[::-1].cumsum(0).argmax(0)))
    #    print('last ' + str(nans.cumsum(0).argmax(0)))
        
    token['r'] = np.fromiter(cells[5:5+token['nro_spline_points']], dtype='float')
    token['phi'] = np.fromiter(cells[5+token['nro_spline_points']:5+2*token['nro_spline_points']], dtype='float')
    token['conf'] = np.fromiter(cells[5+2*token['nro_spline_points']:5+3*token['nro_spline_points']], dtype='float')    

    return token


def retrieve_splines(filename, prompt):
    """
    This version relies on recognising the recording based on a unique prompt. 
    Should really use a combination of id, prompt, filename, recording time.
    Problem is that AAA uses 24 hour clock in prompt files and 12 hour clock in
    exported data files. So SATKIT needs to learn to deal with that.
    The correct field would be called date_and_time.
    """
    with closing(open(filename, 'r')) as splinefile:
        splinefile.readline() # Toss the headers.
        table = [parse_line(line) for line in splinefile.readlines()]

    table = [row for row in table if row['prompt'] == prompt]
    _annd_logger.info("Read file " + filename + ".")
    return table



def annd(token):
    """
    Calculate Average Nearest Neighbour Distance (ANND) curve for the recording. 

    Returns a dictionary containing ANND as a function of time,
    a time vector spanning the splined part of the ultrasound recording.

    """

    notice = token['base_name'] + " " + token['prompt']
    if token['excluded']:
        notice += ': Token excluded.'
        _annd_logger.info(notice)
        return None
    else:
        notice += ': Token being processed.'
        _annd_logger.info(notice)
    
    meta = satkit_AAA.parse_ult_meta(token['ult_meta_file'])
    ult_fps = meta['FramesPerSec']
    ult_NumVectors = meta['NumVectors']
    ult_PixPerVector = meta['PixPerVector']
    ult_TimeInSecsOfFirstFrame = meta['TimeInSecsOfFirstFrame']

    # select the right recording here - we are accessing a database.
    # splines = retrieve_splines(token['spline_file'], token['prompt'])
    # splines = retrieve_splines('annd_sample/File003_splines.csv',
    #                            token['prompt'])
    splines = retrieve_splines('ultrafest_annd_sample/ex4_set2_splines_ultrafest.csv',
                               token['prompt'])
    _annd_logger.debug(token['prompt'] + ' has ' + str(len(splines)) + 'splines.')
    
    for spline in splines:
        x = np.multiply(spline['r'],np.sin(spline['phi']))
        y = np.multiply(spline['r'],np.cos(spline['phi']))
        #####
        # disregard samples 1-12 from the front and 1-4 from back, they have 
        # bad conf values
        #
        # this should be user adjustable after examining the splines
        #####
        spline['x'] = x[15:-6]
        spline['y'] = y[15:-6]

    timestep = 5
    # loop to calculate annd
    num_points = len(splines[1]['x'])
    annd = np.zeros(len(splines)-timestep)
    mnnd = np.zeros(len(splines)-timestep)
    spline_d = np.zeros(len(splines)-timestep)
    for i in range(len(splines)-timestep):
        current_points = np.stack((splines[i]['x'], splines[i]['y']))
        next_points = np.stack((splines[i+timestep]['x'], splines[i+timestep]['y']))

        diff = np.subtract(current_points, next_points) 
        diff = np.square(diff)
        diff = np.sum(diff, axis=0)
        diff = np.sqrt(diff)
        spline_d[i] = np.average(diff)
        
        nnd = np.zeros(num_points)
        for j in range(num_points):
            current_point = np.tile(current_points[:,j:j+1], (1, num_points))
            diff = np.subtract(current_point, next_points) 
            diff = np.square(diff)
            diff = np.sum(diff, axis=0)
            diff = np.sqrt(diff)
            nnd[j] = np.amin(diff)

        annd[i] = np.average(nnd)
        mnnd[i] = np.median(nnd)

        # diff = np.subtract(current_points, next_points)
        # diff = np.square(diff)
        # diff = np.sum(diff, axis=0)
        # diff = np.cbrt(np.sqrt(diff))
        # annd[i] = np.average(diff)
        
    notice = token['base_name'] + " " + token['prompt']
    notice += ': ANND calculated.'
    _annd_logger.debug(notice)
        
    spline_time = np.array([spline['sample_time'] for spline in splines])
    annd_time = np.add(spline_time[timestep:], spline_time[0:-timestep])
    annd_time = np.divide(annd_time, np.repeat(2.0, len(splines)-timestep))
    
    notice = token['base_name'] + " " + token['prompt']
    notice += ': Token processed in ANND.'
    _annd_logger.info(notice)

    data = {}
    data['annd'] = annd
    data['mnnd'] = mnnd
    data['spline_d'] = spline_d
    data['annd_time'] = annd_time
    
    return data
        

