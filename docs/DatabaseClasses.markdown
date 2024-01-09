
# Database Classes

For ease of use all classes containing a list or a dict of their major
components **are** lists and dicts of those components:

* Dataset is a list of Sessions (either RecordingSessions or TrialSessions).
* RecordingSession is a list of Recordings, TrialSession is a list of Trials.
  The difference between a Recording and a Trial is that a Recording involves
  one participant, but a Trial may involve several and consists will have one
  Recording for each Participant.
* Recordings are dictionaries of Modalities.
* Modalities are dictionaries of Annotations. This maybe slightly unintuitive,
  since the 'beef' of a Modality is its data. However, accessing the
  Annotations is also important.

Accessing the components in a Pythonic manner is encouraged, but setting them
that way, may lead to to problems.

At time of writing the existence of a Trial class is uncertain in 1.0. If there
is no Trial class only type of Session will be RecordingSession, which will be
a list of consist of Recordings.

```mermaid
classDiagram
    direction UD
    class Dataset{
        sessions: list[Session]
        participants: dict[Participant]
        metadata: DatasetMetadata
    }

    class Participant{
        id: str
        metadata: ParticipantMetadata
    }

    class RecordingSession{
        recordings: list[Recording]
        metadata: SessionMetadata
    }

    class Recording{
        modalities: dict[Modality]
        metadata: RecordingMetadata
    }

    class Modality{
        modality_data: ModalityData
        metadata: ModalityMetaData
        annotations: dict[Annotation]
    }

    class ModalityData{
        data: ndarray
        timevector: ndarray
        sampling_rate: float
    }

    class Annotation{
        times: ndarray
        properties: list[dict]
    }

    Dataset o-- "1.n" Participant
    Dataset o-- "1.n" RecordingSession
    RecordingSession o-- "1.n" Participant
    RecordingSession o-- "1.n" Recording
    Recording o-- "1.n" Modality
    Modality o-- "1" ModalityData
    Modality o-- "1.n" Annotation

```

In case Trial is included:

```mermaid
classDiagram
    direction UD
    class Dataset{
        sessions: list[Session]
        participants: dict[Participant]
        metadata: DatasetMetadata
    }

    class Participant{
        id: str
        metadata: ParticipantMetadata
    }

    class TrialSession{
        recordings: list[Recording]
        metadata: SessionMetadata
    }

    class Trial{
        participants: list[Participant]
        recordings: list[Recording]
    }

    class Recording{
        modalities: dict[Modality]
        metadata: RecordingMetadata
    }

    class Modality{
        modality_data: ModalityData
        metadata: ModalityMetaData
    }

    class ModalityData{
        data: ndarray
        timevector: ndarray
        sampling_rate: float
    }

    Dataset o-- "1.n" Participant
    Dataset o-- "1.n" TrialSession
    TrialSession o-- "1.n" Participant
    TrialSession o-- "1.n" Trial
    Trial o-- "1.n" Recording
    Trial o-- "1.n" Participant
    Recording o-- "1.n" Modality
    Modality o-- "1" ModalityData

```
