
class SatkitError(Exception):
    """Base class of SATKIT Errors."""
    pass

class MissingDataError(SatkitError):
    """
    Raised by Modality if data is requested but unavailable.
    
    This Error signifies that a Modality was created without providing either a
    path to files to load or an algorithm for deriving the Modality from another
    Modality.
    """
    pass

