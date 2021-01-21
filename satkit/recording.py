#
# Copyright (c) 2019-2020 Pertti Palo, Scott Moisik, and Matthew Faytak.
#
# This file is part of Speech Articulation ToolKIT 
# (see https://github.com/giuthas/satkit/).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# The example data packaged with this program is licensed under the
# Creative Commons Attribution-NonCommercial-ShareAlike 4.0
# International (CC BY-NC-SA 4.0) License. You should have received a
# copy of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0
# International (CC BY-NC-SA 4.0) License along with the data. If not,
# see <https://creativecommons.org/licenses/by-nc-sa/4.0/> for details.
#
# When using the toolkit for scientific publications, please cite the
# articles listed in README.markdown. They can also be found in
# citations.bib in BibTeX format.
#

# Built in packages
import abc
import logging

# Praat textgrids
import textgrids

_recording_logger = logging.getLogger('satkit.recording')

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
        self.modalities = {}


    def read_textgrid(self):
        """
        Tries to open the textgrid specified in self.meta.

        Currently it is a fatal error to call this function either before self.meta has been 
        iniatialised or if the self.meta['textgrid'] is not a valid path to a valid textgrid.
        This may change in the future.
        """
        try:
            self.textgrid = textgrids.TextGrid(self.meta['textgrid'])
        except:
            _recording_logger.critical("Could not read textgrid in " + filename + ".")
            self.textgrid = None

        return grid


    def add_modality(self, name, modality, replace=False):
        """
        This method adds a new Modality object to the Recording.

        Replacing a modality has to be specified otherwise if a
        Modality with the same name already exists in this Recording
        and the replace argument is not True, an Error is raised. 
        """
        if name in self.modalities.keys() and not replace:
# this needs a suitable error
# should the modalities be accessed as a property?
            raise
        else:
            self.modalities[name] = modality
            
    
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
