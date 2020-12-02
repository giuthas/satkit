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
import satkit.audio as satkit_audio
import satkit.io.AAA as satkit_AAA


_pd_logger = logging.getLogger('satkit.pd')    


def pd(token):
    """
    Calculate PD (Pixel Distance) for the recording. 

    Returns a dictionary containing PD and SBPD as functions of time,
    beep time and a time vector spanning the ultrasound recording.

    """

    notice = token['base_name'] + " " + token['prompt']
    if token['excluded']:
        notice += ': Token excluded.'
        _pd_logger.info(notice)
        return None
    else:
        notice += ': Token being processed.'
        _pd_logger.info(notice)

    (ult_wav_fs, ult_wav_frames) = sio_wavfile.read(token['ult_wav_file'])
    # setup the high-pass filter for removing the mains frequency from the recorded sound.
    b, a = satkit_audio.high_pass_50(ult_wav_fs)
    beep_uti, has_speech = satkit_audio.detect_beep_and_speech(ult_wav_frames,
                                                           ult_wav_fs,
                                                           b, a,
                                                           token['ult_wav_file'])
    
    meta = satkit_AAA.parse_ult_meta(token['ult_meta_file'])
    ult_fps = meta['FramesPerSec']
    ult_NumVectors = meta['NumVectors']
    ult_PixPerVector = meta['PixPerVector']
    ult_TimeInSecsOfFirstFrame = meta['TimeInSecsOfFirstFrame']

    with closing(open(token['ult_file'], 'rb')) as ult_file:
        ult_data = ult_file.read()
        ultra = np.fromstring(ult_data, dtype=np.uint8)
        ultra = ultra.astype("float32")
        
        ult_no_frames = int(len(ultra)/(ult_NumVectors*ult_PixPerVector))
        # reshape into vectors containing a frame each
        ultra = ultra.reshape((ult_no_frames, ult_NumVectors, ult_PixPerVector))
            
        ultra_diff = np.diff(ultra, axis=0)
        abs_diff = np.abs(ultra_diff)
        ultra_diff = np.square(ultra_diff)
        slw_pd = np.sum(ultra_diff, axis=2) # this should be square rooted at some point
        ultra_d = np.sqrt(np.sum(slw_pd, axis=1))

        ultra_l1 = np.sum(abs_diff, axis=(1,2))
        ultra_l3 = np.power(np.sum(np.power(abs_diff, 3), axis=(1,2)), 1.0/3.0)
        ultra_l10 = np.power(np.sum(np.power(abs_diff, 10), axis=(1,2)), .1)
        
        notice = token['base_name'] + " " + token['prompt']
        notice += ': PD calculated.'
        _pd_logger.debug(notice)

        
    ultra_time = np.linspace(0, len(ultra_d), len(ultra_d), endpoint=False)/ult_fps
    ultra_time = ultra_time + ult_TimeInSecsOfFirstFrame + .5/ult_fps

    ult_wav_time = np.linspace(0, len(ult_wav_frames), 
                               len(ult_wav_frames), endpoint=False)/ult_wav_fs
        
    notice = token['base_name'] + " " + token['prompt']
    notice += ': Token processed.'
    _pd_logger.info(notice)

    data = {}
    data['pd'] = ultra_d
    data['l1'] = ultra_l1 
    data['l3'] = ultra_l3 
    data['l10'] = ultra_l10 
    data['l_inf'] = np.max(abs_diff, axis=(1,2))
    data['sbpd'] = slw_pd
    data['ultra_time'] = ultra_time
    data['beep_uti'] = beep_uti
    data['ultra_wav_time'] = ult_wav_time
    data['ultra_wav_frames'] = ult_wav_frames

    return data
        

