
# Package manifest

Following is a short explanation of what is what in the package.


## Explanations and licenses

* **README.md** is what you should read first. Licenses, references, all
  that.
* **manifest.txt** is this file.
* **data_license_by-nc-sa.markdown** License file for the data.
* **license.md** Software license.
* **citations.bib** Toolkit references in BibTeX format. 


## Code

* **pd_test.py** This is the test script. Run `python pd_test.py -h` to
  see what it can do.
* **pd/** This is the pd (pixel difference) module. Refer to the
  documentation (not yet written) for a description of contents.


## Data

* **test1_1/** This is the simple test directory.
* **test1_2/** This is the test directory with missing files.
* **test2/**   This is the test directory with subdirectories.


## Config

* **pd_logging_configuration.json**
	* Contains configuration of the runtime logging - filenames and so
      on.
	* If you need to disable or modify parts of the logging behaviour
      when using the toolkit as a library in another program this is
      the place to do so.
	* For runtime modifications use commandline arguments or options
      of the GUI.
* **exclusion_list.csv** List of files/recordings to exclude from
  processing. Only first field of each line is read by pd. The rest
  are comments for humans.
* **gpl-v3_and_CC-BY-NC-SA.tmpl** Template for adding license headers to
  code files.


## Automatically generated files not part of the distribution

* **spaghetti_plot.pdf** Output graphics of the basic PD test runs.
* **pd.log** Log file of data runs.

