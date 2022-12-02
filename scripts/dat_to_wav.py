
import sys

# setting path
sys.path.append('../satkit')

import time
from pathlib import Path

from satkit.formats.rasl_dat_to_wav import dat_to_wav


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
