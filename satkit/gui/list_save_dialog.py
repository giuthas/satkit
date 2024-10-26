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
"""Dialog for asking which items should be saved and where."""

from pathlib import Path

from icecream import ic
from PyQt5 import QtCore
from PyQt5.QtGui import QIcon, QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (
    QDialog, QDialogButtonBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit,
    QListView,
    QPushButton, QVBoxLayout, QWidget
)


class ListSaveDialog(QDialog):

    def __init__(
            self,
            name: str,
            item_names: list[str] | None = None,
            save_path: str | Path | None = None,
            checked: bool = True,
            icon: QIcon | None = None,
            parent: QWidget | None = None,
    ):
        super().__init__(parent)

        self.chosen_item_names = []
        self.name = name
        if save_path is None:
            save_path = Path.cwd()
        elif isinstance(save_path, str):
            save_path = Path(save_path)
        self.save_path = save_path

        # self.icon = icon

        # The checklist
        self.list_view = QListView()
        self.model = QStandardItemModel()
        for item_name in item_names:
            item = QStandardItem(item_name)
            item.setCheckable(True)
            check = QtCore.Qt.Checked if checked else QtCore.Qt.Unchecked
            item.setCheckState(check)
            self.model.appendRow(item)
        self.list_view.setModel(self.model)

        # Buttons for checking and unchecking 
        select_box = QHBoxLayout()
        select_box.addStretch(1)
        self.reverse_selection_button = QPushButton('Reverse selection')
        self.select_button = QPushButton('Select All')
        self.unselect_button = QPushButton('Unselect All')
        self.reverse_selection_button.clicked.connect(self._reverse_selection)
        self.select_button.clicked.connect(self._select)
        self.unselect_button.clicked.connect(self._unselect)
        select_box.addWidget(self.reverse_selection_button)
        select_box.addWidget(self.select_button)
        select_box.addWidget(self.unselect_button)

        # Elements for choosing names to use and location to save at.
        path_and_name_box = QHBoxLayout()
        # path_and_name_box.addStretch(1)
        self.path_label = QLabel(self)
        self.path_label.setText("Path:")
        self.path_field = QLineEdit(str(self.save_path), parent=self)
        self.path_label.setBuddy(self.path_field)
        self.browse_button = QPushButton('Browse...')
        self.browse_button.clicked.connect(self._browse)
        path_and_name_box.addWidget(self.path_label)
        path_and_name_box.addWidget(self.path_field)
        path_and_name_box.addWidget(self.browse_button)


        # The cancel, ok buttons
        dialog_buttons = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.ok_cancel_buttons = QDialogButtonBox(dialog_buttons)
        self.ok_cancel_buttons.accepted.connect(self.accept)
        self.ok_cancel_buttons.button(QDialogButtonBox.Ok).clicked.connect(
            self._on_accepted)
        self.ok_cancel_buttons.rejected.connect(self.reject)

        # Assemble the window contents
        vbox = QVBoxLayout(self)
        vbox.addWidget(self.list_view)
        vbox.addStretch(1)
        vbox.addLayout(select_box)
        vbox.addLayout(path_and_name_box)
        vbox.addWidget(self.ok_cancel_buttons)
        
        self.setWindowTitle(self.name)
        if icon:
            self.setWindowIcon(icon)

    def _browse(self):
        directory = QFileDialog.getExistingDirectory(
            parent=self,
            caption="Select Directory to Export to",
            directory=self.path_field.text(),
            options=QFileDialog.DontResolveSymlinks
        )
        if directory:
            self.path_field.setText(directory)

    def _on_accepted(self):
        self.chosen_item_names = [
            self.model.item(i).text() for i in range(self.model.rowCount())
            if self.model.item(i).checkState() == QtCore.Qt.Checked
        ]
        self.save_path = Path(self.path_field.text())
        self.accept()

    def _reverse_selection(self):
        for i in range(self.model.rowCount()):
            item = self.model.item(i)
            if item.checkState() == QtCore.Qt.Unchecked:
                item.setCheckState(QtCore.Qt.Checked)
            elif item.checkState() == QtCore.Qt.Checked:
                item.setCheckState(QtCore.Qt.Unchecked)

    def _select(self):
        for i in range(self.model.rowCount()):
            item = self.model.item(i)
            item.setCheckState(QtCore.Qt.Checked)

    def _unselect(self):
        for i in range(self.model.rowCount()):
            item = self.model.item(i)
            item.setCheckState(QtCore.Qt.Unchecked)

    @staticmethod
    def get_selection(
            name: str,
            item_names: list[str] | None = None,
            save_path: str | Path | None = None,
            checked: bool = True,
            icon: QIcon | None = None,
            parent: QWidget | None = None,
    ) -> tuple[list[str] | None, Path | None]:
        dialog = ListSaveDialog(
            name=name,
            item_names=item_names,
            save_path=save_path,
            checked=checked,
            icon=icon,
            parent=parent)
        if dialog.exec_() == QDialog.Rejected:
            return None, None
        return dialog.chosen_item_names, dialog.save_path
