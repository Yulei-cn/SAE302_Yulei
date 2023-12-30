import threading
import socket
import json
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QListWidgetItem
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtGui import QTextCharFormat, QColor

# Remplacer par votre classe UI
from client_output import Ui_Form
from chatroom_output import Ui_MainWindow

# Variables globales
IP = ''
PORT = ''
user = ''
listbox1 = ''  # Boîte de liste pour afficher les utilisateurs en ligne
ii = 0  # Utilisé pour déterminer si la boîte de liste est ouverte ou fermée
users = []  # Liste des utilisateurs en ligne

class login_window(QtWidgets.QMainWindow, Ui_Form):
    def __init__(self):
        super(login_window, self).__init__()
        self.setupUi(self)
        self.init()

    def init(self):
        self.pushButton.clicked.connect(self.login_button)
        self.lineEdit_2.setText("127.0.0.1:8008")

    def login_button(self):
        global IP, PORT, user, Ui_Main
        try:
            IP, PORT = self.lineEdit_2.text().split(':')
            PORT = int(PORT)
        except ValueError:
            QMessageBox.warning(self, 'Attention', 'Veuillez entrer une adresse IP et un numéro de port valides')
            return

        user = self.lineEdit_3.text()
        password = self.lineEdit_password.text()

        if not user or not password:
            QMessageBox.critical(self, 'Erreur', 'Le nom d’utilisateur et le mot de passe ne peuvent pas être vides !')
            return

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((IP, PORT))
            credentials = f"{user}:{password}"
            s.send(credentials.encode())

            response = s.recv(1024).decode()
            if response == "Connexion réussie":
                self.hide()
                Ui_Main = main_window(s)
                Ui_Main.setWindowTitle("Nom d'utilisateur : " + user)
                Ui_Main.show()
            else:
                QMessageBox.critical(self, 'Échec de la connexion', 'Nom d’utilisateur ou mot de passe incorrect')
                s.close()
        except Exception as e:
            QMessageBox.critical(self, 'Échec de la connexion', f'Impossible de se connecter au serveur : {e}')
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

        self.plainTextEdit.insertPlainText("Bienvenue dans la salle de chat !")

        self.r = threading.Thread(target=self.recv)
        self.r.daemon = True
        self.r.start()

    def send(self):
        message = self.plainTextEdit_2.toPlainText()
        if message:
            full_message = f"{message}:;{user}:;------Chat de groupe-------"
            self.s.send(full_message.encode())
            self.plainTextEdit_2.setPlainText('')

    def recv(self):
        global users
        while True:
            try:
                data = self.s.recv(1024).decode()
                print("接收到数据:", data)  # 确认是否接收到数据的调试语句
                if not data:
                    print("没有接收到数据，断开连接")
                    break

                if ":;" in data:
                    data_parts = data.split(':;')
                    # 确保更新 UI 的操作在主线程中执行
                    QtCore.QMetaObject.invokeMethod(self, 'update_text', QtCore.Qt.QueuedConnection, 
                                                    QtCore.Q_ARG(list, data_parts))
                else:
                    print("数据不包含预期的分隔符")
            except Exception as e:
                print("接收数据时出现错误：", e)
                break

    @QtCore.pyqtSlot(list)
    def update_text(self, text_list):
        message, sender, receiver = text_list
        color_format = QTextCharFormat()
        
        # 根据发送者是否为当前用户设置消息颜色
        if sender == user:
            color_format.setForeground(QColor("blue"))
        else:
            color_format.setForeground(QColor("green"))
            
        # 在主线程中更新 UI
        self.plainTextEdit.setCurrentCharFormat(color_format)
        self.plainTextEdit.appendPlainText(f"{sender}: {message}")


    def private(self, item):
        self.chat = item.text()
        if self.chat == '------Chat de groupe-------':
            self.setWindowTitle(user)
            return
        self.setWindowTitle(user + '  -->  ' + self.chat)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = login_window()
    window.show()
    sys.exit(app.exec_())
