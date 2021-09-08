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
import logging

# Numpy and scipy
import numpy as np

# local modules
from satkit.recording import DerivedModality


_pd_logger = logging.getLogger('satkit.pd')


def addPD(recording,
          modality,
          preload=True,
          releaseDataMemory=True):
    """
    Calculate PD on dataModality and add it to recording.

    Positional arguments:
    recording -- a Recording object
    modality -- the type of the Modality to be processed. The access will 
        be by recording.modalities[modality.__name__]

    Keyword arguments:
    preload -- boolean indicating if PD should be calculated on creation 
        (preloaded) or only on access.
    releaseDataMemor -- boolean indicatin if the data attribute of the 
        data modality should be set to None after access. Only set this 
        to False, if you know that you have enough memory to hold all 
        of the data in RAM.
    """
    # Name of the new modality is constructed from the type names of
    # PD and the data modality.
    name = PD.__name__ + ' on ' + modality.__name__
    if name in recording.modalities:
        _pd_logger.info(
            "Modality '" + name +
            "' already exists in recording: " + recording.meta['basename'] + '.')
    elif recording.excluded:
        _pd_logger.info(
            "Recording " + recording.meta['basename']
            + " excluded from processing.")
    else:
        dataModality = recording.modalities[modality.__name__]

        pd = PD(name=name, parent=recording, preload=preload,
                dataModality=dataModality, releaseDataMemory=releaseDataMemory)
        recording.addModality(name, pd)
        _pd_logger.info(
            "Added '" + name +
            "' to recording: " + recording.meta['basename'] + '.')


class PD(DerivedModality):
    """
    Calculate PD and represent it as a DerivedModality. 

    PD maybe calculated using several different norms and therefore the
    result may be non-singular. For this reason self.data is a dict
    containing a PD curve for each key.
    """

    acceptedNorms = [
        'l1',
        'l2',
        'l3',
        'l4',
        'l5',
        'l6',
        'l7',
        'l8',
        'l9',
        'l10',
        'inf',
    ]

    def __init__(
            self, name="PD", parent=None, preload=True, timeOffset=0,
            dataModality=None, releaseDataMemory=True, norms=['l2'],
            timesteps=[1]):
        """
        Build a Pixel Difference (PD) Modality       

        If timestep is given as a vector of positive integers, then calculate
        and return pd for each of those.

        If parent is None, it will be copied from dataModality.
        If not specified or 0, timeOffset will be copied from dataModality.

        Note: Currently neither the norms nor the timesteps paremeter 
        is respected. Instead, all the norms get calculated and a 
        timestep of 1 is used always.
        """
        # This allows the caller to be lazy.
        if not timeOffset:
            timeOffset = dataModality.timeOffset

        super().__init__(name, parent=parent, preload=preload, timeOffset=timeOffset,
                         dataModality=dataModality, releaseDataMemory=releaseDataMemory)

        # This allows the caller to be lazy.
        if not parent and dataModality:
            self.parent = dataModality.parent

        if all(norm in PD.acceptedNorms for norm in norms):
            self._norms = norms
        else:
            ValueError("Unexpected norm requested in " + str(norms))

        if all((isinstance(timestep, int) and timestep > 0)
                for timestep in timesteps):
            # Since all timesteps are valid, we are ok.
            self._timesteps = timesteps
        else:
            ValueError("Negative or non-integer timestep in " + str(timesteps))

        self._loggingBaseNotice = (self.parent.meta['basename']
                                   + " " + self.parent.meta['prompt'])

        if preload:
            self._getData()

    def _getData(self):
        """
        Calculate Pixel Difference (PD) on the DataModality.       

        If self._timesteps is a vector of positive integers, then calculate
        pd for each of those. NOTE! Changing timestep is not yet implemented.
        """
        _pd_logger.info(self._loggingBaseNotice
                        + ': Calculating PD on '
                        + type(self.dataModality).__name__ + '.')

        data = self.dataModality.data
        result = {}

        # Hacky hack to recognise LipVideo data and change the timestep for it.
        if len(data.shape) != 3:
            self._timesteps[0] = 2

        if self._timesteps[0] != 1:
            # Before 1.0: We are only dealing with the one timestep currently. For 1.0, come up with a way of dealing with multiple timesteps in parallel.
            timestep = self._timesteps[0]

            # Flatten the data into a vector at each timestamp.
            #old_shape = data.shape
            #new_shape = (old_shape[0], np.prod(old_shape[1:]))
            #data.shape = new_shape

            # Calculate differences and reshape the result to matrices.
            raw_diff = np.subtract(data[: -timestep], data[timestep:])
            # diff_shape = list(raw_diff.shape)
            # diff_shape[0] = [diff_shape[0]-timestep]
            # raw_diff.shape = tuple(diff_shape)

            # After using data, restore the shape.
            #data.shape = old_shape

            if timestep % 2 == 1:
                self.timevector = (
                    self.dataModality.timevector
                    [timestep // 2: -(timestep // 2 + 1)])
                self.timevector = (
                    self.timevector
                    + .5/self.dataModality.meta['FramesPerSec'])
            else:
                self.timevector = (
                    self.dataModality.timevector
                    [timestep//2:-timestep//2])
        else:
            raw_diff = np.diff(data, axis=0)
            self.timevector = (self.dataModality.timevector[:-1]
                               + .5/self.dataModality.meta['FramesPerSec'])

        # Use this if we want to collapse e.g. rgb data without producing a
        # PD contour for each colour or channel.
        if raw_diff.ndim > 2:
            old_shape = raw_diff.shape
            new_shape = (old_shape[0], old_shape[1], np.prod(old_shape[2:]))
            raw_diff = raw_diff.reshape(new_shape)

        abs_diff = np.abs(raw_diff)
        square_diff = np.square(raw_diff)
        # this should be square rooted at some point
        slw_pd = np.sum(square_diff, axis=2)

        result['sbpd'] = slw_pd
        result['pd'] = np.sqrt(np.sum(slw_pd, axis=1))
        result['l1'] = np.sum(abs_diff, axis=(1, 2))
        result['l3'] = np.power(
            np.sum(np.power(abs_diff, 3), axis=(1, 2)), 1.0/3.0)
        result['l4'] = np.power(
            np.sum(np.power(abs_diff, 4), axis=(1, 2)), 1.0/4.0)
        result['l5'] = np.power(
            np.sum(np.power(abs_diff, 5), axis=(1, 2)), 1.0/5.0)
        result['l10'] = np.power(
            np.sum(np.power(abs_diff, 10), axis=(1, 2)), .1)
        result['l_inf'] = np.max(abs_diff, axis=(1, 2))

        _pd_logger.debug(self._loggingBaseNotice
                         + ': PD calculated.')

        self._data = result

        if self.releaseDataMemory:
            # Accessing the data modality's data causes it to be
            # loaded into memory. Keeping it there may cause memory
            # overflow. This releases the memory.
            self.dataModality.data = None
