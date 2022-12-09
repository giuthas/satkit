# Modalities for Derived Data

These Modalities are derived from another Modality by running an Algorithm on it.

```mermaid
classDiagram
    class Modality{
        ModalityData data
        dict meta
    }

    class RecordedDataAsModality{
        ModalityData data
        dict meta
    }

    class PixelDifference{
        Modality parent
        ModalityData data
        dict meta
    }

    class OpticFlow{
        Modality parent
        ModalityData data
        dict meta
    }

    class PrincipalComponentAnalysis{
        Modality parent
        ModalityData data
        dict meta
    }

    Modality <|-- RecordedDataAsModality
    Modality <|-- PixelDifference
    Modality <|-- OpticFlow
    Modality <|-- PrincipalComponentAnalysis
    PixelDifference ..> RecordedDataAsModality  : derived from
    OpticFlow ..> RecordedDataAsModality : derived from
    PrincipalComponentAnalysis ..> RecordedDataAsModality  : derived from


```
