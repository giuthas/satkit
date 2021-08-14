#
# Copyright (c) 2019-2021 Pertti Palo, Scott Moisik, and Matthew Faytak.
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
from contextlib import closing
import logging

# Numerical arrays and more
import numpy as np

# wav file handling
import scipy.io.wavfile as sio_wavfile

# Praat textgrids
import textgrids

# local modules
import satkit.audio as satkit_audio

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


    # should the modalities dict be accessed as a property?
    def add_modality(self, name, modality, replace=False):
        """
        This method adds a new Modality object to the Recording.

        Replacing a modality has to be specified otherwise if a
        Modality with the same name already exists in this Recording
        and the replace argument is not True, an Error is raised. 
        """
        if name in self.modalities.keys() and not replace:
            raise Exception("A modality named " + name +
                            " already exists and replace flag was False.")
        elif replace:
            self.modalities[name] = modality
            _recording_logger.debug("Replaced modality " + name + ".")
        else:
            self.modalities[name] = modality
            _recording_logger.debug("Added new modality " + name + ".")
            

class Modality(metaclass=abc.ABCMeta):
    """
    Abstract superclass for all Modality classes.

    If the data in a modality that implements this interface is going to be 
    large enough that it may not be possible to load it into memory for all recordings 
    being processed, then the implementations should come in two tiers: 1. an 'almost 
    concrete but still abstract' implementation with most functionality in place and 2. 
    a separate concrete implementation for a) loading the data when requested and b) 
    loading the data at init. Audio is an example of data that is not expected to run 
    into this problem. 
    """

    def __init__(self, name = None, parent = None, isPreloaded = True, timeOffset = 0):
        """
        Modality constructor.

        name is the name of this Modality and should be unique in this recording.
        parent is the parent Recording.
        isPreloaded is a boolean indicating if this instance reads the data from disc 
            on construction or only when needed.
        timeOffset (s) is the offset against the baseline audio track.
        """
        if parent == None or isinstance(parent, Recording):
            self.parent = parent
        else:
            raise TypeError("Modality given a parent which is not of type Recording " +
                            "or a decendant. Instead found: " + type(parent) + ".")
            
        self.isPreloaded = isPreloaded
        self.timeOffset = timeOffset

        # use self.parent.meta[key] to set parent metadata
        # certain things should be properties with get/set 
        self.meta = {}

        # This is a property which when set to True will also set parent.excluded to True.
        self.excluded = False

    @property
    @abc.abstractmethod
    def data(self):
        """
        Return the data of this Modality as a NumPy array. 
        
        This method is abstract to let subclasses either load the data
        on the fly or preload it.

        In either case, the dimensions of the array should be in the 
        order of [time, others]
        """
        
    @data.setter
    @abc.abstractmethod
    def data(self, data):
        """
        Abstract data setter method.
        """

    @property
    def excluded(self):
        return self.__excluded


    @excluded.setter
    def excluded(self, excluded):
        self.__excluded = excluded

        if excluded:
          self.parent.excluded = excluded  
            
    @property
    def timeOffset(self):
        return self.__timeOffset


    @timeOffset.setter
    def timeOffset(self, timeOffset):
        self.__timeOffset = timeOffset
        if self.isPreloaded:
            self.__time_vector = self.time_vector + (timeOffset - self.time_vector[0])

    @property
    @abc.abstractmethod
    def time_vector(self):
        """
        Return the timevector corresponding to self.data as a NumPy array. 
        
        This method is abstract to let subclasses either generate the timevector
        on the fly or preload or pregenerate it.
        """


    @time_vector.setter
    @abc.abstractmethod
    def time_vector(self, time_vector):
        """
        Set the timevector corresponding to self.data. 
        
        This method is abstract to let subclasses decide if they allow this.
        """


class MonoAudio(Modality):
    """
    A mono audio track. 

    Audio does not use the two tier implementation because the audio data is assumed to be small
    enough to fit in working memory.
    """

    def __init__(self, name = 'mono audio', parent = None, isPreloaded = True, timeOffset = 0, 
        filename = None, mainsFrequency = 50):
        """
        Create a MonoAudio track.

        filename should be either None or the name of a wav-file.
        mainsFrequency (Hz) is the mains frequency of the place of recording. 
            When detecting the recording onset beep, the audio is high pass 
            filtered with this frequency as the high end of the stop band.
            The frequency should be checked locally, if not clear from here
            https://en.wikipedia.org/wiki/Mains_electricity_by_country .
        """

        super.__init__(name, parent, isPreloaded, timeOffset)

        self.meta['filename'] = filename
        self.meta['mainsFrequency'] = mainsFrequency

        # If we do not have a filename, there is not much to init.
        if filename is None:
            return self
        
        (wav_fs, wav_frames) = sio_wavfile.read(filename)
        self.meta['wav_fs'] = wav_fs
        self.data = wav_frames
        
        # before v1.0: the high_pass filter coefs should be generated once for a set of recordings
        # rather than create overhead everytime the code is run
        #
        # Good place to do this would actually be in the satkit_audio module. Make a detector object or something.
        #
        # setup the high-pass filter for removing the mains frequency (and anything below it)
        # from the recorded sound.
# needs work: the high_pass filter coefs should be generated once for a set of recordings rather than create overhead everytime a new recording is processed.
        b, a = satkit_audio.high_pass(wav_fs, mainsFrequency)
        beep_uti, has_speech = satkit_audio.detect_beep_and_speech(wav_frames,
                                                                   wav_fs,
                                                                   b, a,
                                                                   filename)

        # before v1.0: this is a bad name for the beep: 1) this is an AAA thing,
        # 2) the recording might not be UTI
        self.meta['beep_uti'] = beep_uti
        self.meta['has_speech'] = has_speech
        
        self.__time_vector = np.linspace(0, len(wav_frames), 
                                         len(wav_frames),
                                         endpoint=False)
        self.__time_vector = self.__time_vector/wav_fs + self.timeOffset

    @property
    def data(self):
        """
        Return the data of this Modality as a NumPy array. 
        
        This method is abstract to let subclasses either load the data
        on the fly or preload it.

        In either case, the dimensions of the array should be in the 
        order of [time, others]
        """
        return self.__data
        
    @data.setter
    def data(self, data):
        """
        Data setter method.
        """
        self.__data = data

    @property
    def time_vector(self):
        return self.__time_vector    

    @time_vector.setter
    def time_vector(self, time_vector):
        self.__time_vector = time_vector
        self.timeOffset = time_vector[0]


# dynamically loading things have a problem with time vector generation.
# this may be taken care of by initing the timevector
# on first call and raising an exception if somebody tries to access the vector before - or
# even just generating it on the fly by loading and discarding the data
# this may be a really bad idea though, because it has a failure mode of
# ask_for_time_vec(); triggers drive access, now that we have time_vec ask_for_data();
# triggers drive access again...
class AbstractAAAUltrasound(Modality):
    """
    Abstract superclass for ultrasound recording classes.
    """

    def __init__(self, name = 'abstract ultrasound', parent = None, isPreloaded = True, timeOffset = 0, 
        filename = None, meta_filename = None, meta_dict = None):
        super.__init__(name, parent, timeOffset)

        self.meta['ultrasound_file'] = filename
        self.meta['meta_file'] = meta_filename
        
        if meta_dict != None:
            self.meta.update(meta_dict)
            self.meta['FramesPerSec'] = meta['FramesPerSec']
            self.meta['NumVectors'] = meta['NumVectors']
            self.meta['PixPerVector'] = meta['PixPerVector']
            self.meta['TimeInSecsOfFirstFrame'] = meta['TimeInSecsOfFirstFrame'] # this goes in timeOffset, not here
    
        
    @property
    @abc.abstractmethod
    def raw_ultrasound(self):
        """
        Raw ultrasound frames of this recording. 

        super().__init__(name=name, parent=parent, timeOffset=timeOffset, data=data)
        The frames are either read from a file when needed to keep memory needs 
        in check, or if using large amounts of memory is not a problem, they can be 
        preloaded when the object is created.

        Inheriting classes should raise a sensible error if they only contain
        ultrasound video data.
        """

    @property
    @abc.abstractmethod
    def interpolated_ultrasound(self):
        """
        Interpolated ultrasound frames. 

        These should never be stored in memory but rather dynamically generated as needed
        unless the class represents a video ultrasound recording, in which case the frames
        should be loaded into memory before they are needed only if running out of memory will
        not be an issue (i.e. there is a lot of it available).
        """

        
class DynRawUltrasound(AbstractAAAUltrasound):
    """
    Ultrasound Recording with dynamically loaded raw (probe return) data.
    """

    def __init__(self, name = 'raw tongue ultrasound', parent = None, isPreloaded = True, timeOffset = 0, filename = None):
        super.__init__(name, parent, timeOffset, filename)


    @property
    def raw_ultrasound(self):
        """
        Raw ultrasound frames of this recording as a 3D numpy array. 

        The frames are read from a file when needed to keep memory needs 
        in check.

        Output array has the dimensions [frames, scanlines, pixels].
        """
        with closing(open(self.meta['ultrasound_file'], 'rb')) as ult_file:
            ult_data = ult_file.read()
            ultra = np.fromstring(ult_data, dtype=np.uint8)
            ultra = ultra.astype("float32")
            
            self.meta['no_frames'] = int(len(ultra) / (self.meta['NumVectors']*self.meta['PixPerVector']))
            return ultra.reshape((self.meta['no_frames'], self.meta['NumVectors'], self.meta['PixPerVector']))


    @raw_ultrasound.setter
    def raw_ultrasound(self):  
        """
        Writing over dynamically loaded data is not currently possible. 

        NOTE: Not implemented yet. Calling this method will raise an error.
        """
        raise NotImplementedError('Writing over dynamically loaded raw ultrasound data has not been implemented yet.')


    @property
    def interpolated_ultrasound(self):
        """
        Interpolated ultrasound frames. 

        These are dynamically generated as needed.

        NOTE: Not implemented yet. Calling this method will raise an error.
        """

        # before v1.0: consider implementing this
        raise NotImplementedError('Conversion from raw data to video has not been implemented yet.')

    
    @interpolated_ultrasound.setter
    def interpolated_ultrasound(self):  
        """
        Writing over dynamically loaded data is not currently possible. 

        NOTE: Not implemented yet. Calling this method will raise an error.
        """
        raise NotImplementedError('Writing over dynamically loaded ultrasound data has not been implemented yet.')



class StaticRawUltrasound(AbstractAAAUltrasound):
    """
    Ultrasound Recording with dynamically loaded raw (probe return) data.
    """

    def __init__(self, name = 'raw tongue ultrasound', parent = None, isPreloaded = True, timeOffset = 0, filename = None):
        super.__init__(name, parent, timeOffset, filename)

        with closing(open(self.meta['ultrasound_file'], 'rb')) as ult_file:
            ult_data = ult_file.read()
            ultra = np.fromstring(ult_data, dtype=np.uint8)
            ultra = ultra.astype("float32")
            
            self.meta['no_frames'] = int(len(ultra) / (self.meta['NumVectors']*self.meta['PixPerVector']))
            self.__raw_ultrasound = ultra.reshape((self.meta['no_frames'], self.meta['NumVectors'], self.meta['PixPerVector']))


    @property
    def raw_ultrasound(self):
        """
        Raw ultrasound frames of this recording as a 3D numpy array. 

        Output array has the dimensions [frames, scanlines, pixels].
        """
        return self.__raw_ultrasound


    @raw_ultrasound.setter
    def raw_ultrasound(self, raw_ultrasound):  
        """
        Replaces the raw ultrasound data of this recording. 

        NOTE: Not fully implemented yet. Calling this method will raise an error.
        """
        raise NotImplementedError('Writing over dynamically loaded raw ultrasound data has not been implemented yet.')

        # there needs to be type checking and meta data will need to be updated
        self.__raw_ultrasound = raw_ultrasound



    @property
    def interpolated_ultrasound(self):
        """
        Interpolated ultrasound frames. 

        These are dynamically generated as needed.

        NOTE: Not implemented yet. Calling this method will raise an error.
        """

        # before v1.0: consider implementing this
        raise NotImplementedError('Conversion from raw data to video has not been implemented yet.')


    @interpolated_ultrasound.setter
    def interpolated_ultrasound(self):  
        """
        Writing over dynamically generated videos is not currently possible. 

        NOTE: Not implemented yet. Calling this method will raise an error.
        """
        raise NotImplementedError('Writing over dynamically generated ultrasound videos has not been implemented yet.')



class VideoUltrasound(AbstractUltrasound):
    """
    Ultrasound video Recording -- does not contain raw data.

    This is the dynamically loading version and as such does not load the ultrasound data 
    before it is actually accessed. While some metadata will only be populated once the video
    has been loaded, it should be noted that the video itself will not be kept in memory 
    by instances of this class. Rather every time the interpolated_ultrasound property of 
    an instance is accessed, there will be a hard drive operation. 
    """

    def __init__(self, name = 'video ultrasound', parent = None, isPreloaded = True, timeOffset = 0, filename = None):
        super.__init__(name, parent, timeOffset, filename)


    @property
    def raw_ultrasound(self):
        """
        Raw ultrasound frames of this recording. 

        The frames are either read from a file when needed to keep memory needs 
        preloaded when the object is created.

        NOTE: Not implemented yet and might never be. Calling this method will raise an error.
        """
        raise NotImplementedError('There is currently no conversion from video ultrasound data to raw data.')

        
    @property
    @abc.abstractmethod
    def interpolated_ultrasound(self):
        """
        Interpolated ultrasound frames. 

        These should never be stored in memory but rather dynamically generated as needed
        unless the class represents a video ultrasound recording, in which case the frames
        should be loaded into memory before they are needed only if running out of memory will
        not be an issue (i.e. there is a lot of it available).
        
        NOTE: Not implemented yet.
        """
        
        raise NotImplementedError('There is currently no conversion from video ultrasound data to raw data.')
        # This will be implemented with something like:
        #return self.__video
        # in the static loading case. Otherwise disk reading goes here.
        

        
# dynamically loading things have a problem with time vector generation.
# this may be taken care of by initing the timevector
# on first call and raising an exception if somebody tries to access the vector before - or
# even just generating it on the fly by loading and discarding the data
# this may be a really bad idea though, because it has a failure mode of
# ask_for_time_vec(); triggers drive access, now that we have time_vec ask_for_data();
# triggers drive access again...
class AbstractVideo(Modality):
    """
    Abstract superclass for video recording classes.
    """

    def __init__(self, name = 'video ultrasound', parent = None, isPreloaded = True, timeOffset = 0, filename = None):
        super.__init__(name, parent, timeOffset, filename)



    @property
    @abc.abstractmethod
    def video(self):
        """
        Video frames of this recording. 

        The frames are either read from a file when needed to keep memory needs 
        in check, or if using large amounts of memory is not a problem, they can be 
        preloaded when the object is created.
        """


class LipVideo(AbstractVideo):

    def __init__(self, name = 'video ultrasound', parent = None, isPreloaded = True, timeOffset = 0, filename = None):
        super.__init__(name, parent, timeOffset, filename)
