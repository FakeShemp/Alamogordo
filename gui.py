#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

from PyQt5 import QtWidgets, uic
from os import path
from read_disc import read_disc, disc_profiles
from sys import platform
import json
import operator
import settings
if platform is 'win32':
    import wmi

qtMainWindow = "mainwindow.ui"
qtSettingsWindow = "settings.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtMainWindow)
Ui_SettingsWindow, QtBaseClassSettings = uic.loadUiType(qtSettingsWindow)


class RedumpGui(QtWidgets.QMainWindow, Ui_MainWindow):
    no_drives = "No optical drives found"

    def __init__(self, app):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        profiles = sorted(disc_profiles())

        self.cb_driveLetter.addItems(self.available_drives())
        self.rb_custom.toggled.connect(lambda: self.custom_drive_speed_status(self.rb_custom))
        self.pb_browseDir.clicked.connect(self.browse_directory)
        self.cb_discType.addItems(profiles)
        self.pb_start.clicked.connect(lambda: read_disc(self, app))

        def open_settings_window():
            self.child_win = SettingsGui()
            self.child_win.show()

        self.action_settings.triggered.connect(open_settings_window)
        # TODO - Add cancel button
        # TODO - Add "new disc info" dialog - easily copyable data

    def available_drives(self):
        drives = []
        if platform is 'win32':
            c = wmi.WMI()
            for drive in c.Win32_CDROMDrive():
                drives.append(str(drive.Drive) + ' [' + str(drive.Caption) + ']')
            if not drives:
                return [self.no_drives]
        else:
            # This is just for testing.
            drives.append(str('D: [FAKE DRIVE FOR TESTING]'))

        return drives

    def custom_drive_speed_status(self, button):
        if button.isChecked():
            self.le_customDriveSpeed.setEnabled(True)
        else:
            self.le_customDriveSpeed.setEnabled(False)

    def browse_directory(self):
        directory = QtWidgets.QFileDialog.getExistingDirectory(self,
                                                               'Browse',
                                                               path.expanduser(self.le_dir.text()))
        if directory is not "":
            self.le_dir.setText(directory)

    def lock_input(self, state):
        state = not state
        self.le_fileName.setEnabled(state)
        self.le_dir.setEnabled(state)
        self.pb_browseDir.setEnabled(state)
        self.cb_discType.setEnabled(state)
        self.cb_driveLetter.setEnabled(state)
        self.rb_speed4.setEnabled(state)
        self.rb_speed8.setEnabled(state)
        self.rb_speed16.setEnabled(state)
        self.rb_speed48.setEnabled(state)
        self.rb_custom.setEnabled(state)
        if self.rb_custom.isChecked():
            self.le_customDriveSpeed.setEnabled(state)
        self.zipFiles.setEnabled(state)
        self.pt_console.setEnabled(state)
        self.pb_start.setEnabled(state)


class SettingsGui(Ui_SettingsWindow, QtBaseClassSettings):

    def __init__(self):
        QtBaseClassSettings.__init__(self)
        self.setupUi(self)

        if path.isfile(settings.settings_file):
            js = open(settings.settings_file).read()
            data = json.loads(js)
            if settings.dic_path in data:
                self.le_dicLocation.setText(data[settings.dic_path])
            if settings.psxt001z_path in data:
                self.le_psxt001zLocation.setText(data[settings.psxt001z_path])
            if settings.edccchk_path in data:
                self.le_edccchkLocation.setText(data[settings.edccchk_path])
            if settings.c2reads in data:
                self.le_c2.setText(str(data[settings.c2reads]))
            if settings.beep in data:
                if data[settings.beep] is True:
                    self.cb_beep.setChecked(True)

        self.pb_dicBrowse.clicked.connect(lambda: self.browse_file(self.le_dicLocation, 'DiscImageCreator.exe'))
        self.pb_psxt001zBrowse.clicked.connect(lambda: self.browse_file(self.le_psxt001zLocation, 'psxt001z.exe'))
        self.pb_edccchkBrowse.clicked.connect(lambda: self.browse_file(self.le_edccchkLocation, 'edccchk.exe'))
        self.buttonBox.accepted.connect(self.accept)

    def browse_file(self, lineedit, browse_filter):
        file_path, file = QtWidgets.QFileDialog.getOpenFileName(self,
                                                                caption='Browse',
                                                                directory=path.expanduser(lineedit.text()),
                                                                filter=browse_filter)

        if file_path is not "":
            lineedit.setText(file_path)

    def accept(self):
        data = {}
        if self.le_dicLocation.text() != "":
            data[settings.dic_path] = self.le_dicLocation.text()
        if self.le_psxt001zLocation.text() != "":
            data[settings.psxt001z_path] = self.le_psxt001zLocation.text()
        if self.le_edccchkLocation.text() != "":
            data[settings.edccchk_path] = self.le_edccchkLocation.text()
        if self.le_c2.text() != "":
            if self.le_c2.text().isdigit():
                data[settings.c2reads] = int(self.le_c2.text())
        if self.cb_beep.isChecked():
            data[settings.beep] = True

        with open(settings.settings_file, 'w') as outfile:
            json.dump(data, outfile)

        self.close()

