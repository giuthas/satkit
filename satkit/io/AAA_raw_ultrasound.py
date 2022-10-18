import datetime
import logging
from contextlib import closing
from pathlib import Path
from typing import Optional, Union

from data_structures import RawUltrasound, Recording

_AAA_raw_ultrsound_logger = logging.getLogger('satkit.AAA_raw_ultrasound')


def parse_aaa_promptfile(filepath: Union[str, Path]) -> dict:
    """
    Read an AAA .txt (not US.txt or .param) file and save prompt, 
    recording date and time, and participant name into the meta dictionary.
    """
    if isinstance(filepath, str):
        filepath = Path(filepath)

    meta = {}
    with closing(open(filepath, 'r', encoding="utf8")) as promptfile:
        lines = promptfile.read().splitlines()
        meta['prompt'] = lines[0]

        # The date used to be just a string, but needs to be more sturctured since
        # the spline export files have a different date format.
        meta['date_and_time'] = datetime.strptime(
            lines[1], '%d/%m/%Y %H:%M:%S')
        # TODO: hunt and remove uses of either date or date_and_time and use only one in the future.
        meta['date'] = meta['date_and_time']

        if len(lines) > 2 and lines[2].strip():
            meta['participant'] = lines[2].split(',')[0]
        else:
            _AAA_raw_ultrsound_logger.info(
                "Participant does not have an id in file %s.", filepath)
            meta['participant'] = ""

        _AAA_raw_ultrsound_logger.debug("Read prompt file %s.", filepath)
    return meta

def parse_ultrasound_meta_aaa(filename):
    """
    Parse metadata from an AAA export file into a dictionary.

    This is either a 'US.txt' or a '.param' file. They have
    the same format.

    Arguments:
    filename -- path and name of file to be parsed.

    Returns a dictionary which should contain the following keys:
        NumVectors -- number of scanlines in a frame
        PixPerVector -- number of pixels in a scanline
        ZeroOffset --
        BitsPerPixel -- byte length of a single pixel in the .ult file
        Angle -- angle in radians between two scanlines
        Kind -- type of probe used
        PixelsPerMm -- depth resolution of a scanline
        FramesPerSec -- framerate of ultrasound recording
        TimeInSecsOfFirstFrame -- time from recording start to first frame
    """
    meta = {}
    with closing(open(filename, 'r', encoding="utf8")) as metafile:
        for line in metafile:
            (key, value_str) = line.split("=")
            try:
                value = int(value_str)
            except ValueError:
                value = float(value_str)
            meta[key] = value

        _AAA_raw_ultrsound_logger.debug(
            "Read and parsed ultrasound metafile %s.", filename)
        meta['meta_file'] = filename
    return meta


def add_aaa_raw_ultrasound(recording: Recording, preload: bool,
                            path: Optional[Path]=None) -> None:
    """Create a RawUltrasound Modality and add it to the Recording."""
    if not path:
        ult_file = recording.path.with_suffix(".ult")
    else:
        ult_file = path

    meta = parse_ultrasound_meta_aaa(path)

    # We pop the timeoffset from the meta dict so that people will not
    # accidentally rely on setting that to alter the timeoffset of the
    # ultrasound data in the Recording. This throws KeyError if the meta
    # file didn't contain TimeInSecsOfFirstFrame.
    ult_time_offset = meta.pop('TimeInSecsOfFirstFrame')

    if ult_file.is_file():
        ultrasound = RawUltrasound(
            recording=recording,
            preload=preload,
            path=ult_file,
            parent=None,
            timeOffset=ult_time_offset,
            meta=meta
        )
        recording.addModality(ultrasound)
        _AAA_raw_ultrsound_logger.debug(
            "Added RawUltrasound to Recording representing %s.",
            recording.path.name)
    else:
        notice = 'Note: ' + ult_file + " does not exist."
        _AAA_raw_ultrsound_logger.warning(notice)
        recording.exclude()

