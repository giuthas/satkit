
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

* **of_cli.py** and **pd_cli.py** These are the processing
  scripts. Run `python of_cli.py -h` and `python pd_cli.py -h` to see
  what they can do.
* **satkit/** This is the satkit (Speech Articulation ToolKIT)
  module. Refer to the documentation (not yet written) for a
  description of contents.


## Data

* **larynx_data/** This is the simple sample directory of larynx data.
* **tongue_data_1_1/** This is the simple sample directory of tongue data.
* **tongue_data_1_2/** This is the test directory with missing files.
* **tongue_data_2/**   This is the test directory with subdirectories.


## Config

* **satkit_logging_configuration.json**
	* Contains configuration of the runtime logging - filenames and so
      on.
	* If you need to disable or modify parts of the logging behaviour
      when using the toolkit as a library in another program this is
      the place to do so.
	* For runtime modifications use commandline arguments or options
      of the GUI.
* **exclusion_list.csv** List of files/recordings to exclude from
  processing. Only first field of each line is read by the
  scripts. The rest are comments for humans.
* **gpl-v3_and_CC-BY-NC-SA.tmpl** Template for adding license headers to
  code files.
* **licenseheaders_command** Command for running licenseheaders.py to
  get the headers in place for the code files.


## Automatically generated files not part of the distribution

* **spaghetti_plot.pdf** Output graphics of the basic PD test runs.
* **satkit.log** Log file of data runs.

