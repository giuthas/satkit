# SATKIT Release Notes

## Foreshadowing the next release: Version 0.10.0

- New functionality and configuration for extracting annotations and producing
  plots out of them.
- New two stage internal configuration model
  - Started rolling out a model where configuration files are still parsed with
    strictyaml to preserve comments in round tripping (which has not yet been
    implemented), but get reinterpreted as pydantic classes to make coding
    easier.

Known issues:

- To be determined

## Version 0.9.0

- Simulation
  - Two contours for running sensitivity simulations for contour metrics.
  - Perturbation generation for the contours.
  - Functions for running metrics on the simulated data.
  - Lots of plotting routines to look at the results.
  
Known issues:

Same as in 0.8.0.

## Version 0.8.0

- Splines
  - Spline loading from AAA export files.
  - Several spline metrics now work and can be displayed.
  - Splines can be displayed on the ultrasound frame.
- Some updates to clean the code in general.

Known issues:

- Same as in 0.7.0. plus
- Synchronising spline metrics and splines with ultrasound is currently
  unreliable. This is because the timestamps in spline files have proven to
  have either drift or just inaccuracies and testing why this is so is a job
  for the future. This may eventually be solved just by matching splines with
  ultrasound frames and reporting when that becomes too unreliable.

## Version 0.7.0

- Saving and loading to/from native formats for derived Modalities.
  - Saved data can be loaded on startup or opened afterwards. This means
    derived Modalities don't need to be re-generated every time and switching
    between recording sessions is fast.
  - Metadata of derived Modalities is now saved in human readable form while
    the numeric data is saved in numpy native formats.
  - Database is also saved in human readable formats for easy checking of data
    integrity.
  - Opening (ctrl+'o') and saving (ctrl+shift+'s') work in the GUI. Overwrites
    are verified when saving, but the logic of that part may change before 1.0.
    The most obvious alternative to approving overwrites on a file-by-file
    basis alongside the 'Yes to all' option, is to only have the latter.
- Zooming in, out and to all now works with 'i', 'o' and 'a' respectively.

Known issues:

- ctrl+'i' and ctrl+'a' zoom but ctrl+'o' is bound to opening a recording
  session. The fix will be removing the first two bindings which are
  unintentional.
