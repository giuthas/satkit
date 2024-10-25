from PyQt5 import QtCore
from PyQt5.QtGui import QIcon, QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (
    QApplication, QDialog, QDialogButtonBox, QHBoxLayout, QListView,
    QPushButton, QVBoxLayout, QWidget
)


class ChecklistDialog(QDialog):

    def __init__(
            self,
            name: str,
            choices: list[str] | None = None,
            checked: bool = False,
            icon: QIcon | None = None,
            parent: QWidget | None = None,
    ):
        super().__init__(parent)

        self.choices = []
        self.name = name
        self.icon = icon
        self.model = QStandardItemModel()
        self.listView = QListView()

        for choice in choices:
            item = QStandardItem(choice)
            item.setCheckable(True)
            check = QtCore.Qt.Checked if checked else QtCore.Qt.Unchecked
            item.setCheckState(check)
            self.model.appendRow(item)

        self.listView.setModel(self.model)

        self.selectButton = QPushButton('Select All')
        self.unselectButton = QPushButton('Unselect All')

        dialog_buttons = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(dialog_buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.button(
            QDialogButtonBox.Ok).clicked.connect(self.onAccepted)
        self.buttonBox.rejected.connect(self.reject)

        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(self.selectButton)
        hbox.addWidget(self.unselectButton)

        vbox = QVBoxLayout(self)
        vbox.addWidget(self.listView)
        vbox.addStretch(1)
        vbox.addLayout(hbox)
        vbox.addWidget(self.buttonBox)
        
        self.setWindowTitle(self.name)
        if self.icon:
            self.setWindowIcon(self.icon)

        self.selectButton.clicked.connect(self.select)
        self.unselectButton.clicked.connect(self.unselect)

    def onAccepted(self):
        self.choices = [
            self.model.item(i).text() for i in range(self.model.rowCount())
            if self.model.item(i).checkState() == QtCore.Qt.Checked
        ]
        self.accept()

    def select(self):
        for i in range(self.model.rowCount()):
            item = self.model.item(i)
            item.setCheckState(QtCore.Qt.Checked)

    def unselect(self):
        for i in range(self.model.rowCount()):
            item = self.model.item(i)
            item.setCheckState(QtCore.Qt.Unchecked)

    @staticmethod
    def get_selection(
            name: str,
            choices: list[str] | None = None,
            checked: bool = False,
            icon: QIcon | None = None,
            parent: QWidget | None = None,
    ) -> list[str]:
        dialog = ChecklistDialog(name, choices, checked, icon, parent)
        dialog.exec_()
        if dialog.exec_() == QDialog.Rejected:
            return []
        return dialog.choices


# if __name__ == '__main__':
#
#     import sys
#
#     fruits = [
#         'Banana',
#         'Apple',
#         'Elderberry',
#         'Clementine',
#         'Fig',
#         'Guava',
#         'Mango',
#         'Honeydew Melon',
#         'Date',
#         'Watermelon',
#         'Tangerine',
#         'Ugli Fruit',
#         'Juniperberry',
#         'Kiwi',
#         'Lemon',
#         'Nectarine',
#         'Plum',
#         'Raspberry',
#         'Strawberry',
#         'Orange',
#     ]
#     app = QApplication(sys.argv)
#     form = ChecklistDialog('Fruit', fruits, checked=True)
#     if form.exec_() == QDialog.Accepted:
#         print(', '.join([str(s) for s in form.choices]))
