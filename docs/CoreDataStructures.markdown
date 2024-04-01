# Core Data Structures

Dataset is a collection of Sessions (see below for details on which kind they
might be), most usually RecordingSession which in turn are a collection of the
different data Modalities recorded from a single Participant. Finally
Modalities are collections of not only data but also Annotations of that data.

In future RecordingSessions will either be expanded or get a sibling class to
represent Sessions that have more than one Participant.

The below UML graph does not show all of the members of the classes, but rather
only the most important ones. For a full description, please refer to the API
documentation and the code itself.

![core data structures](core_data_structures.drawio.png)

## Structures as Concrete Collections

For ease of use all classes containing a list or a dict of their major
components **are** Python lists and dicts of those components:

* Dataset is a list of Sessions (either RecordingSessions or possibly
  TrialSessions).
* RecordingSession is a list of Recordings, TrialSession is a list of Trials.
  The difference between a Recording and a Trial is that a Recording involves
  one participant, but a Trial may involve several and consists will have one
  Recording for each Participant.
* Recordings are dictionaries of Modalities.
* Modalities are dictionaries of Annotations. This maybe slightly unintuitive,
  since the 'beef' of a Modality is its data. However, accessing the
  Annotations is also important.

Accessing the components in a Pythonic manner is encouraged, but setting them
that way may lead to to problems. Use instead accessors like
`Recording.add_modality`.

## What Else is Contained: Metadata and Others

Dataset represents a single experiment with possibly multiple Participants and
each with possibly multiple Sessions (RecordingSessions or otherwise). While
Dataset contains a full dictionary of all of the participants, the Sessions
only have references to the Participants that took part in the Session.

A Recording represents data from one source -- for example ultrasound recorded
with AAA along with an audio track. The different datatypes -- both recorded
and derived -- are represented by direct subclasses of Modality.

If there are multiple data sources for one or more Participants, they each get
their own Recording. RecordingMetaData contains information on what was
recorded and when, but not redundant information such as what kind of data. In
addition, each Recording has a TextGrid (or rather a SatGrid, see API docs),
which is a dict of Tiers which are lists of either Intervals or Points.

Besides being a dictionary of Annotations, each Modality contains metadata --
both general and specific to the type of Modality -- and the actual data of the
Modality along with its timevector. These are primarily wrapped as a
ModalityData object but also available as `Modality.data, Modality.timevector`
and `Modality.timeoffset` for convenience.

The data field in ModalityData has a standardised axes order so that algorithms
will work on unseen data. The general order is [time, coordinate axes and
datatypes, data points] and further structure. For example stereo audio data
would be [time, channels] or just [time] for mono audio. For a more complex
example, splines from AAA have [time, x-y-confidence, spline points] or [time,
r-phi-confidence, spline points] for data in polar coordinates.
