
import logging
import time
from typing import Optional

start_time = time.time()
last_log_time = time.time()

_satkit_logger = logging.getLogger('satkit')

def set_logging_level(verbosity: Optional[int]):
        """Set up logging with the logging module.

        Main thing to do is set the level of printed output based on the
        verbosity argument.
        """
        logger = logging.getLogger('satkit')
        logger.setLevel(logging.DEBUG)

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
            logging.critical("Negative argument %s to verbose!",
                str(verbosity))
        logger.addHandler(console_handler)

        logger.info('Data run started.')
        
        return logger

def log_elapsed_time():
    """
    Log the time elapsed since logging began.
    
    Also logs the time since the last call to this function.
    """
    global start_time, last_log_time
    current_time = time.time()
    elapsed_time = current_time - start_time
    since_last_log = current_time - last_log_time
    log_text = 'Elapsed time from start: %f, from last logged time: %f'%(
        elapsed_time, since_last_log)
    _satkit_logger.info(log_text)
    last_log_time = current_time
