# Built in packages
import logging
import sys

# Numpy and scipy
import numpy as np
# dicom reading
import pydicom

# TODO change the logger name
_3D4D_ultra_logger = logging.getLogger('satkit.ThreeD_ultrasound')

def getData(meta):
    ds = pydicom.dcmread(meta['filename'])

    # There are other options, but we don't deal with them just yet.
    # Before 1.0: fix the above. see loadPhillipsDCM.m on how.
    if len(ds.SequenceOfUltrasoundRegions) == 3:
        type = ds[0x200d, 0x3016][1][0x200d, 0x300d].value
        if type == 'UDM_USD_DATATYPE_DIN_3D_ECHO':
            read_3D_ultra(ds)
        else:
            _3D4D_ultra_logger.critical(
                "Unknown DICOM ultrasound type: " + type + " in "
                + meta['filename'] + ".")
            _3D4D_ultra_logger.critical('Exiting.')
            sys.exit()
    else:
        _3D4D_ultra_logger.critical(
            "Do not know what to do with data with "
            + str(len(ds.SequenceOfUltrasoundRegions)) + " regions in "
            + meta['filename'] + ".")
        _3D4D_ultra_logger.critical('Exiting.')
        sys.exit()

    # Before 1.0: 'NumVectors' and 'PixPerVector' are bad names here.
    # They come from the AAA ultrasound side of things and should be
    # replaced, but haven't been yet as I'm in a hurry to get PD
    # running on 3d4d ultrasound.

    # TODO Make sure that the data is in the order expected by everybody else:
    # first dimension is time, then as they are in 2d ultra and z is the last
    # one. also check that the direction of data is correct: axis going the way
    # they should.
    meta['no_frames'] = data.shape[0]
    meta['NumVectors'] = data.shape[1]
    meta['PixPerVector'] = data.shape[2]
    ultra3D_time = np.linspace(
        0, meta['no_frames'],
        num=meta['no_frames'],
        endpoint=False)
    timevector = ultra3D_time / \
        meta['FramesPerSec'] + timeOffset

def read_3D_ultra(self, ds, meta):
    ultra_sequence = ds[0x200d, 0x3016][1][0x200d, 0x3020][0]

    # data dimensions
    numberOfFrames = int(ultra_sequence[0x200d, 0x3010].value)
    shape = [int(token) for token in ds[0x200d, 0x3301].value]
    frameSize = np.prod(shape)
    shape.append(numberOfFrames)

    # data scale in real space-time
    scale = [float(token) for token in ds[0x200d, 0x3303].value]
    meta['FramesPerSec'] = float(ds[0x200d, 0x3207].value)

    # Before 1.0: unify the way scaling works across the data.
    # here we have an attribute, in AAA ultrasound we have meta
    # keys.
    _scale = scale

    # The starting index for the non-junk data
    # no junk from pydicom at the beginning. only at end of each frame
    # s = 32

    # Get the number of junk data points between each frame
    interval = (
        len(ultra_sequence[0x200d, 0x300e].value)-frameSize*numberOfFrames)
    interval = int(interval/numberOfFrames)

    data = np.frombuffer(
        ultra_sequence[0x200d, 0x300e].value, dtype=np.uint8)

    data.shape = (numberOfFrames, frameSize+interval)
    data = np.take(data, np.arange(frameSize)+32, axis=1)
    shape.reverse()
    data.shape = shape

    return data, meta

    # this should be unnecessary now
    # _data = np.transpose(data)
