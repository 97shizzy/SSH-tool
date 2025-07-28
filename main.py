import sys
import re
import json
import os
import subprocess
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLineEdit, QLabel, QTextEdit, QComboBox,
                             QMessageBox, QScrollArea)
from PyQt5.QtCore import QProcess, QTextStream, Qt, QTimer
from PyQt5.QtGui import QTextCursor, QKeyEvent


import re

ansi_escape = re.compile(r'''
    \x1B  
    (?:   
        [@-Z\\-_]
    |     
        \[
        [0-?]*  
        [ -/]*  
        [@-~]   
    )
''', re.VERBOSE)

def clean_ansi(text):
    return ansi_escape.sub('', text)

class SSHServerTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SSH Server Tool")
        self.setGeometry(0, 0, 900, 700)
        
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        
        self.main_layout = QVBoxLayout()
        self.central_widget.setLayout(self.main_layout)
        
        
        self.init_ui()
        
        
        self.ssh_servers = []
        self.current_process = None
        self.connected = False
        self.current_server = None
        self.command_history = []
        self.history_index = -1
        self.load_servers()
        self.update_combo_box()
        
        
        self.connect_buttons()
        
        
        self.setup_styles()

    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        self.label = QLabel("SSH SERVER TOOL")
        self.label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.label)

        self.row1_layout = QHBoxLayout()
        
        self.pushButton = QPushButton("ADD SSH")
        self.row1_layout.addWidget(self.pushButton)
        
        self.lineEdit = QLineEdit()
        self.lineEdit.setPlaceholderText("Username@Ip")
        self.row1_layout.addWidget(self.lineEdit)
        
        self.main_layout.addLayout(self.row1_layout)

        self.row2_layout = QHBoxLayout()
        
        self.lineEdit_3 = QLineEdit()
        self.lineEdit_3.setPlaceholderText("SSH NAME")
        self.row2_layout.addWidget(self.lineEdit_3)
        
        self.lineEdit_2 = QLineEdit()
        self.lineEdit_2.setPlaceholderText("Password")
        self.lineEdit_2.setEchoMode(QLineEdit.Password)
        self.row2_layout.addWidget(self.lineEdit_2)
        
        self.main_layout.addLayout(self.row2_layout)

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
        
        self.main_layout.addLayout(self.row3_layout)

     
        self.console_widget = QWidget()
        self.console_layout = QVBoxLayout()
        self.console_widget.setLayout(self.console_layout)
        
       
        self.textEdit = QTextEdit()
        self.textEdit.setReadOnly(True)
        
       
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Введите команду и нажмите Enter...")
        self.command_input.returnPressed.connect(self.send_command)
        
        self.console_layout.addWidget(self.textEdit)
        self.console_layout.addWidget(self.command_input)
        
     
        scroll = QScrollArea()
        scroll.setWidget(self.console_widget)
        scroll.setWidgetResizable(True)
        self.main_layout.addWidget(scroll)
    
    def setup_styles(self):
        """Настройка стилей элементов"""
        
        self.setStyleSheet("""
            background: qlineargradient(spread:pad, x1:0, y1:0, x2:2, y2:0, 
                          stop:0 rgba(0, 0, 0, 255), stop:1 rgba(237, 81, 210, 255));
        """)
        
       
        self.label.setStyleSheet("""
            font: "Lucida Sans Unicode";
            font-weight: 800;
            font-size: 45px;
            background: none;
            color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, 
                  stop:0 rgba(58, 255, 169, 255), stop:1 rgba(246, 146, 244, 255));
        """)
        
      
        button_style = """
            font: "Lucida Sans Unicode";
            font-weight: 700;
            font-size: 20px;
            background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, 
                  stop:0.433333 rgba(74, 0, 130, 255), stop:1 rgba(230, 65, 83, 255));
            border: 2px solid black;
            border-radius: 10px;
            min-height: 41px;
        """
        
        for btn in [self.pushButton, self.pushButton_2, self.pushButton_3, 
                   self.pushButton_4, self.pushButton_5]:
            btn.setStyleSheet(button_style)
        
       
        line_edit_style = """
            font: "Lucida Sans Unicode";
            font-weight: 700;
            font-size: 25px;
            color: rgba(255, 255, 255, 255);
            border: 2px solid black;
            border-radius: 10px;
            background-color: rgba(255, 61, 171, 100);
            min-height: 41px;
        """
        
        for le in [self.lineEdit, self.lineEdit_2, self.lineEdit_3]:
            le.setStyleSheet(line_edit_style)
        
      
        self.lineEdit.setStyleSheet("""
            font: "Lucida Sans Unicode";
            font-weight: 700;
            font-size: 30px;
            color: rgba(255, 255, 255, 255);
            border: 2px solid black;
            border-radius: 10px;
            background-color: rgba(255, 61, 171, 100);
            min-height: 46px;
        """)
        
       
        self.comboBox.setStyleSheet("""
            font: "Lucida Sans Unicode";
            font-weight: 700;
            font-size: 20px;
            color: rgba(255, 255, 255, 255);
            border: 2px solid black;
            border-radius: 10px;
            background-color: rgba(255, 61, 171, 100);
        """)
        
        
        self.textEdit.setStyleSheet("""
            border: 3px solid rgb(255, 125, 170);
            background-color: rgba(0, 0, 0, 200);
            font: 12pt "Consolas";
            color: white;
        """)
        
        
        self.command_input.setStyleSheet("""
            font: 12pt "Consolas";
            color: white;
            background-color: rgba(0, 0, 0, 200);
            border: 2px solid rgb(255, 125, 170);
            border-radius: 5px;
            padding: 5px;
        """)

    def connect_buttons(self):
        """Подключение сигналов кнопок"""
        self.pushButton.clicked.connect(self.add_ssh_server)
        self.pushButton_2.clicked.connect(self.connect_to_server)
        self.pushButton_3.clicked.connect(self.show_server_list)
        self.pushButton_4.clicked.connect(self.open_powershell)
        self.pushButton_5.clicked.connect(self.delete_server)

    def load_servers(self):
        """Загрузка списка серверов из JSON файла"""
        try:
            if os.path.exists("ssh_servers.json"):
                with open("ssh_servers.json", "r") as f:
                    self.ssh_servers = json.load(f)
        except Exception as e:
            self.show_error(f"Ошибка загрузки серверов: {str(e)}")

    def save_servers(self):
        """Сохранение списка серверов в JSON файл"""
        try:
            with open("ssh_servers.json", "w") as f:
                json.dump(self.ssh_servers, f, indent=4)
        except Exception as e:
            self.show_error(f"Ошибка сохранения серверов: {str(e)}")

    def update_combo_box(self):
        """Обновление комбобокса с серверами"""
        self.comboBox.clear()
        for server in self.ssh_servers:
            self.comboBox.addItem(server["name"])

    def add_ssh_server(self):
        """Добавление нового SSH сервера"""
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
        self.textEdit.append(f"Сервер {name} успешно добавлен!")

      
        self.lineEdit.clear()
        self.lineEdit_2.clear()
        self.lineEdit_3.clear()

    def connect_to_server(self):
        if self.connected and self.current_process:
            self.current_process.terminate()
            self.current_process = None
            self.connected = False
            self.current_server = None
            self.pushButton_2.setText("CONNECT")
            self.textEdit.append("\nОтключено от сервера")
            return

        index = self.comboBox.currentIndex()
        if index == -1:
            self.show_error("Нет доступных серверов!")
            return

        server = self.ssh_servers[index]
        self.current_server = server
        self.textEdit.clear()
        self.textEdit.append(f"Подключаемся к {server['name']} ({server['connection']})...")

        username, ip = server['connection'].split('@')
        password = server['password']

        self.current_process = QProcess()
        self.current_process.setProcessChannelMode(QProcess.MergedChannels)
        self.current_process.readyReadStandardOutput.connect(self.handle_stdout)
    
        if os.name == 'nt':
            command = f'plink -ssh {username}@{ip} -pw {password}'
            self.current_process.start('cmd.exe', ['/c', command])
        else:
            command = f"sshpass -p '{password}' ssh {username}@{ip}"
            self.current_process.start('bash', ['-c', command])

        self.connected = True
        self.pushButton_2.setText("DISCONNECT")
        QTimer.singleShot(1000, self.focus_command_input)

    def focus_command_input(self):
        """Установка фокуса на поле ввода команд"""
        self.command_input.setFocus()

    def handle_stdout(self):
        if not self.current_process:
            return
        data = self.current_process.readAllStandardOutput()
        if data:
            try:
                text = data.data().decode('utf-8')
            except UnicodeDecodeError:
                try:
                    text = data.data().decode('cp866')
                except:
                    text = str(data.data())
            text = clean_ansi(text)
            cursor = self.textEdit.textCursor()
            cursor.movePosition(QTextCursor.End)
            cursor.insertText(text)
            self.textEdit.setTextCursor(cursor)
            self.textEdit.ensureCursorVisible()
    
    

    def send_command(self):
        if not self.connected or not self.current_process:
            self.textEdit.append("Сначала подключитесь к серверу!")
            return

        command = self.command_input.text().strip()
        if not command:
            return

        self.command_history.append(command)
        self.history_index = len(self.command_history)


        self.textEdit.append(f"$ {command}")

        if os.name == 'nt':
            command += "\r\n"
        else:
            command += "\n"

        self.current_process.write(command.encode())
        self.command_input.clear()

    def keyPressEvent(self, event: QKeyEvent):
        """Обработка нажатий клавиш для истории команд"""
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
        """Отображение списка серверов"""
        if not self.ssh_servers:
            self.textEdit.append("Нет сохраненных серверов.")
            return

        self.textEdit.clear()
        self.textEdit.append("Список сохраненных серверов:")
        self.textEdit.append("=" * 50)

        for i, server in enumerate(self.ssh_servers, 1):
            self.textEdit.append(f"{i}. {server['name']} ({server['connection']})")

    def open_powershell(self):
        """Открытие внешнего терминала"""
        index = self.comboBox.currentIndex()
        if index == -1:
            self.show_error("Нет доступных серверов!")
            return

        server = self.ssh_servers[index]
        username, ip = server['connection'].split('@')
        password = server['password']

        if os.name == 'nt':
            try:
                command = f'plink -ssh {username}@{ip} -pw {password}'
                subprocess.Popen(['start', 'cmd', '/k', command], shell=True)
            except Exception as e:
                self.show_error(f"Ошибка: {e}\nУстановите PuTTY")
        else:
            try:
                command = f"sshpass -p '{password}' ssh {username}@{ip}"
                subprocess.Popen(['x-terminal-emulator', '-e', command])
            except Exception as e:
                self.show_error(f"Ошибка: {e}\nУстановите sshpass")

    def delete_server(self):
        """Удаление выбранного сервера"""
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
            self.textEdit.append(f"Сервер {server['name']} удален")

    def show_error(self, message):
        """Отображение сообщения об ошибке"""
        QMessageBox.critical(self, "Ошибка", message)

    def closeEvent(self, event):
        """Обработка закрытия окна"""
        if self.current_process and self.current_process.state() == QProcess.Running:
            self.current_process.terminate()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SSHServerTool()
    window.show()
    sys.exit(app.exec_())