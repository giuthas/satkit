import abc

# Praat textgrids
import textgrids

class Recording():
    """
    A Recording contains 1-n synchronised Modalities.

    The recording also contains the non-modality 
    specific metadata (participant, speech content, etc) 
    as a dictionary, so that it can be easily written 
    to .csv files.
    """

    def __init__(self):
        self.excluded = False
        self.meta = {}
# maybe a dict?
        self.modalities = []


    def read_textgrid(self):
        # Try to open the file as textgrid
        try:
            grid = textgrids.TextGrid(self.textgridname)
        except:
            _recording.logger.critical("Could not read textgrid in " + filename + ".")
            grid = None

        return grid

        
#
#Dynamic loadin or not should be a thing here
#
class Modality(metaclass=abc.ABCMeta):
    """
    Abstract superclass for all Modality classes.
    """

    def __init__(self, parent = None, timeOffSet = 0, data = None):
        if parent == None or isinstance(parent, Recording):
            self.parent = parent
        else:
            raise TypeError("Modality given a parent which is not of type Recording or a decendant: " +
                            type(parent))
            
        self.timeOffSet = timeOffset
        self.data = data # Do not load data here unless you are sure their will be enough memory.

        # use self.parent.meta[key] to set parent metadata
        # certain things should be properties with get/set 
        self.meta = {}

        # This is a property that when set to True will also set parent.excluded to True.
        self.excluded = False

    @property
    def excluded(self):
        return self.__excluded

    @excluded.setter
    def excluded(self, excluded):
        self.__excluded = excluded

        if excluded:
          self.parent.excluded = excluded  

            
# this should be a property
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


    @abc.abstractmethod
    @property
    def raw_ultrasound(self):
        """
        Raw ultrasound frames of this recording. 

        The frames are either read from a file when needed to keep memory needs 
        in check or if using large amounts of memory is not a problem they can be 
        preloaded when the object is created.

        Inheriting classes should raise a sensible error if they only contain
        ultrasound video data.
        """

    @abc.abstractmethod
    @property
    def interpolated_ultrasound(self):
        """
        Interpolated ultrasound frames. 

        These should never be stored in memory but rather dynamically generated as needed
        unless the class represents a video ultrasound recording, in which case the frames
        should be loaded into memory before they are needed only if running out of memory will
        not be an issue (i.e. there is a lot of it available).
        """

#when implementing do
# @raw_ultrasound.setter
# and put the getting thing in the raw_ultrasound(self) method
# etc
