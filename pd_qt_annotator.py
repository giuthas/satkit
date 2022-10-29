#
# Copyright (c) 2019-2022 Pertti Palo, Scott Moisik, Matthew Faytak, and Motoki Saito.
#
# This file is part of Speech Articulation ToolKIT
# (see https://github.com/giuthas/satkit/).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# The example data packaged with this program is licensed under the
# Creative Commons Attribution-NonCommercial-ShareAlike 4.0
# International (CC BY-NC-SA 4.0) License. You should have received a
# copy of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0
# International (CC BY-NC-SA 4.0) License along with the data. If not,
# see <https://creativecommons.org/licenses/by-nc-sa/4.0/> for details.
#
# When using the toolkit for scientific publications, please cite the
# articles listed in README.markdown. They can also be found in
# citations.bib in BibTeX format.
#

# built-in modules
import logging
import sys
import time

# For running a Qt GUI
from PyQt5 import QtWidgets

from satkit import pd
# local modules
from satkit.commandLineInterface import RawCLI
from satkit.modalities import RawUltrasound
from satkit.qt_annotator import PdQtAnnotator


def main():
    """Simple main to run the CLI back end and start the QT front end."""
    start_time = time.time()

    # Run the command line interface.
    #function_dict = {'pd':pd.pd, 'annd':annd.annd}
    function_dict = {'PD': (pd.add_pd, [RawUltrasound])}
    cli = RawCLI("PD annotator", function_dict, plot=True)

    elapsed_time = time.time() - start_time
    log_text = 'Elapsed time ' + str(elapsed_time)
    logging.info(log_text)

    # Get the GUI running.
    app = QtWidgets.QApplication(sys.argv)
    # Apparently the assigment to an unused variable is needed to avoid a segfault.
    annotator = PdQtAnnotator(cli.recordings, cli.args)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
