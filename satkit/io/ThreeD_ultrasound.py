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
from satkit.recording import MatrixData
import logging
import sys

# Numpy
import numpy as np
from numpy.matlib import repmat

# dicom reading
import pydicom

# Local packages

_Phillips_ultra_logger = logging.getLogger('satkit.Phillips_ultrasound')


class ThreeD_Ultrasound(MatrixData):
    """
    Ultrasound Recording with raw (probe return) data.    
    """

    # Before 1.0: Figure out how to move this to MatrixData
    # and how to extend it when necessary. Practically whole of
    # __init__ is shared with RawUltrasound and so should be in MatrixData
    # instead of here. Only _getData and data.setter's message change.
    requiredMetaKeys = [
        'FramesPerSec'
    ]

    def __init__(
            self, name="lip video", parent=None, preload=False,
            timeOffset=0, filename=None, meta=None):
        """
        New keyword arguments:
        filename -- the name of a .ult file containing raw ultrasound 
            data. Default is None.
        meta -- a dict with (at least) the keys listed in 
            RawUltrasound.requiredMetaKeys. Extra keys will be ignored. 
            Default is None.
        """
        super().__init__(name=name, parent=parent, preload=preload,
                         timeOffset=timeOffset)

        self.meta['filename'] = filename

        # Explicitly copy meta data fields to ensure that we have what we expected to get.
        if meta != None:
            try:
                wanted_meta = {key: meta[key]
                               for key in ThreeD_Ultrasound.requiredMetaKeys}
            except KeyError:
                # Missing metadata for one recording may be ok and this could be handled with just
                # a call to _recording_logger.critical and setting self.excluded = True
                notFound = set(ThreeD_Ultrasound.requiredMetaKeys) - set(meta)
                _Phillips_ultra_logger.critical(
                    "Part of metadata missing when processing "
                    + self.meta['filename'] + ". ")
                _Phillips_ultra_logger.critical(
                    "Could not find " + str(notFound) + ".")
                _Phillips_ultra_logger.critical('Exiting.')
                sys.exit()

            self.meta.update(wanted_meta)

        if filename and preload:
            self._getData()
        else:
            self._data = None

    def _getData(self):
        ds = pydicom.dcmread(self.meta['filename'])

        # There are other options, but we don't deal with them just yet.
        # Before 1.0: fix the above. see loadPhillipsDCM.m on how.
        if len(ds.SequenceOfUltrasoundRegions) == 3:
            type = ds[0x200d, 0x3016][1][0x200d, 0x300d].value
            if type == 'UDM_USD_DATATYPE_DIN_3D_ECHO':
                self._read_3D_ultra(ds)
            else:
                _Phillips_ultra_logger.critical(
                    "Unknown DICOM ultrasound type: " + type + " in "
                    + self.meta['filename'] + ".")
                _Phillips_ultra_logger.critical('Exiting.')
                sys.exit()
        else:
            _Phillips_ultra_logger.critical(
                "Do not know what to do with data with "
                + str(len(ds.SequenceOfUltrasoundRegions)) + " regions in "
                + self.meta['filename'] + ".")
            _Phillips_ultra_logger.critical('Exiting.')
            sys.exit()

        # Before 1.0: 'NumVectors' and 'PixPerVector' are bad names here.
        # They come from the AAA ultrasound side of things and should be
        # replaced, but haven't been yet as I'm in a hurry to get PD
        # running on videos.
        self.meta['no_frames'] = self.data.shape[0]
        self.meta['NumVectors'] = self.data.shape[1]
        self.meta['PixPerVector'] = self.data.shape[2]
        video_time = np.linspace(
            0, self.meta['no_frames'],
            num=self.meta['no_frames'],
            endpoint=False)
        self.timevector = video_time / \
            self.meta['FramesPerSec'] + self.timeOffset
        # this should be added for PD and similar time vectors:
        # + .5/self.meta['framesPerSec']
        # while at the same time dropping a suitable number
        # (most likely = timestep) of timestamps

    def _read_3D_ultra(self, ds):
        ultra_sequence = ds[0x200d, 0x3016][1][0x200d, 0x3020][0]

        # data dimensions
        numberOfFrames = int(ultra_sequence[0x200d, 0x3010].value)
        shape = [int(token) for token in ds[0x200d, 0x3301].value]
        frameSize = np.prod(shape)
        shape.append(numberOfFrames)

        # data scale in real space-time
        scale = [float(token) for token in ds[0x200d, 0x3303].value]
        self.meta['FramesPerSec'] = float(ds[0x200d, 0x3207].value)

        # Before 1.0: unify the way scaling works across the data.
        # here we have an attribute, in AAA ultrasound we have meta
        # keys.
        self._scale = scale

        # The starting index for the non-junk data
        # no junk from pydicom at the beginning. only at end of each frame
        # s = 32

        # Get the number of junk data points between each frame
        interval = (
            len(ultra_sequence[0x200d, 0x300e].value)-frameSize*shape[3])
        interval = int(interval/shape[3])

        data = np.frombuffer(
            ultra_sequence[0x200d, 0x300e].value, dtype=np.uint8)

        # would but no junk in beginning in pydicom
        #data = data[32:]

        data.shape = (frameSize+interval, numberOfFrames)
        index = np.transpose(repmat(np.arange(frameSize), numberOfFrames, 1))

        data = np.take_along_axis(data, index, axis=0)
        data.shape = shape
        print(shape)
        self._data = np.transpose(data)
        print(self._data.shape)

    @property
    def data(self):
        return super().data

    # before v1.0: check that the data is actually valid, also call the beep detect etc. routines on it.
    @data.setter
    def data(self, data):
        """
        Data setter method.

        Assigning anything but None is not implemented yet.
        """
        if data is not None:
            raise NotImplementedError(
                'Writing over video data has not been implemented yet.')
        else:
            self._data = data
