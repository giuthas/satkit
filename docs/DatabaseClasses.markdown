
# Database Classes

At time of writing (before release of 1.0) Dataset and Participant are only tentative. The rest will be part of either 1.0 or 1.1.

```mermaid
classDiagram
    direction LR
    class Dataset{
        Modalities modalities
        RecordingMetaData meta
    }

    class Participant{
        ModalityData data
        dict meta
    }

    class Session{
        ModalityData data
        dict meta
    }

    class Trial{
        Modality parent
        ModalityData data
        dict meta
    }

    class Recording{
        Modality parent
        ModalityData data
        dict meta
    }

    class Modality{
        Modality parent
        ModalityData data
        dict meta
    }

    Dataset o-- "0.n" Participant
    Participant o-- "0.n" Session
    Session o-- "0.n" Trial
    Trial o-- "0.n" Recording
    Recording o-- "0.n" Modality

```
