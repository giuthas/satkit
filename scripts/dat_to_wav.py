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

from satkit.import_formats.rasl_dat_to_wav import dat_to_wav
from pathlib import Path
import time
import sys

# setting path
sys.path.append('../satkit')


def main(args):
    dat_dir = Path(args.pop())
    wav_dir = dat_dir.with_stem("WAV")

    if not wav_dir.is_dir():
        wav_dir.mkdir()

    for dat in dat_dir.glob('*.dat'):
        wav = wav_dir/dat.name
        wav = wav.with_suffix('.wav')
        dat_to_wav(dat, wav)


if (len(sys.argv) not in [2]):
    print("\ndat_to_wav.py")
    print("\tusage: dat_to_wav.py dat_dir")
    print("\n\tConverts dat files in dat_dir to wav files and creates a directory for them.")
    print("\tThe wav file directory will be formed by changin 'DAT' to 'WAV' in the dat directory path's end.")
    sys.exit(0)


if (__name__ == '__main__'):
    start_time = time.perf_counter()
    main(sys.argv[1:])
    elapsed_time = time.perf_counter() - start_time
    print(f'Elapsed time was {elapsed_time}.')
