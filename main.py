import sys
import re
import json
import os
import subprocess
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLineEdit, QLabel, QTextEdit, QComboBox,
                             QMessageBox, QScrollArea, QAction, QDialog, QFileDialog, QFontComboBox, QFontDialog)
from PyQt5.QtCore import QProcess, Qt, QTimer, QByteArray
from PyQt5.QtGui import QTextCursor, QKeyEvent, QTextCharFormat, QColor
from PyQt5.QtGui import QFont

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About program and creator")
        self.setFixedSize(500, 400)
        
        layout = QVBoxLayout()
        
        
        title = QLabel("SSH Server Tool")
        title.setStyleSheet("""
            font-size: 24px;
            color: #ffcc00;
            font-weight: bold;
            padding: 10px;
            text-align: center;
        """)
        layout.addWidget(title)
        
       
        version = QLabel("Версия: 1.1.0 (Stable)")
        version.setStyleSheet("""
            font-size: 16px;
            color: #e6e6e6;
            text-align: center;
            padding-bottom: 20px;
        """)
        layout.addWidget(version)
        
        
        desc = QLabel("""
        <p>Профессиональный инструмент для управления SSH соединениями.<br>
        Поддержка множества серверов с безопасным хранением учетных данных.</p>
        
        <p><b>Системные требования:</b><br>
        • Windows 10/11 или Linux<br>
        • Python 3.8+<br>
        • SSH клиент (OpenSSH или PuTTY)</p>
        """)
        desc.setStyleSheet("font-size: 14px;color: #BFBCBB")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
       
        cert = QLabel("""
        <div style='
            border: 1px solid #ffcc00;
            padding: 10px;
            margin: 10px 0;
            background-color: #3a3a3a;
            font-family: Consolas;
            font-size: 12px;
            color: #CFC884;
        '>
        <b>Digital Certificate:</b><br>
        Issued to: Rasez Softworks<br>
        Issued by: Rasez Certification Authority<br>
        Valid from: 01/01/2025 to 31/12/2030<br>
        SHA-256 Fingerprint: 12:34:56:78:90:AB:CD:EF...
        </div>
        """)
        cert.setWordWrap(True)
        layout.addWidget(cert)
        
       
        copyright = QLabel("© 2025 Rasez Softworks. Все права защищены.")
        copyright.setStyleSheet("""
            font-size: 12px;
            color: #a0a0a0;
            text-align: center;
            padding-top: 20px;
        """)
        layout.addWidget(copyright)
        
        self.setLayout(layout)
        self.setStyleSheet("background-color: #2d2d2d;")


class ConsoleOutput(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
       
        self.setReadOnly(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setLineWrapMode(QTextEdit.NoWrap)
        self.document().setMaximumBlockCount(1000)
        self.setStyleSheet("font-family: 'Monospace'; font-size: 12pt;")
        self.default_format = QTextCharFormat()
        self.default_format.setForeground(QColor("#e6e6e6"))
        
        self.error_format = QTextCharFormat()
        self.error_format.setForeground(QColor("#ff4444"))
        
        self.success_format = QTextCharFormat()
        self.success_format.setForeground(QColor("#44ff44"))
        
        self.command_format = QTextCharFormat()
        self.command_format.setForeground(QColor("#ffcc00"))
        self.command_format.setFontWeight(75)
        
        self.buffer = QByteArray()
        self.partial_line = ""

    def append_text(self, text, fmt=None):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        if fmt:
            cursor.setCharFormat(fmt)
        else:
            cursor.setCharFormat(self.default_format)
            
        cursor.insertText(text)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def process_data(self, data):

        text = data.data().decode('utf-8', errors='replace')

        text = self.partial_line + text

        lines = text.split('\n')
        if text.endswith('\n'):
            self.partial_line = ""
        else:
            self.partial_line = lines.pop()  
    
    
        for line in lines:
            self.append_line(line + '\n')

    def append_line(self, line):
        clean_line = self.clean_ansi(line)
        
        if clean_line.startswith("ERROR") or "fail" in clean_line.lower():
            self.append_text(clean_line, self.error_format)
        elif clean_line.startswith("$ "):
            self.append_text(clean_line, self.command_format)
        elif "success" in clean_line.lower() or "connected" in clean_line.lower():
            self.append_text(clean_line, self.success_format)
        else:
            self.append_text(clean_line)

    @staticmethod
    def clean_ansi(text):
         return text


class SSHServerTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SSH Server Tool")
        self.setGeometry(100, 100, 1000, 800)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.init_menu()
        self.main_layout = QVBoxLayout()
        self.central_widget.setLayout(self.main_layout)
        
        self.init_ui()
        
        self.ssh_servers = []
        self.current_process = None
        self.connected = False
        self.current_server = None
        self.command_history = []
        self.history_index = -1
        self.pause_output = False
        self.output_buffer = ""
        
        self.load_servers()
        self.update_combo_box()
        self.connect_buttons()
        self.setup_styles()
        
        self.output_timer = QTimer()
        self.output_timer.timeout.connect(self.flush_buffer)
        self.output_timer.start(100)

    def init_ui(self):
        self.label = QLabel("SSH SERVER TOOL")
        self.label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.label)

        self.server_management_layout = QVBoxLayout()
        
        self.row1_layout = QHBoxLayout()
        self.pushButton = QPushButton("ADD SSH")
        self.row1_layout.addWidget(self.pushButton)
        self.lineEdit = QLineEdit()
        self.lineEdit.setPlaceholderText("Username@Ip")
        self.row1_layout.addWidget(self.lineEdit)
        self.server_management_layout.addLayout(self.row1_layout)

        self.row2_layout = QHBoxLayout()
        self.lineEdit_3 = QLineEdit()
        self.lineEdit_3.setPlaceholderText("SSH NAME")
        self.row2_layout.addWidget(self.lineEdit_3)
        self.lineEdit_2 = QLineEdit()
        self.lineEdit_2.setPlaceholderText("Password")
        self.lineEdit_2.setEchoMode(QLineEdit.Password)
        self.row2_layout.addWidget(self.lineEdit_2)
        self.server_management_layout.addLayout(self.row2_layout)

        self.row3_layout = QHBoxLayout()
        self.pushButton_2 = QPushButton("CONNECT")
        self.row3_layout.addWidget(self.pushButton_2)
        self.pushButton_3 = QPushButton("SERVER LIST")
        self.row3_layout.addWidget(self.pushButton_3)
        self.pushButton_4 = QPushButton("POWERSHELL")
        self.row3_layout.addWidget(self.pushButton_4)
        self.pushButton_5 = QPushButton("DELETE")
        self.row3_layout.addWidget(self.pushButton_5)
        self.comboBox = QComboBox()
        self.row3_layout.addWidget(self.comboBox)
        self.server_management_layout.addLayout(self.row3_layout)

        self.main_layout.addLayout(self.server_management_layout)
    
        self.console_tools_layout = QHBoxLayout()
        
        self.clear_btn = QPushButton("Clear Console")
        self.clear_btn.clicked.connect(self.clear_console)
        self.console_tools_layout.addWidget(self.clear_btn)
        
        self.pause_btn = QPushButton("Pause Output")
        self.pause_btn.setCheckable(True)
        self.pause_btn.toggled.connect(self.toggle_pause)
        self.console_tools_layout.addWidget(self.pause_btn)
        
        self.save_btn = QPushButton("Save Output")
        self.save_btn.clicked.connect(self.save_output)
        self.console_tools_layout.addWidget(self.save_btn)
        
        self.main_layout.addLayout(self.console_tools_layout)

        self.console_widget = QWidget()
        self.console_layout = QVBoxLayout()
        self.console_widget.setLayout(self.console_layout)
        
        self.textEdit = ConsoleOutput()
        
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Введите команду и нажмите Enter...")
        self.command_input.returnPressed.connect(self.send_command)
        
        self.console_layout.addWidget(self.textEdit)
        self.console_layout.addWidget(self.command_input)
        
        scroll = QScrollArea()
        scroll.setWidget(self.console_widget)
        scroll.setWidgetResizable(True)
        self.main_layout.addWidget(scroll)

    def init_menu(self):
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #3a3a3a;
                font: 14pt 'Segoe UI';
            }
            QMenuBar::item {
                background-color: #3a3a3a;
                padding: 5px 10px;
                color: white;
            }
            QMenuBar::item:selected {
                background-color: #ffcc00;
                color: black;
            }
            QMenu {
                background-color: #3a3a3a;
                color: #e6e6e6;
                font: 12pt 'Segoe UI';
                border: 1px solid #4d4d4d;
            }
            QMenu::item:selected {
                background-color: #ffcc00;
                color: black;
            }
        """)

        file_menu = menubar.addMenu("File")
        export_action = QAction("Export Servers", self)
        export_action.triggered.connect(self.export_servers)
        file_menu.addAction(export_action)
        
        import_action = QAction("Import Servers", self)
        import_action.triggered.connect(self.import_servers)
        file_menu.addAction(import_action)

        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def setup_styles(self):
        self.setStyleSheet("""
            background-color: #2d2d2d;
        """)
        
        self.label.setStyleSheet("""
            font: bold 32pt 'Segoe UI';
            background: none;
            color: #ffcc00;
            padding: 10px;
        """)
        
        button_style = """
            QPushButton {
                font: 14pt 'Segoe UI';
                background-color: #3a3a3a;
                color: #e6e6e6;
                font-weight: 600;
                border: 1px solid #4d4d4d;
                border-radius: 5px;
                padding: 8px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                border: 1px solid #5d5d5d;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
            QPushButton:checked {
                background-color: #ffcc00;
                color: black;
            }
        """
        
        for btn in [self.pushButton, self.pushButton_2, self.pushButton_3, 
                   self.pushButton_4, self.pushButton_5, self.clear_btn, 
                   self.pause_btn, self.save_btn]:
            btn.setStyleSheet(button_style)
        
        line_edit_style = """
            QLineEdit {
                border: 1.5px solid #ffcc00;
                font: 14pt 'Consolas';
                color: #e6e6e6;
                background-color: #3a3a3a;
                font-weight: 700;
                border-radius: 5px;
                padding: 8px;
                selection-background-color: #ffcc00;
                selection-color: #000000;
            }
        """
        
        for le in [self.lineEdit, self.lineEdit_2, self.lineEdit_3, self.command_input]:
            le.setStyleSheet(line_edit_style)
        
        self.comboBox.setStyleSheet("""
            QComboBox {
                font: 12pt 'Segoe UI';
                color: #e6e6e6;
                background-color: #3a3a3a;
                border: 1px solid #4d4d4d;
                border-radius: 5px;
                padding: 8px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #3a3a3a;
                color: #e6e6e6;
                selection-background-color: #ffcc00;
                selection-color: #000000;
            }
        """)

    def connect_buttons(self):
        self.pushButton.clicked.connect(self.add_ssh_server)
        self.pushButton_2.clicked.connect(self.connect_to_server)
        self.pushButton_3.clicked.connect(self.show_server_list)
        self.pushButton_4.clicked.connect(self.open_powershell)
        self.pushButton_5.clicked.connect(self.delete_server)

    def load_servers(self):
        try:
            if os.path.exists("ssh_servers.json"):
                with open("ssh_servers.json", "r") as f:
                    self.ssh_servers = json.load(f)
        except Exception as e:
            self.show_error(f"Ошибка загрузки серверов: {str(e)}")

    def save_servers(self):
        try:
            with open("ssh_servers.json", "w") as f:
                json.dump(self.ssh_servers, f, indent=4)
        except Exception as e:
            self.show_error(f"Ошибка сохранения серверов: {str(e)}")

    def export_servers(self):
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Servers", "", "JSON Files (*.json)")
            if file_path:
                with open(file_path, "w") as f:
                    json.dump(self.ssh_servers, f, indent=4)
                self.textEdit.append_text(f"Серверы успешно экспортированы в {file_path}", 
                                        self.textEdit.success_format)
        except Exception as e:
            self.show_error(f"Ошибка экспорта: {str(e)}")

    def import_servers(self):
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Import Servers", "", "JSON Files (*.json)")
            if file_path:
                with open(file_path, "r") as f:
                    imported_servers = json.load(f)
                
                new_servers = [s for s in imported_servers 
                             if not any(es['name'] == s['name'] for es in self.ssh_servers)]
                
                if len(new_servers) < len(imported_servers):
                    dup_count = len(imported_servers) - len(new_servers)
                    self.textEdit.append_text(f"Пропущено {dup_count} дубликатов", 
                                            self.textEdit.error_format)
                
                self.ssh_servers.extend(new_servers)
                self.save_servers()
                self.update_combo_box()
                self.textEdit.append_text(f"Успешно импортировано {len(new_servers)} серверов", 
                                        self.textEdit.success_format)
        except Exception as e:
            self.show_error(f"Ошибка импорта: {str(e)}")

    def update_combo_box(self):
        self.comboBox.clear()
        for server in self.ssh_servers:
            self.comboBox.addItem(server["name"])

    def add_ssh_server(self):
        name = self.lineEdit_3.text().strip()
        connection = self.lineEdit.text().strip()
        password = self.lineEdit_2.text().strip()

        if not name or not connection or not password:
            self.show_error("Все поля должны быть заполнены!")
            return

        if "@" not in connection:
            self.show_error("Формат подключения: username@ip")
            return

        if any(s["name"] == name for s in self.ssh_servers):
            self.show_error("Сервер с таким именем уже существует!")
            return

        self.ssh_servers.append({
            "name": name,
            "connection": connection,
            "password": password
        })

        self.save_servers()
        self.update_combo_box()
        self.textEdit.append_text(f"Сервер {name} успешно добавлен!", 
                                self.textEdit.success_format)

        self.lineEdit.clear()
        self.lineEdit_2.clear()
        self.lineEdit_3.clear()

    def connect_to_server(self):
        if self.connected and self.current_process:
            self.disconnect_from_server()
            return

        index = self.comboBox.currentIndex()
        if index == -1:
            self.show_error("Нет доступных серверов!")
            return

        server = self.ssh_servers[index]
        self.current_server = server
        self.textEdit.clear()
        self.textEdit.append_text(f"Подключаемся к {server['name']} ({server['connection']})...")

        username, ip = server['connection'].split('@')
        password = server['password']

        self.current_process = QProcess()
        self.current_process.setProcessChannelMode(QProcess.MergedChannels)
        self.current_process.readyReadStandardOutput.connect(self.handle_stdout)
        self.current_process.finished.connect(self.process_finished)
    
        if os.name == 'nt':
            command = f'plink -ssh {username}@{ip} -pw {password}'
            self.current_process.start('cmd.exe', ['/c', command])
        else:
            command = f"sshpass -p '{password}' ssh {username}@{ip}"
            self.current_process.start('bash', ['-c', command])

        self.connected = True
        self.pushButton_2.setText("DISCONNECT")
        QTimer.singleShot(1000, self.focus_command_input)

    def disconnect_from_server(self):
        if self.current_process:
            self.current_process.terminate()
            self.current_process = None
        self.connected = False
        self.current_server = None
        self.pushButton_2.setText("CONNECT")
        self.textEdit.append_text("\nОтключено от сервера", 
                               self.textEdit.success_format)

    def process_finished(self, exit_code, exit_status):
        self.disconnect_from_server()
        self.textEdit.append_text(f"\nСоединение прервано с кодом выхода: {exit_code}", 
                                self.textEdit.error_format if exit_code != 0 else self.textEdit.success_format)

    def focus_command_input(self):
        self.command_input.setFocus()

    def handle_stdout(self):
        if not self.current_process or self.pause_output:
            return
        
   
        data = self.current_process.readAllStandardOutput()
        if data:
            text = data.data().decode('utf-8', errors='replace')
            self.output_buffer += text
#4istka buferaaa
    def flush_buffer(self):
        if not self.pause_output and self.output_buffer != "":
            self.textEdit.process_data(QByteArray(self.output_buffer.encode()))
            self.output_buffer = ""

    def send_command(self):
        if not self.connected or not self.current_process:
            self.textEdit.append_text("Сначала подключитесь к серверу!", 
                                    self.textEdit.error_format)
            return

        command = self.command_input.text().strip()
        if not command:
            return

        self.command_history.append(command)
        self.history_index = len(self.command_history)

        self.textEdit.append_text(f"$ {command}\n", 
                                self.textEdit.command_format)

        if os.name == 'nt':
            command += "\r\n"
        else:
            command += "\n"

        self.current_process.write(command.encode())
        self.command_input.clear()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Up and self.command_history:
            if self.history_index > 0:
                self.history_index -= 1
                self.command_input.setText(self.command_history[self.history_index])
        elif event.key() == Qt.Key_Down and self.command_history:
            if self.history_index < len(self.command_history) - 1:
                self.history_index += 1
                self.command_input.setText(self.command_history[self.history_index])
            else:
                self.history_index = len(self.command_history)
                self.command_input.clear()
        else:
            super().keyPressEvent(event)

    def show_server_list(self):
        if not self.ssh_servers:
            self.textEdit.append_text("Нет сохраненных серверов.", 
                                    self.textEdit.error_format)
            return

        self.textEdit.clear()
        self.textEdit.append_text("Список сохраненных серверов:", 
                                self.textEdit.success_format)
        self.textEdit.append_text("=" * 50 + "\n", 
                                self.textEdit.default_format)

        for i, server in enumerate(self.ssh_servers, 1):
            self.textEdit.append_text(f"{i}. {server['name']} ({server['connection']})\n", 
                                    self.textEdit.default_format)
        #смерть
    def open_powershell(self):
        index = self.comboBox.currentIndex()
        if index == -1:
            self.show_error("Нет доступных серверов!")
            return

        server = self.ssh_servers[index]
        username, ip = server['connection'].split('@')
        password = server['password']

        try:
            if os.name == 'nt':
                command = f'plink -ssh {username}@{ip} -pw {password}'
                subprocess.Popen(['start', 'cmd', '/k', command], shell=True)
                self.textEdit.append_text(f"Открыт внешний терминал PuTTY для {server['name']}", 
                                        self.textEdit.success_format)
            else:
                command = f"sshpass -p '{password}' ssh {username}@{ip}"
                subprocess.Popen(['x-terminal-emulator', '-e', command])
                self.textEdit.append_text(f"Открыт внешний терминал для {server['name']}", 
                                        self.textEdit.success_format)
        except Exception as e:
            error_msg = f"Ошибка: {str(e)}\n"
            error_msg += "Установите PuTTY (Windows) или sshpass (Linux)" if os.name == 'nt' else "Установите sshpass"
            self.show_error(error_msg)

    def delete_server(self):
        index = self.comboBox.currentIndex()
        if index == -1:
            self.show_error("Нет доступных серверов!")
            return

        server = self.ssh_servers[index]
        reply = QMessageBox.question(
            self, 'Подтверждение',
            f"Удалить сервер {server['name']}?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            del self.ssh_servers[index]
            self.save_servers()
            self.update_combo_box()
            self.textEdit.append_text(f"Сервер {server['name']} удален", 
                                    self.textEdit.success_format)

    def clear_console(self):
        self.textEdit.clear()

    def toggle_pause(self, paused):
        self.pause_output = paused
        self.pause_btn.setText("Resume" if paused else "Pause")
        if not paused and self.output_buffer:
            self.flush_buffer()

    def save_output(self):
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Console Output", "", "Text Files (*.txt);;All Files (*)")
            if file_path:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.textEdit.toPlainText())
                self.textEdit.append_text(f"Вывод сохранен в {file_path}", 
                                        self.textEdit.success_format)
        except Exception as e:
            self.show_error(f"Ошибка сохранения: {str(e)}")

    def show_about_dialog(self):
        dialog = AboutDialog(self)
        dialog.exec_()

    def show_error(self, message):
        QMessageBox.critical(self, "Ошибка", message)

    def closeEvent(self, event):
        if self.current_process and self.current_process.state() == QProcess.Running:
            self.current_process.terminate()
            self.current_process.waitForFinished(1000)
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SSHServerTool()
    window.show()
    sys.exit(app.exec_())
