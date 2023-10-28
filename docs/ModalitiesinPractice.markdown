# Modalities in Practice

The diagram below shows an example of regular Modalities and a derived Modality in practice. The example is directly based on classes that will be instantieted when ultrasound data from AAA is loaded into SATKIT and PixelDifference is run on the data.

```mermaid
classDiagram
    class Recording{
        Modalities modalities
        RecordingMetaData meta
    }

    class MonoAudio{
        ModalityData data
        dict meta
    }

    class RawUltrasound{
        ModalityData data
        dict meta
    }

    class PixelDifference{
        Modality parent
        ModalityData data
        dict meta
    }


    Recording o-- "1" MonoAudio
    Recording o-- "1" RawUltrasound
    Recording o-- "0..n" PixelDifference

    RawUltrasound <.. PixelDifference : derived from

```

## Notes on specific Modalities

- [Splines in SATKIT](Splines.markdown)
