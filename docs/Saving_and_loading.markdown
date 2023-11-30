# Saving and Loading Data

SATKIT distinguishes between importing and loading, as well as exporting and saving. Importing and exporting are used (as consistently as possible) of the operations for data coming in from sources other than SATKIT and going out for use by other systems. Saving and loading on the hand refer to data produced by SATKIT for its own use.

## Basic design principles for saving and loading

1. Keep files human-readable when possible. This does not necessarily mean
   human-editable, but comes close to it.
2. High degree of modularity. We want each bit of metadata stored at the correct
   level. If the metadata refers to a Modality, it should be in that Modality's
   meta file; if it refers to the Recording, in the Recordings meta file; if to
   the whole Trial, in the Trials meta file; etc.
3. Keep redundancy as low as possible. For example, this means that frame rate
   of an ultrasound video is only stored in the (externally generated)
   ultrasound parameter file and not as part of SATKIT generated metadata.
4. Break the rules when they make life difficult. For example, in future the
   sampling frequency of a wav (and possibly its duration) might be stored in
   the Recording's metafile to make it unnecessary to open the `.wav` file to
   just get this sort of implicit metadata. A valid reason for doing something
   like this is, if the overhead from doing multiple disk reads starts to
   matter. This is very unlikely though with modern drives.
5. Backwards compatibility. This will be mainly taken care of by keeping
   importers for old versions of the files as part of SATKIT when changes are
   made to how the save formats work. For this purpose the metafiles will always
   contain a SATKIT file version number -- separate from SATKIT version number
   -- which will tell SATKIT which importer to use and also tell an old version
   of SATKIT that it is outdated and unable to open a given save if that is the
   case.

## Versioning

Starting from version 1.0 SATKIT file formats will be versioned separately from
versions of SATKIT itself. Until then, no attempts are made for backwards
compatibility.

## File names

The file names are made up of two or three parts separated by dots:

1. Basename - this is the name of the corresponding `.wav` file.
2. Modality name - the Modality's name attribute with whitespace converted to underscores if this file is specific to a Modality.
3. Suffix - either `.npz` or `.satkit_meta`. Former is for data stored in a numpy zip format and latter is for metadata stored as [NestedText](https://nestedtext.org/en/stable/index.html).

> **Example:**
>
> `File005.PD_l2_on_RawUltrasound.satkit`. This is the data for PD calculated with the l2 metric on raw ultrasound data for Recording File005. The metadata for the same Modality will be `File005.PD_l2_on_RawUltrasound.satkit_meta`, while the enclosing Recording's metadata will be stored in `File005.satkit_meta`.

The filenames themselves are not used by SATKIT currently to figure out what a
given file contains. Rather that bit of information is just for human readability.

## File name suffixes in code

SATKIT defines an Enum for valid suffixes in satkit.constants.
