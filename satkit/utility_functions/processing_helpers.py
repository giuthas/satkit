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

import itertools
import re


def camel_to_snake(name: str) -> str:
    """
    Transform name from CamelCase to snake_case.

    Parameters
    ----------
    name : str
        Name to be converted to snake_case.

    Returns
    -------
    str
        The transformed name.
    """
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def product_dict(**kwargs):
    """
    Produce a list of dicts of the Cartesian product of lists in a dict.

    ```python
    options = {"number": [1,2,3], "color": ["orange","blue"] }
    print(list(product_dict(**options)))

    [ {"number": 1, "color": "orange"},
    {"number": 1, "color": "blue"},
    {"number": 2, "color": "orange"},
    {"number": 2, "color": "blue"},
    {"number": 3, "color": "orange"},
    {"number": 3, "color": "blue"}
    ]
    ```

    Yields
    ------
    list of dicts
        See example above.
    """
    keys = kwargs.keys()
    for instance in itertools.product(*kwargs.values()):
        yield dict(zip(keys, instance))
