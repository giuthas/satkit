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
    Modality <|-- Splines

```

Since currently SATKIT does not generate splines, Splines is considered a recorded Modality, but it is at the same time a good example of why separating recorded and derived Modalities as different types is probably a bad idea: Splines might be external data provided as is, or they might in future also be produced by a module in SATKIT if somebody finds it a good idea to do so.
