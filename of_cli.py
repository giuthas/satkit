#
# Copyright (c) 2019-2021 Pertti Palo, Scott Moisik, and Matthew Faytak.
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

import logging
import sys
import time

import multiprocessing as mp

# local modules
from satkit.commandLineInterface import RawCLI
import satkit.ofreg as of


def main():
    # Run the command line interface.
    RawCLI("OF processing script", of.of)


if __name__ == '__main__':
    # The old default start method in multiprocessing on MacOS
    # (i.e. darwin) leads to crashes. Fixing it apparently leads to
    # different kinds of crashes. Better solution on the todo list.
    if sys.version_info < (3, 8) and sys.platform == "darwin":
        logging.warning("Changing multiprocessing to use spawn.")
        mp.set_start_method('spawn')

    t = time.time()
    main()
    elapsed_time = time.time() - t
    logging.info('Elapsed time ' + str(elapsed_time))
