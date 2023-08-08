from dataclasses import dataclass


@dataclass(frozen=True)
class Suffix():
    """
    Suffixes for files saved by SATKIT.
    
    These exist as a convenient way of not needing to risk typos. To see the
    whole layered scheme SATKIT uses see the 'Saving and Loading Data' section
    in the documentation.
    """
    CONFIG = ".yaml"
    DATA = ".npz"
    META = ".satkit_meta"

    def __str__(self):
        return self.value
