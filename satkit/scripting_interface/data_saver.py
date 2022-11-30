
from pathlib import Path
from typing import List

import satkit.io as satkit_io
from satkit.data_structures import Recording

from .logger import logger


def save_data(path: Path, recordings: List[Recording]):
    if path.suffix is '.pickle':
        satkit_io.save2pickle(
            recordings,
            path)
        logger.info(
            "Wrote data to file %s.", str(path))
    elif path.suffix is '.json':
        logger.error(
            'Unsupported filetype: %s.', str(path))
    else:
        logger.error(
            'Unsupported filetype: %s.', str(path))
