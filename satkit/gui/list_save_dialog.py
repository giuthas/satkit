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
"""Dialog for asking which items should be saved and where."""
import os
from pathlib import Path

from PyQt5 import QtCore
from PyQt5.QtGui import QIcon, QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox, QFileDialog, QHBoxLayout, QLabel,
    QLineEdit,
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
            option_label: str | None = None,
    ):
        super().__init__(parent)

        self.chosen_item_names = []
        self.name = name
        if save_path is None:
            save_path = Path.cwd()
        elif isinstance(save_path, str):
            save_path = Path(save_path)
        self.save_path = save_path
        self.option = None

        # self.icon = icon

        # The checklist
        self.list_view = QListView()
        self.list_view.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff)
        self.model = QStandardItemModel()
        for item_name in item_names:
            item = QStandardItem(item_name)
            item.setCheckable(True)
            check = QtCore.Qt.Checked if checked else QtCore.Qt.Unchecked
            item.setCheckState(check)
            self.model.appendRow(item)
        self.list_view.setModel(self.model)
        # TODO: this doesn't quite work, but rather sets the width too large
        self.list_view.setMinimumWidth(
            self.list_view.contentsRect().width())

        # Buttons for checking and unchecking list items
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
        option_box = None
        if option_label is not None:
            option_box = QHBoxLayout()
            self.option_checkbox = QCheckBox(option_label)
            option_box.addWidget(self.option_checkbox)
            self.option = False
        path_and_name_box = QHBoxLayout()
        self.path_label = QLabel(self)
        self.path_label.setText("Path:")
        if self.save_path.is_dir():
            path_string = os.path.join(self.save_path, "")
        else:
            path_string = str(self.save_path)
        self.path_field = QLineEdit(path_string, parent=self)
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
        if option_box is not None:
            vbox.addLayout(option_box)
        vbox.addLayout(path_and_name_box)
        vbox.addWidget(self.ok_cancel_buttons)
        
        self.setWindowTitle(self.name)
        if icon:
            self.setWindowIcon(icon)

        self.adjustSize()

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
        if self.option is not None:
            self.option = self.option_checkbox.isChecked()
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
            option_label: str | None = None,
    ) -> tuple[list[str] | None, Path | None, bool | None]:
        dialog = ListSaveDialog(
            name=name,
            item_names=item_names,
            save_path=save_path,
            checked=checked,
            icon=icon,
            parent=parent,
            option_label=option_label,
        )
        if dialog.exec_() == QDialog.Rejected:
            return None, None, None
        return dialog.chosen_item_names, dialog.save_path, dialog.option
