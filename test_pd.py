#
# Copyright (c) 2019-2020 Pertti Palo.
#
# This file is part of Pixel Difference toolkit 
# (see https://github.com/giuthas/pd/).
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

import argparse
import logging
import sys
import time
import datetime 

# local modules
import pd as pd

def main():
    parser = argparse.ArgumentParser(description="PD toolkit test script")
    parser.add_argument("directory", help="directory containing the data")
    parser.add_argument("-l", "--log_file", dest="log_filename",
                        help="write log to FILE", metavar="FILE")
    parser.add_argument("-f", "--file", dest="filename",
                        help="write report to FILE", metavar="FILE")
    parser.add_argument("-q", "--quiet",
                        action="store_false", dest="verbose",
                        default=True,
                        help="don't print status messages to stdout")

    args = parser.parse_args()

    logging.basicConfig(filename = (directory + '.log'), 
                        filemode = 'w', 
                        level = logging.INFO)
    logging.info('Run started at ' + str(datetime.datetime.now()))

    directory = args[0]
        
    exclusion_list_name = None
    if len(args) > 1:
        exclusion_list_name = args[1]

    # this is the actual list of tokens that gets processed 
    # including meta data contained outwith the ult file
    token_list = pd.get_token_list_from_dir(directory, exclusion_list_name)

    # run PD on each token
    data = [pd.pd(token) for token in token_list]

    data = [datum for datum in data if not datum is None]

    # do something sensible with the data
    pd.draw_spaghetti(token_list, data)
    logging.info('Run ended at ' + str(datetime.datetime.now()) + '\n')
    

# if (len(sys.argv) > 3 or len(sys.argv) < 1):
#     print("\npd.py")
#     print("\tusage: python pd.py uti_directory [exclusion_list]")
#     print("\n\tGenerates a pd spaghetti plot based on .ult files and meta data.")
#     sys.exit(0)


if (__name__ == '__main__'):
    t = time.time()
    main()
    elapsed_time = time.time() - t
    logging.info('Elapsed time ' + str(elapsed_time))
