
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple, Union

# Efficient array operations
import numpy as np
from scipy import signal as scipy_signal


# TODO: Move this somewhere else and joing with teh same thing in plot.py.
class Normalisation(Enum):
    none = 'NONE'
    peak = 'PEAK'
    bottom = 'BOTTOM'
    both = 'PEAK AND BOTTOM'

@dataclass
class PeakData:
    """Peaks, their times, and properties as returned by scipy's find_peaks."""
    peaks: np.ndarray
    peak_times: np.ndarray
    properties: dict

def time_series_peaks(
        data: np.ndarray, 
        time: np.ndarray,
        time_lim: Tuple[float, float], 
        normalise: Normalisation='NONE',
        number_of_ignored_frames: int=10,
        distance: Optional[int]=10,
        prominence: Optional[float]=0.05):

    search_data = data[number_of_ignored_frames:]
    search_time = time[number_of_ignored_frames:]

    indeces = np.nonzero((search_time > time_lim[0]) & (search_time < time_lim[1]))
    search_data = search_data[indeces]
    search_time = search_time[indeces]

    if normalise in (Normalisation.both, Normalisation.bottom):
        search_data = search_data - np.min(search_data)
    if normalise in [Normalisation.both, Normalisation.peak]:
        search_data = search_data/np.max(search_data)

    peaks, properties = scipy_signal.find_peaks(search_data, 
                                distance=distance, prominence=prominence)

    peak_times = search_time[peaks]

    return PeakData(peaks, peak_times, properties)
