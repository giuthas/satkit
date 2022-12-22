# Core Data Structures

![core data structures](core_data_structures.drawio.png)

A Recording represents data from one source -- for example ultrasound recorded with AAA along with an audio track. The differenet datatypes are represented by preferrably direct subclasses of Modality.

RecordingMetaData contains information on who and what was recorded, but not redundant information such as what kind of data.
