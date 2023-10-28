# Splines

While SATKIT does not generate splines it can handle them as a Modality. Since
the formats in which splines are saved vary quite a bit, SATKIT needs a helping
hand in understanding how to read the files. This happens in the form of a YAML
file, such as those in the included spline sample directories.

## Import configuration files

The file should always be called 'csv_spline_import_config.yaml' and follow the
format of the example below. The comments in the file (this is one of the
example ones) explain the role of each parameter.

```yaml
# Single spline file for all recordings (True) or one for each recording
# (False).
single_spline_file: True

# Only one of the following will be in use.
# If a single spline file, what is it called.
spline_file: File003_splines.csv
# If not a single spline, what glob pattern should be used to find the splines.
# E.g. '*.csv'
spline_file_glob: '*.csv'

# Do the files have a header row?
# Please note that possible header row information is ignored.
headers: True

# Either 'polar' or 'Cartesian' 
coordinates: polar

# Are the coordinates interleaved in 
#  interleaved format (True): point1/x point1/y point2/x point2/y
#  or non-interleaved (False): point1/x point2/x ... point1/y point2/y
interleaved_coords: False

# These are listed in order of appearance in the file. 
# Please note that possible header row information is ignored.
# Accepted values:
  # - ignore: marks a column to be ignored, unlike the others below, 
  #   can be used several times
  # - id: used to identify the speaker, 
  #   often contained in a csv field called 'family name'
  # - given names: appended to 'id' if not marked 'ignore'
  # - date and time: dat3 and time of recording
  # - prompt: prompt of recording, used to identify the recording with 'id'
  # - annotation label: optional field containing annotation information
  # - time in recording: timestamp of the frame this spline belongs to
  # - number of spline points: number of sample points in the spline used 
  #   to parse the coordinates and possible confidence information
meta_columns:
  - id
  - date and time
  - time in recording
  - prompt
  - number of spline points

# These will be either interleaved or not as specified by 'interleaved coords'.
# Confidence values are always assumed to be non-interleaved.
# Accepted values: 'r' with 'phi', 'x' with 'y', and 'confidence'
data_columns:
  - r
  - phi
  - confidence
```
