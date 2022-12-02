
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
    print("\ncast.py")
    print("\tusage: cast.py [config strict yaml file]")
    print("\n\tConcatenates wav files and creates a corresponding TextGrid.")
    print("\tWrites a huge wav-file, a corresponding textgrid, and")
    print("\ta metafile to assist in extracting shorter textgrid after annotation.")
    print("\n\tAll options are provided by the config file which defaults to cast_config.yml.")
    sys.exit(0) 


if (__name__ == '__main__'):
    start_time = time.perf_counter()
    main(sys.argv[1:])
    elapsed_time = time.perf_counter() - start_time
    print(f'Elapsed time was {elapsed_time}.')
