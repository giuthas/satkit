#
# Copyright (c) 2019-2025
# Pertti Palo, Scott Moisik, Matthew Faytak, and Motoki Saito.
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

from contextlib import closing
from pathlib import Path

import numpy as np
import scipy.io.wavfile as sio_wavfile


def dat_to_wav(datpath: Path, wavpath: Path):
    with closing(open(datpath, 'rb')) as dat_file:
        # Matlab version does a test here to decide if the
        # recording is from Labview or RASL 1.0.
        # We don't. We just blindly assume RASL 1.0
        raw_data = dat_file.read()
        data = np.frombuffer(raw_data, dtype='float')
        diffData = data[1:]-data[0]
        threshold = 0.0001
        numberOfChannels = np.median(
            np.diff(np.nonzero(np.abs(diffData) < threshold)))
        numberOfChannels = int(numberOfChannels)
        if len(data) % numberOfChannels == 0:
            data.shape = [int(len(data)/numberOfChannels),
                          numberOfChannels]

        # The commented out section below tries to replicate the batchDAT2WAV
        # behaviour but something makes difference 1D when it should be 2D.
        # Since we are for the moment dealing with a steady data source,
        # we just hardcode the variables instead.

        # print(data.shape)
        # print(data[:8,:])

        # difference = np.diff(np.flipud(data[:,0]))

        # print(np.flipud(data[:,3]).shape)
        # plt.plot(data[:,3])
        # plt.show()

        # idx = np.nonzero(difference >= 2)#[0]
        # idx = len(data[:,3]) - idx + 1
        # data = data[:idx, :]

        # # Define the DAT variables
        # temp = np.diff(np.nonzero(data[:,0]>=1))/np.diff(data(np.nonzero(data[:,0]>=1)))
        # sampling_rate = np.round(np.median(temp))
        # if sampling_rate != 48000:
        #     print(f'Calculated sampling rate {sampling_rate} is not equal to 48kHz.')
        #     sampling_rate = 48000
        # data = data/np.repmat(np.max(np.abs(data)), data.shape[0],1)

        channel = 1  # second channel
        sampling_rate = 48000
        sound = data[:, channel]
        sound = sound/np.max(np.abs(sound))*0.99

        with closing(open(wavpath, 'wb')) as wav_file:
            sio_wavfile.write(wav_file, sampling_rate, sound)
            print(f"Wrote a new wav {wavpath}.")
