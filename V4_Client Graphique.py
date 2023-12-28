import threading
import socket
import json
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QListWidgetItem
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtGui import QTextCharFormat, QColor

# 替换为您的UI类
from client_output import Ui_Form
from chatroom_output import Ui_MainWindow

# 全局变量
IP = ''
PORT = ''
user = ''
listbox1 = ''  # 用于显示在线用户的列表框
ii = 0  # 用于判断是开还是关闭列表框
users = []  # 在线用户列表

class login_window(QtWidgets.QMainWindow, Ui_Form):
    def __init__(self):
        super(login_window, self).__init__()
        self.setupUi(self)
        self.init()

    def init(self):
        self.pushButton.clicked.connect(self.login_button)
        self.lineEdit_2.setText("127.0.0.1:50007")

    def login_button(self):
        global IP, PORT, user, Ui_Main
        try:
            IP, PORT = self.lineEdit_2.text().split(':')
            PORT = int(PORT)
        except ValueError:
            QMessageBox.warning(self, '警告', '请输入正确的IP地址和端口号')
            return

        user = self.lineEdit_3.text()
        password = self.lineEdit_password.text()

        if not user or not password:
            QMessageBox.critical(self, '错误', '用户名和密码不能为空！')
            return

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((IP, PORT))
            credentials = f"{user}:{password}"
            s.send(credentials.encode())

            response = s.recv(1024).decode()
            if response == "登录成功":
                self.hide()
                Ui_Main = main_window(s)
                Ui_Main.setWindowTitle("User Name: " + user)
                Ui_Main.show()
            else:
                QMessageBox.critical(self, '登录失败', '用户名或密码错误')
                s.close()
        except Exception as e:
            QMessageBox.critical(self, '连接失败', f'无法连接到服务器：{e}')
            if 's' in locals():
                s.close()

class main_window(QtWidgets.QMainWindow, Ui_MainWindow):
    update_txt = pyqtSignal(list)

    def __init__(self, socket):
        super(main_window, self).__init__()
        self.s = socket
        self.setupUi(self)
        self.init()

    def init(self):
        self.pushButton.clicked.connect(self.send)
        self.listWidget.currentItemChanged.connect(self.private)
        self.update_txt.connect(self.update_text)
        self.plainTextEdit.setReadOnly(True)

        if user:
            self.s.send(user.encode())
        else:
            self.s.send('no'.encode())

        self.plainTextEdit.insertPlainText("Welcome to the chat room!")

        self.r = threading.Thread(target=self.recv)
        self.r.daemon = True
        self.r.start()

    def send(self):
        message = self.plainTextEdit_2.toPlainText()
        if message:
            full_message = f"{message}:;{user}:;------Group chat-------"
            self.s.send(full_message.encode())
            self.plainTextEdit_2.setPlainText('')

    def recv(self):
        global users
        while True:
            try:
                data = self.s.recv(1024).decode()
                if not data:
                    break

                if ":;" in data:
                    data_parts = data.split(':;')
                    self.update_txt.emit(data_parts)
                else:
                    users = json.loads(data)
                    self.listWidget.clear()
                    for user in users:
                        self.listWidget.addItem(user)
            except Exception as e:
                print(f"接收数据时发生错误：{e}")
                break

    @pyqtSlot(list)
    def update_text(self, text_list):
        message, sender, receiver = text_list
        color_format = QTextCharFormat()
        if receiver == '------Group chat-------':
            if sender == user:
                color_format.setForeground(QColor("blue"))
            else:
                color_format.setForeground(QColor("green"))
            self.plainTextEdit.setCurrentCharFormat(color_format)
            self.plainTextEdit.appendPlainText(f"{sender}: {message}")

    def private(self, item):
        self.chat = item.text()
        if self.chat == '------Group chat-------':
            self.setWindowTitle(user)
            return
        self.setWindowTitle(user + '  -->  ' + self.chat)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = login_window()
    window.show()
    sys.exit(app.exec_())
