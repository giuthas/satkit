# Writing a New Modality

We separate data containment, creation (and related import/export/save/load and algorithmic generation), and modification. A new Modality class will be responsible for containing a new type of data, but not for creating itself nor for writing itself to files etc.

## Flow of Importing a Series of Recordings

Repeat this for each datasource:

- Run the import function: `generate_[datasource]_recordings`.
  - Read enough metadata to be able to create the Recording instances.
  - Exclude recordings based on the list of files and rules contained in the exclusion configuration file.
- For each recording add Modalities.
  - Run the individual Modality adding functions.
  - These functions will add the Modalities, but not necessarily load the data. Loading data is avoided when it is large and loading all of it may lead to the system running out of memory.

Finally,

- in a separate step run algorithms on Modalities and add the results to the Recordings

So depending on the case, to create a new Modality we may need to implement at least some of the following:

- A subclass of Modality -- in every case.
- An `add_[modality name]` function to create and add the new Modality to a
  Recording -- also in every case.
- If the datasource does not yet exist, a `generate_[datasource]_recordings` to create the Recording objects.

## What the New Modality Class should do?

Have a look in `satkit/modalities/modalities.py`. The classes deal with which functions to use for reading their data from files and what to do with possible metadata that needs to be stored. On top of that some of them have special case accessors like the `interpolated_image` and `interpolated_frames` in `RawUltrasound`. Other than that Modalities don't really do anything.

## Creating a Modality Instance

Assuming that the new Modality is a data Modality and not a derived one, it is going to need a read function that goes into `satkit/formats`. The reason these aren't tied to the import functions in `satkit/data_import` is that the same file format -- especially `wav` -- may get used by many datasources.

If a datasource already exists for the new Modality then there should already be an import function like `generate_aaa_recording`, but if not then that needs to be written to deal with reading Recording specific metadata and creating the Recording to contain the Modalities.

```mermaid
flowchart LR

    Modality


```

## Saving and Loading a Modality

The ModalityData part of the Modality should be written into its own file with the generic exporter routine `save_modality_data()`.

Other parts of the Modality should be saved to a [NestedText file](https://nestedtext.org/en/stable/). Implement a schema for doing so and for reading the saved data back.

Specifically we use a different save format for configuration and for (meta)data. With configuration, having a format that at least attempts to retain comments when read, edited, and written out again, is very desirable. For data this is less important but having an easier API is nice.

## An Example of a New Modality: MultiChannelAudio
