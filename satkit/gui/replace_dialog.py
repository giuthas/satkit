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
"""Dialog for asking if we should overwrite an existing file or files."""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QDialogButtonBox)
from PyQt5.QtCore import Qt

from satkit.ui_callbacks import OverwriteConfirmation


class ReplaceDialog(QDialog):
    def __init__(self, filename: str, parent=None):
        super(ReplaceDialog, self).__init__(parent)

        layout = QVBoxLayout(self)

        self.question = QLabel(self)
        self.question.setText(
            f"File {filename} exists. Do you want to overwrite it?")
        layout.addWidget(self.question)

        buttons = QDialogButtonBox(
            (QDialogButtonBox.Yes | QDialogButtonBox.YesToAll |
             QDialogButtonBox.No | QDialogButtonBox.NoToAll),
            Qt.Horizontal, self)
        layout.addWidget(buttons)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        button_yes = buttons.button(QDialogButtonBox.Yes)
        button_yes.clicked.connect(self._handle_yes)
        button_yes_all = buttons.button(QDialogButtonBox.YesToAll)
        button_yes_all.clicked.connect(self._handle_yes_all)
        button_no = buttons.button(QDialogButtonBox.No)
        button_no.clicked.connect(self._handle_no)
        button_no_all = buttons.button(QDialogButtonBox.NoToAll)
        button_no_all.clicked.connect(self._handle_no_all)

        self.pressed_button = None

    def _handle_yes(self):
        self.pressed_button = OverwriteConfirmation.YES

    def _handle_yes_all(self):
        self.pressed_button = OverwriteConfirmation.YES_TO_ALL

    def _handle_no(self):
        self.pressed_button = OverwriteConfirmation.NO

    def _handle_no_all(self):
        self.pressed_button = OverwriteConfirmation.NO_TO_ALL

    @staticmethod
    def confirm_overwrite(filename: str, parent=None) -> OverwriteConfirmation:
        dialog = ReplaceDialog(filename, parent)
        dialog.exec_()
        pressed_button = dialog.pressed_button
        return pressed_button
