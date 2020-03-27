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
import logging

# Numpy and scipy
import numpy as np
import scipy.io.wavfile as sio_wavfile

# local modules
import pd.audio as pd_audio
import pd.import_from_AAA as pdAAA


pd_logger = logging.getLogger('pd.pd')    


def pd(token):
    """
    Calculate PD (Pixel Distance) for the recording. 

    Returns a dictionary containing PD and SBPD as functions of time,
    beep time and a time vector spanning the ultrasound recording.

    """
    if token['excluded']:
        pd_logger.info("PD: " + token['base_name'] + " " + token['prompt'] + '. Token excluded.')
        return None
    else:
        pd_logger.info("PD: " + token['base_name'] + " " + token['prompt'] + '. Token processed.')

    (ult_wav_fs, ult_wav_frames) = sio_wavfile.read(token['ult_wav_file'])
    # setup the high-pass filter for removing the mains frequency from the recorded sound.
    b, a = pd_audio.high_pass_50(ult_wav_fs)
    beep_uti, has_speech = pd_audio.detect_beep_and_speech(ult_wav_frames,
                                                           ult_wav_fs,
                                                           b, a,
                                                           token['ult_wav_file'])
    
    meta = pdAAA.parse_ult_meta(token['ult_meta_file'])
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
        ultra_diff = np.square(ultra_diff)
        slw_pd = np.sum(ultra_diff, axis=2)
        ultra_d = np.sqrt(np.sum(slw_pd, axis=1))
            
    ultra_time = np.linspace(0, len(ultra_d), len(ultra_d), endpoint=False)/ult_fps
    ultra_time = ultra_time + ult_TimeInSecsOfFirstFrame + .5/ult_fps

    ult_wav_time = np.linspace(0, len(ult_wav_frames), 
                               len(ult_wav_frames), endpoint=False)/ult_wav_fs
        
    data = {}
    data['pd'] = ultra_d
    data['sbpd'] = slw_pd
    data['ultra_time'] = ultra_time
    data['beep_uti'] = beep_uti

    return data
        

