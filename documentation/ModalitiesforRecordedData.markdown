# Modalities for Recorded Data

```mermaid
classDiagram
    class Modality{
        ModalityData data
        dict meta
    }

    Modality <|-- MonoAudio
    Modality <|-- RawUltrasound
    Modality <|-- Video
    Modality <|-- ThreeDUltrasound
    Modality <|-- Flow

```
