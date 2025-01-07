#
# Copyright (c) 2019-2025
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
String formatter functions.
"""
from typing import Generator


def split_by(
        string: str,
        delimiters: str = "{}"
) -> Generator[tuple[str, bool], None, None]:
    """
    Split a string by delimiters.

    No nesting of delimiters is allowed.

    Parameters
    ----------
    string : str
        The string to split.
    delimiters : str
        The delimiter(s) to split the string by, by default "{}".

    Yields
    -------
    tuple[str, bool]
        The next chunk and a boolean indicating if the chunk is a directive
        string (surrounded by delimiters).
    """
    while len(string) > 0:
        directive = string[0] == delimiters[0]
        if directive:
            result, string = string[1:].split(sep=delimiters[-1], maxsplit=1)
        else:
            if delimiters[0] in string[1:]:
                result, string = string.split(sep=delimiters[0], maxsplit=1)
                string = "{" + string
            else:
                result = string
                string = ""
        yield result, directive


