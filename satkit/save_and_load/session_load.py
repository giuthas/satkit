import logging
from pathlib import Path
from pprint import pprint
from typing import List

import nestedtext
import numpy as np
from pydantic import BaseModel
from satkit.configuration import config
from satkit.constants import Suffix
from satkit.data_structures import Session

_session_loader_logger = logging.getLogger('satkit.session_loader')
