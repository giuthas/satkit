import logging
from typing import List

import nestedtext
import numpy as np
from satkit.constants import Suffix
from satkit.data_structures import Session

_session_saver_logger = logging.getLogger('satkit.session_saver')
