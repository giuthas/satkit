
import datetime
import logging
from typing import Optional

logger = None

def set_up_logging(verbosity: Optional[int]):
        """Set up logging with the logging module.

        Main thing to do is set the level of printed output based on the
        verbosity argument.
        """
        global logger
        logger = logging.getLogger('satkit')
        logger.setLevel(logging.INFO)

        # also log to the console at a level determined by the --verbose flag
        console_handler = logging.StreamHandler()  # sys.stderr

        # Set the level of logging messages that will be printed to
        # console/stderr.
        if not verbosity:
            console_handler.setLevel('WARNING')
        elif verbosity < 1:
            console_handler.setLevel('ERROR')
        elif verbosity == 1:
            console_handler.setLevel('WARNING')
        elif verbosity == 2:
            console_handler.setLevel('INFO')
        elif verbosity >= 3:
            console_handler.setLevel('DEBUG')
        else:
            logging.critical("Unexplained negative argument %s to verbose!",
                str(verbosity))
        logger.addHandler(console_handler)

        logger.info('Data run started at %s.', str(datetime.datetime.now()))
