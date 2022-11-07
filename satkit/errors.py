
class SatkitError(Exception):
    """Base class of SATKIT Errors."""
    pass

class MissingDataError(SatkitError):
    """
    Data requested from Modality but is unavailable.
    
    This Error signifies that a Modality was created without providing either a
    path to files to load or an algorithm for deriving the Modality from another
    Modality.
    """
    pass

class ModalityError(SatkitError):
    """
    Modality already exists in Recording.
    """
    pass

class OverWriteError(SatkitError):
    """
    Trying to replace the data or timevector in a Modality with non-matching dtype, size, or shape.
    """
    pass
