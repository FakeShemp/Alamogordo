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

from os import path, listdir, getcwd
from PyQt5.QtGui import QTextCursor
import subprocess
import zipfile
import json
import settings


def execute_dic(cmd, gui, app):
    gui.pt_console.clear()
    app.processEvents()
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    buf = bytearray()
    while True:
        c = p.stdout.read(1)
        if c == b"" and p.poll() is not None:
            break
        if c == b"\r":
            n = p.stdout.read(1)
            if n == b"\n":
                gui.pt_console.appendPlainText(str(buf.decode('UTF-8')))
                app.processEvents()
                buf = bytearray()
            else:
                cursor = gui.pt_console.textCursor()
                cursor.select(QTextCursor.LineUnderCursor)
                cursor.removeSelectedText()
                gui.pt_console.insertPlainText(str(buf.decode('UTF-8')))
                app.processEvents()
                buf = bytearray()
                buf += n
        else:
            buf += c

    return p.returncode


def execute_psxt001z():
    return None


def execute_edccchk():
    return None


def gather_image_info(dir, file):
    image_info = {}
    base_path = path.join(dir, file)[:-4]

    # Gather CUE
    if path.isfile(base_path + '.cue'):
        cue = open(base_path + '.cue', 'r').read()
        image_info['cue'] = cue

    # Gather ClrMamePro DAT
    if path.isfile(base_path + '.dat'):
        dat = open(base_path + '.dat', 'r').read()
        image_info['cmp_dat'] = dat

    # Gather Write Offset
    if path.isfile(base_path + '_disc.txt'):
        with open(base_path + '_disc.txt') as f:
            for line in f:
                if 'CD Offset(Byte)' in line:
                    image_info['write_offset'] = int(line.split('(Samples)', 1)[1])
                    break

    # Gather PVD
    if path.isfile(base_path + '_mainInfo.txt'):
        with open(base_path + '_mainInfo.txt') as f:
            pvd = ""
            for i, line in enumerate(f):
                if 51 < i < 58:
                    pvd += line
                elif i >= 58:
                    break
        image_info['pvd'] = pvd

    return image_info


def show_image_info(info, gui):
    gui.open_image_info_window(info)


def read_disc(gui, app):
    gui.statusBar.showMessage("")
    gui.lock_input(True)
    cmd = assemble_commandline(gui)

    # Run DiscImageCreator
    if cmd is not None:
        return_code = execute_dic(cmd, gui, app)
        if return_code != 0:
            gui.statusBar.showMessage("Reading image failed! Please read DIC output.")
            gui.lock_input(False)
            return return_code

    # Gather redump.org necessary info
    image_info = gather_image_info(directory(gui), file_name(gui))

    # Zip log files
    if gui.zipFiles.isChecked():
        zip_logs(path.dirname(cmd[3]))

    show_image_info(image_info, gui)

    gui.lock_input(False)


def assemble_commandline(gui):
    if path.isfile(settings.settings_file):
        js = open(settings.settings_file).read()
        data_settings = json.loads(js)

    # Add DiscImageCreator.exe path
    cmd = []
    if settings.dic_path in data_settings:
        cmd.append(data_settings[settings.dic_path])
    elif path.isfile(path.abspath(path.join(getcwd(), 'DiscImageCreator.exe'))) is True:
        cmd.append(path.abspath(path.join(getcwd(), 'DiscImageCreator.exe')))
    else:
        gui.statusBar.showMessage("DiscImageCreator.exe not found!")
        return None

    # Get profiles
    profiles = disc_profiles()
    current_profile = profiles[gui.cb_discType.currentText()]

    # Add disc type
    if 'disc_type' in current_profile:
        cmd.append(current_profile['disc_type'])

    # Add drive letter
    dl = drive_letter(gui)
    if dl is not None:
        cmd.append(str(dl))
    else:
        gui.statusBar.showMessage(gui.no_drives)
        return None

    # Add output file path
    fn = file_name(gui)
    dr = directory(gui)
    if fn is not None and dr is not None:
        cmd.append(path.normpath(path.abspath(path.join(dr, fn))))
    else:
        return None

    # Add drive read speed
    ds = drive_speed(gui)
    if ds is not None:
        cmd.append(ds)
    else:
        return None

    # Add extra switches
    if 'c2' in current_profile:
        if settings.c2reads in data_settings:
            cmd.append(current_profile['c2'] + ' ' + str(data_settings[settings.c2reads]))
        else:
            cmd.append(current_profile['c2'])

    if 'nl' in current_profile:
        cmd.append(current_profile['nl'])

    if settings.beep not in data_settings:
        cmd.append('/q')

    return cmd


def disc_profiles():
    if path.isfile(settings.profiles_file):
        js = open(settings.profiles_file).read()
        data_profiles = json.loads(js)
        return data_profiles
    return None


def file_name(gui):
    if gui.le_fileName.text() != "":
        # TODO - Check for illegal characters
        if not gui.le_fileName.text().endswith('.bin'):
            return gui.le_fileName.text() + '.bin'
        else:
            return gui.le_fileName.text()
    gui.statusBar.showMessage("Output file name is malformed. Aborting!")
    return None


def directory(gui):
    if gui.le_dir.text() != "":
        expanded_path = path.expanduser(gui.le_dir.text())
        if path.isdir(expanded_path):
            return expanded_path
    gui.statusBar.showMessage("Output directory is malformed. Aborting!")
    return None


def drive_letter(gui):
    if gui.cb_driveLetter.currentText() != gui.no_drives:
        # TODO - Split this by colon instead
        return gui.cb_driveLetter.currentText().lower()[0]
    return None


def drive_speed(gui):
    if gui.rb_speed4.isChecked():
        return '4'
    elif gui.rb_speed8.isChecked():
        return '8'
    elif gui.rb_speed16.isChecked():
        return '16'
    elif gui.rb_speed48.isChecked():
        return '48'
    elif gui.rb_custom.isChecked():
        if gui.le_customDriveSpeed.text() != "":
            if gui.le_customDriveSpeed.text().isdigit():
                return gui.le_customDriveSpeed.text()
    gui.statusBar.showMessage("Drive speed is not a number. Aborting!")
    return None


def zip_logs(working_dir):
    extensions = ['.c2', '.ccd', '.cue', '.dat', '.sub', '.txt']  # TODO - Add all types
    output = path.join(working_dir, 'logs.zip')
    all_files = listdir(working_dir)
    log_files = []

    for file in all_files:
        if file.endswith(tuple(extensions)):
            log_files.append(file)
    logs = zipfile.ZipFile(output, compression=zipfile.ZIP_DEFLATED, mode='w')
    if log_files:
        for file in log_files:
            logs.write(path.join(working_dir, file), arcname=file)
        logs.close()
    return output
