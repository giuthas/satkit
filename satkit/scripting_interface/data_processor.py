
import datetime
from typing import Dict, List

from satkit.data_structures import Recording

from . import logger


def process_data(recordings: List[Recording], processing_functions: Dict, arguments) -> None:
    # calculate the metrics
    for recording in recordings:
        if recording.excluded:
            continue

        for key in processing_functions:
            (function, modalities) = processing_functions[key]
            # TODO: Version 1.0: add a mechanism to change the arguments for different modalities.
            for modality in modalities:
                function(
                    recording,
                    modality,
                    preload=True,
                    release_data_memory=True)

    logger.info('Data run ended at %s.', str(datetime.datetime.now()))
