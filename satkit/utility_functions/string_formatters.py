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
String formatter functions.
"""
from typing import Generator

from ..data_structures import Modality

def _split_by(
        string: str,
        delimiters: str = "{}"
) -> Generator[(str, bool), None, None]:
    while len(string) > 0:
        directive = string[0] == delimiters[0]
        if directive:
            result, string = string[1:].split(sep=delimiters[-1], maxsplit=1)
        else:
            result, string = string[1:].split(sep=delimiters[0], maxsplit=1)
        yield result, directive


def process_directive(
        directive: str,
        modality: Modality,
        index: int
) -> str:
    field_name, format_specifier = directive.split(sep=":", maxsplit=1)
    format_specifier = "{" + format_specifier + "}"
    if field_name == "sampling_rate":
        return format_specifier.format(modality.sampling_rate)
    else:
        return format_specifier.format(
            modality.modality_data.__dict__[field_name])


def format_modality_legend(
    modality: Modality,
    index: int,
    format_string: str,
    delimiters: str = "{}"
) -> str:
    result = ""
    for chunk, is_directive in _split_by(format_string, delimiters):
        if not is_directive:
            result += chunk
        else:
            result += process_directive(chunk, modality, index)

    return result
