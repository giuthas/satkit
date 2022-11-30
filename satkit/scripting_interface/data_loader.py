

from pathlib import Path
from typing import List

import satkit.io as satkit_io
from satkit.configuration import data_run_params
from satkit.data_import import generate_aaa_recording_list
from satkit.data_structures import Recording

from . import logger


def load_data(path: Path) -> List[Recording]:
    """Handle loading data from individual files or a previously saved session."""
    if not path.exists():
        logger.critical(
            'File or directory does not exist: %s.', path)
        logger.critical('Exiting.')
        quit()
    elif path.is_dir():
        # this is the actual list of recordings that gets processed
        # token_list includes meta data contained outwith the ult file
        recordings = read_data_from_files()
    elif path.suffix is '.pickle':
        recordings = satkit_io.load_pickled_data(path)
    elif path.suffix is '.json':
        recordings = satkit_io.load_json_data(path)
    else:
        logger.error(
            'Unsupported filetype: %s.', path)
    
    return recordings

def read_data_from_files(self):
    """
    Wrapper for reading data from a directory full of files.

    Having this as a separate method allows subclasses to change
    arguments or even the parser.

    Note that to make data loading work the in a consistent way,
    this method just returns the data and saving it in a
    instance variable is left for the caller to handle.
    """
    if self.args.exclusion_filename:
        data_run_params['data properties']['exclusion list'] = Path(
            self.args.exclusion_filename)

    recordings = generate_aaa_recording_list(
        self.args.load_path)
    return recordings

