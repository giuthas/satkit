import abc

class Recording():
    """
    A recording contains 1-n Modalities and the non-modality 
    specific metadata (participant, speech content, etc).
    """

    def __init__(self):
        self.excluded = False
        self.meta = {}
        self.modalities = []
        self.timeOffSets = [] # Synchronisation time offsets
                              # corresponding to each modality.

        
class Modality(metaclass=abc.ABCMeta):
    """
    Abstract superclass for all recording classes.
    """

    def __init__(self):
        self.data = {} # To be used for only relatively small data vectors/matrices.
        self.meta = {}
        self.excluded = False
        

    @abc.abstractmethod
    def get_time_vector(self):
        """
        Return timevector corresponding to self.frames. This
        method is abstract to let subclasses either generate the timevector
        on the fly or preload or pregenerate it.
        """

        
class Ultrasound(Modality):
    """
    Abstract superclass for ultrasound recording classes.
    """

    def __init__(self):
        super.__init__()
        self._recording_type = "ultrasound"


    @abc.abstractmethod
    def get_ultrasound_data(self):
        """
        Return ultrasound frames. Generally the frames are read from a
        file when this method is called because keeping too much data in 
        memory leads to a crash due to memory running out.
        """
