
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


from enum import Enum
from typing import Callable, Optional, Protocol, TypeVar

T = TypeVar('T')


class OverwriteConfirmation(Enum):
    """
    Codes for a user's response when asked if a file should be overwritten.
    """
    YES = 'yes'
    YES_TO_ALL = 'yes to all'
    NO = 'no'
    NO_TO_ALL = 'no to all'


class UiCallbacks:
    """
    Mechanisms for handling user interaction via callbacks in a 
    ui implementation agnostic way.

    It is the responsibility of all UIs to implement and register
    the callbacks defined here on initialisation. See `register_xyz`
    for details.
    """

    confirm_overwrite: Optional[Callable[[
        str, T], OverwriteConfirmation]] = None

    @staticmethod
    def register_overwrite_confirmation_callback(
            callback: Callable[[str, T], OverwriteConfirmation]) -> None:
        UiCallbacks.confirm_overwrite = callback

    @staticmethod
    def get_overwrite_confirmation(
            filename: str, parent=None) -> OverwriteConfirmation:
        """
        Confirm overwriting a file by asking the user.

        Parameters
        ----------
        filename : str
            File about to be overwritten.
        parent : _type_, optional
            For tying a dialog to the gui mainwindow, by default None

        Returns
        -------
        ReplaceResult
            The user's response.
        """
        return UiCallbacks.confirm_overwrite(filename, parent)
