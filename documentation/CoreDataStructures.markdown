# Core Datastructures

```mermaid
classDiagram
    class Recording{
        Modalities modalities
        RecordingMetaData meta
    }

    class RecordingMetaData{
        str speaker
        time time_of_recording
        str prompt 
    }

    class Modality{
        ModalityData data
        dict meta
    }

    class ModalityData{
        numpy.ndarray data
        numpy.ndarray time
        float sampling_frequency
    }

    Recording "1" o-- "0..*" Modality
    Recording o-- "1" RecordingMetaData
    Recording o-- "1" TextGrid

    Modality o-- "1" ModalityData

```

A Recording represents data from one source -- for example ultrasound recorded with AAA along with an audio track. The differenet datatypes are represented by preferrably direct subclasses of Modality.

RecordingMetaData contains information on who and what was recorded, but not redundant information such as what kind of data.
