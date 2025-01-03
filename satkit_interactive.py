#!/usr/bin/env python3
#
# Copyright (c) 2019-2024
# Pertti Palo, Scott Moisik, Matthew Faytak, and Motoki Saito.
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
"""
Experimental interactive interpreter mode
"""
import code

from satkit import (
    add_derived_data, initialise_satkit
)
from satkit.utility_functions import log_elapsed_time


def main():
    """Main to initialise SATKIT and start the interactive interpreter."""

    cli, configuration, logger, session = initialise_satkit()
    log_elapsed_time(logger)

    add_derived_data(session=session, config=configuration)
    log_elapsed_time(logger)

    # TODO 1.0: Probably better doing this with IPython than the history-less
    # standard library version
    # import IPython
    # IPython.embed()
    code.interact(
        banner="SATKIT Interactive Console",
        local=locals(),
        exitmsg="Exiting SATKIT Interactive Console",
    )


if __name__ == '__main__':
    main()
