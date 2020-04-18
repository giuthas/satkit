#
# Copyright (c) 2019-2020 Pertti Palo, Scott Moisik, and Matthew Faytak.
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

import argparse
import logging
import os
import os.path
import sys
import time
import datetime 

# local modules
import satkit.pd as pd
import satkit.pdplot as pdplot
import satkit.io.AAA as satkit_AAA
import satkit.io as satkit_io


def widen_help_formatter(formatter, total_width=140, syntax_width=35):
    """Return a wider HelpFormatter, if possible."""
    try:
        # https://stackoverflow.com/a/5464440
        # beware: "Only the name of this class is considered a public API."
        kwargs = {'width': total_width, 'max_help_position': syntax_width}
        formatter(None, **kwargs)
        return lambda prog: formatter(prog, **kwargs)
    except TypeError:
        warnings.warn("Widening argparse help formatter failed. Falling back.")
        return formatter


def parse_args(description):
    parser = argparse.ArgumentParser(description=description,
        formatter_class = widen_help_formatter(argparse.HelpFormatter,
                                               total_width=100,
                                               syntax_width=35))

    # mutually exclusive with reading previous results from a file
    helptext = (
        'Path containing the data to be read.'
        'Supported types are .pickle files, and directories containing files exported from AAA. '
        'Loading from .m, .json, and .csv are in the works.'
    )
    parser.add_argument("load_path", help=helptext)
    
    parser.add_argument("-e", "--exclusion_list", dest="exclusion_filename",
                        help="Exclusion list of data files that should be ignored.",
                        metavar="file")
    
    helptext = (
        'Save metrics to file. '
        'Supported type is .pickle. '
        'Saving to .json, .csv., and .m may be possible in the future.'
    )
    parser.add_argument("-o", "--output", dest="output_filename",
                        help=helptext, metavar="file")

    helptext = (
        'Set verbosity of console output. Range is [0, 3], default is 1, '
        'larger values mean greater verbosity.'
    )
    parser.add_argument("-v", "--verbose",
                        type=int, dest="verbose",
                        default=1,
                        help=helptext,
                        metavar = "verbosity")

    args = parser.parse_args()
    return args


def set_up_logging(args):
    logger = logging.getLogger('satkit')
    logger.setLevel(logging.INFO)

    # also log to the console at a level determined by the --verbose flag
    console_handler = logging.StreamHandler() # sys.stderr

    # Set the level of logging messages that will be printed to
    # console/stderr.
    if not args.verbose:
        console_handler.setLevel('WARNING')
    elif args.verbose < 1:
        console_handler.setLevel('ERROR')
    elif args.verbose == 1:
        console_handler.setLevel('WARNING')
    elif args.verbose == 2:
        console_handler.setLevel('INFO')
    elif args.verbose >= 3:
        console_handler.setLevel('DEBUG')
    else:
        logging.critical("Unexplained negative argument " +
                         str(args.verbose) + " to verbose!")
    logger.addHandler(console_handler)

    logger.info('Run started at ' + str(datetime.datetime.now()))

    
def cli(description, processing_function):
    args = parse_args(description)
    
    set_up_logging(args)


    if not os.path.exists(args.load_path):
        logger.critical('File or directory doesn not exist: ' + args.load_path)
        logger.critical('Exiting.')
        sys.exit()
    elif os.path.isdir(args.load_path): 
        exclusion_list_name = None
        if args.exclusion_filename:
            exclusion_list_name = args.exclusion_filename

        # this is the actual list of tokens that gets processed 
        # token_list includes meta data contained outwith the ult file
        token_list = satkit_AAA.get_recording_list(args.load_path,
                                                   args.exclusion_filename)

        # run PD on each token
        data = [pd.pd(token) for token in token_list]

        data = [datum for datum in data if not datum is None]
    elif os.path.splitext(args.load_path)[1] == '.pickle':
        token_list, data = satkit_io.load_pickled_data(args.load_path)
    elif os.path.splitext(args.load_path)[1] == '.json':
        token_list, data = satkit_io.load_json_data(args.load_path)
    else:
        logger.error('Unsupported filetype: ' + args.load_path + '.')
        
    # do something sensible with the data
    logger.info("Drawing spaghetti plot.")
    pdplot.draw_spaghetti(token_list, data)

    if args.output_filename:
        if os.path.splitext(args.output_filename)[1] == '.pickle':
            pd.save2pickle((token_list, data), args.output_filename)
            logger.info("Wrote data to file " + args.output_filename + ".")
        elif os.path.splitext(args.output_filename)[1] == '.json':
            logger.error('Unsupported filetype: ' + args.output_filename + '.')
        else:
            logger.error('Unsupported filetype: ' + args.output_filename + '.')
            
    logger.info('Run ended at ' + str(datetime.datetime.now()))
    

# if (len(sys.argv) > 3 or len(sys.argv) < 1):
#     print("\npd.py")
#     print("\tusage: python pd.py uti_directory [exclusion_list]")
#     print("\n\tGenerates a pd spaghetti plot based on .ult files and meta data.")
#     sys.exit(0)


if (__name__ == '__main__'):
    t = time.time()
    cli()
    elapsed_time = time.time() - t
    logging.info('Elapsed time ' + str(elapsed_time))
