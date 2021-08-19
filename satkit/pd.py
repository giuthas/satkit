#
# Copyright (c) 2019-2021 Pertti Palo, Scott Moisik, and Matthew Faytak.
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
import satkit.audio as satkit_audio
import satkit.io.AAA as satkit_AAA


_pd_logger = logging.getLogger('satkit.pd')    


    # this belongs in the thing that reads, not here
    # if data.excluded:
    #     notice += ': Token excluded.'
    #     _pd_logger.info(notice)


def pd(mModality, timestep = 1):
    """
    Calculate PD and attach the results to the mModality. 

    Returns a dictionary containing PD and SBPD as functions of time,
    beep time and a time vector spanning the ultrasound recording.
    """
    baseNotice = (mModality.parent.meta['base_name'] 
            + " " + mModality.parent.meta['prompt'])

    _pd_logger.info(baseNotice + ': Token being processed.')
    
    data = mModality.data
        
    raw_diff = np.diff(data, axis=0)
    abs_diff = np.abs(raw_diff)
    square_diff = np.square(raw_diff)
    slw_pd = np.sum(square_diff, axis=2) # this should be square rooted at some point
    data_l2 = np.sqrt(np.sum(slw_pd, axis=1))

    data_l1 = np.sum(abs_diff, axis=(1,2))
    data_l3 = np.power(np.sum(np.power(abs_diff, 3), axis=(1,2)), 1.0/3.0)
    data_l4 = np.power(np.sum(np.power(abs_diff, 4), axis=(1,2)), 1.0/4.0)
    data_l5 = np.power(np.sum(np.power(abs_diff, 5), axis=(1,2)), 1.0/5.0)
    data_l10 = np.power(np.sum(np.power(abs_diff, 10), axis=(1,2)), .1)

    _pd_logger.debug(baseNotice + ': PD calculated.')

    pd_time = mModality.timevector + .5/mModality.meta['FramesPerSec']

    result = {}
    result['l1'] = data_l1 
    result['pd'] = data_l2
    result['l3'] = data_l3 
    result['l4'] = data_l4 
    result['l5'] = data_l5 
    result['l10'] = data_l10 
    result['l_inf'] = np.max(abs_diff, axis=(1,2))
    result['sbpd'] = slw_pd
    result['pd_time'] = pd_time

    mModality.pd = result
        

