# Core Data Structures

![core data structures](core_data_structures.drawio.png)

A Recording represents data from one source -- for example ultrasound recorded with AAA along with an audio track. The different datatypes are represented by preferrably direct subclasses of Modality.

RecordingMetaData contains information on who and what was recorded, but not redundant information such as what kind of data.

The data field in ModalityData has a standardised axes order so that algorithms
will work on unseen data. The general order is [time, coordinate axes and
datatypes, datapoints] and further structure. For example stereo audio data
would be [time, channels] or just [time] for mono audio. For a more complex
example, splines from AAA have [time, x-y-confidende, spline points] or [time,
r-phi-confidence, spline points] for data in polar coordinates.
