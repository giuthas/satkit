=======
# Speech Image ToolKIT - SITKIT

Currently these tools are meant for processing ultrasound speech data
from both the tongue and the larynx. In the future the toolkit will
include facilities for processing other kinds of articulatory
data. The first two to be implemented are Optical Flow and Pixel
Difference.

Optical Flow tracks local changes in ultrasound frames and estimates
the flow field based on these. 

Pixel Difference and Scanline Based Pixel Difference -- work on raw,
uniterpolated data and produce measures of change over the course of a
recording. How they work is explained in Chapter 3 of Pertti Palo's
[PhD
thesis](https://eresearch.qmu.ac.uk/handle/20.500.12289/10163). The
next stage is a automated reaction time measure, followed possibly by
spline distance measures and optic flow.


## Getting Started

Download the repository to either a subdirectory of the project you
want to use the tools on or a suitable place that you then add to your
$PYTHONPATH. 


### Prerequisites

PD is written in Python3 and developed with version 3.7.4.

In addition to built in Python modules, to use the tools you will need
the following packages (or newer versions of them):
* MatPlotLib 3.1.1
* NumPy 1.17.2
* SciPy 1.3.1

A handy way of getting MatPlotLib, NumPy, and SciPy is to get them as
part of the [Anaconda
distribution](https://www.anaconda.com/distribution/#download-section).


### What's included

See
[manifest.txt](https://github.com/giuthas/pd/blob/master/manifest.txt)
for a description of the contents.


### Running the examples

There are three small datasets included in the distribution. You can
run tests on them with the test script `test_pd.py`. Currently the
following work and produce a new spaghetti_plot.pdf and a transcript
in `[directory_name].log`.

```
python test_pd.py test1_1
python test_pd.py test1_1 exclusion_list.csv
python test_pd.py test1_2
python test_pd.py test1_2 exclusion_list.csv
```

The first example directory contains recordings with all files present
while the second is intentionally missing some files. The latter case
should therefore produce warnings in the resulting log. Running
without the exclusion list specified should produce a plot with a
couple more curves in it.

The routines to deal with a directory structure like that of `test2`
are yet to be implemented.


## Running the tests

Proper testing is yet to be implemented.


## Contributing

Please get in touch with [Pertti](https://taurlin.org), if you would
like to contribute to the project.


## Versioning

We use [SemVer](http://semver.org/) for versioning under the rules as
set out by [PEP 440](https://www.python.org/dev/peps/pep-0440/) with
the additional understanding that releases before 1.0 (i.e. current
releases at time of writing) have not been tested in any way.

For the versions available, see the [tags on this
repository](https://github.com/giuthas/pd/tags).


## Authors

* **Pertti Palo** - *Initial work on PD and the Python framework used
  by the combined toolkit* - [giuthas](https://github.com/giuthas)
* **Scott Moisik** - *Initial work on OF* - [giuthas](https://github.com/giuthas)
* **Matthew Faytak** - ** - [giuthas](https://github.com/giuthas)

List of [contributors](https://github.com/your/project/contributors)
will be updated once there are more people working on this project.


## Copyright and License

The Pixel Difference tools (PD for short) and examples is a tool box
for analysing articulatory data.

Optical Flow tools Copyright (C) 2020 Scott Moisik
Pixel Difference tools Copyright (C) 2019-2020 Pertti Palo

OF Example data Copyright (C) 2020 Scott Moisik
PD Example data Copyright (C) 2013-2020 Pertti Palo

### Program license

[Program License](https://github.com/giuthas/pd/blob/master/license.md)

This program (see below for data) is free software: you can
redistribute it and/or modify it under the terms of the GNU General
Public License as published by the Free Software Foundation, either
version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see
[https://www.gnu.org/licenses/gpl-3.0.en.html](https://www.gnu.org/licenses/gpl-3.0.en.html).


### Data license

[Data License](https://github.com/giuthas/pd/blob/master/data_license_by-nc-sa.markdown)

The data in directories `of_data`, `test1_1`, `test1_2`, and `test2`
are licensed under the Creative Commons
Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA
4.0) License. See
[https://creativecommons.org/licenses/by-nc-sa/4.0/](https://creativecommons.org/licenses/by-nc-sa/4.0/)
for details.

### Citing the code

When making use of the Optic Flow code, please cite:
1. Esling, J. H., & Moisik, S. R. (2012). Laryngeal aperture in
relation to larynx height change: An analysis using simultaneous
laryngoscopy and laryngeal ultrasound. In D. Gibbon, D. Hirst, &
N. Campbell (Eds.), Rhythm, melody and harmony in speech: Studies in
honour of Wiktor Jassem: Vol. 14/15 (pp. 117–127). Polskie Towarzystwo
Fonetyczne.
2. Moisik, S. R., Lin, H., & Esling, J. H. (2014). A study of
laryngeal gestures in Mandarin citation tones using simultaneous
laryngoscopy and laryngeal ultrasound (SLLUS). Journal of the
International Phonetic Association, 44(01),
21–58. https://doi.org/10.1017/S0025100313000327
3. Poh, D. P. Z., & Moisik, S. R. (2019). An acoustic and
articulatory investigation of citation tones in Singaporean Mandarin
using laryngeal ultrasound. In S. Calhoun, P. Escudero, M. Tabain, &
P. Warren (Eds.), Proceedings of the 19th International Congress of
the Phonetic Sciences.

When using the Pixel Difference code, please cite:
1. Pertti Palo (2019). Measuring Pre-Speech Articulation. PhD
thesis. Queen Margaret University, Scotland, UK. Available here [PhD
thesis](https://eresearch.qmu.ac.uk/handle/20.500.12289/10163).


## Acknowledgments

* Inspiration for PD was drawn from previous projects using Euclidean
  distance to measure change in articulatory speech data. For
  references, see Pertti Palo's [PhD
  thesis](https://eresearch.qmu.ac.uk/handle/20.500.12289/10163).

* The project uses a nifty python tool called
  [licenseheaders](https://github.com/johann-petrak/licenseheaders) by
  Johann Petrak and contributors to add and update license headers for
  python files.
