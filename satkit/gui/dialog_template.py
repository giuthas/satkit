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
"""This is not a functional dialog window, only a template."""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QDialogButtonBox, QApplication)
from PyQt5.QtCore import Qt


class DialogTemplate(QDialog):
    """
    Template for making dialog windows. Have a look at ReplaceDialog for a
    different way of handling button presses.

    This file can be run by itself for ease of testing out the dialog design.
    """

    def __init__(self, filename: str, parent=None):
        super(DialogTemplate, self).__init__(parent)

        layout = QVBoxLayout(self)

        # nice widget for editing the date
        self.question = QLabel(self)
        self.question.setText(
            f"File {filename} exists. Do you want to overwrite it?")
        layout.addWidget(self.question)

        # OK and Cancel buttons
        buttons = QDialogButtonBox(
            (QDialogButtonBox.Ok | QDialogButtonBox.YesToAll |
             QDialogButtonBox.Cancel | QDialogButtonBox.NoToAll),
            Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # get current date and time from the dialog
    def dateTime(self):
        return self.datetime.dateTime()

    # static method to create the dialog and return (date, time, accepted)
    @staticmethod
    def getDateTime(filename: str, parent=None):
        dialog = DialogTemplate(filename, parent)
        result = dialog.exec_()
        return (result == QDialog.Accepted, result)


app = QApplication([])
(ok, result) = DialogTemplate.getDateTime(filename='foobar.txt')
print("{} {}".format(ok, result))
