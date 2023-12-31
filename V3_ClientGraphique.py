import threading
import socket
import json  # json.dumps(some)  
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow,QMessageBox, QListWidgetItem
from PyQt5.QtCore import Qt, QTimer, QThread
from PyQt5.QtGui import QTextCharFormat, QImage, QColor, QPixmap, QKeyEvent, QStandardItemModel, QStandardItem

from client_output import Ui_Form
from chatroom_output import *

IP = ''
PORT = ''
user = ''
listbox1 = ''  # Boîte de liste pour afficher les utilisateurs en ligne
ii = 0  # Utilisé pour déterminer si la boîte de liste est ouverte ou fermée
users = []  # Liste des utilisateurs en ligne

class login_window(QtWidgets.QMainWindow, Ui_Form):
    def __init__(self):
        super(login_window, self).__init__()
        self.setupUi(self)  # Créer l'objet de la fenêtre
        self.init()

    def init(self):
        self.pushButton.clicked.connect(self.login_button)  # Connecter le slot
        self.pushButton_2.clicked.connect(self.register_button)  # Bouton d'inscription
        self.lineEdit_2.setText("127.0.0.1:8008")

    def login_button(self):
        global IP, PORT, user, Ui_Main
        try:
            IP, PORT = self.lineEdit_2.text().split(':')  # Récupérer l'IP et le numéro de port
            PORT = int(PORT)  # Le numéro de port doit être un int
        except ValueError:
            QMessageBox.warning(self, 'Avertissement', 'Veuillez entrer une adresse IP et un numéro de port corrects, format comme : 127.0.0.1:50007')
            return

        user = self.lineEdit_3.text()  # Récupérer le nom d'utilisateur
        password = self.lineEdit_password.text()  # Récupérer le mot de passe

        if not user or not password:
            QMessageBox.critical(self, 'Erreur', 'Le nom d\'utilisateur et le mot de passe ne peuvent pas être vides !')
            return

        # Se connecter au serveur et envoyer le nom d'utilisateur et le mot de passe
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((IP, PORT))
            credentials = f"{user}:{password}"
            s.send(credentials.encode())

            # Recevoir la réponse du serveur
            response = s.recv(1024).decode()
            if response == "Connexion réussie":
                self.hide()  # Cacher la fenêtre de connexion
                Ui_Main = main_window(s)  # Passer le socket à la fenêtre principale
                Ui_Main.setWindowTitle("Nom d'utilisateur : " + user)
                Ui_Main.show()
            else:
                QMessageBox.critical(self, 'Échec de la connexion', 'Nom d\'utilisateur ou mot de passe incorrect')
                s.close()
        except Exception as e:
            QMessageBox.critical(self, 'Échec de la connexion', f'Impossible de se connecter au serveur : {e}')
            if 's' in locals():
                s.close()  # Fermer le socket

    def register_button(self):
        global IP, PORT, user, Ui_Main
        try:
            IP, PORT = self.lineEdit_2.text().split(':')  # Récupérer l'IP et le numéro de port
            PORT = int(PORT)  # Le numéro de port doit être un int
        except ValueError:
            QMessageBox.warning(self, 'Avertissement', 'Veuillez entrer une adresse IP et un numéro de port corrects, format comme : 127.0.0.1:50007')
            return

        # Obtenir le nom d'utilisateur et le mot de passe
        username = self.lineEdit_3.text()
        password = self.lineEdit_password.text()

        if not username or not password:
            QMessageBox.critical(self, 'Erreur', 'Le nom d\'utilisateur et le mot de passe ne peuvent pas être vides pour l\'inscription !')
            return

        # Essayez de vous connecter au serveur et d'envoyer les informations d'inscription
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((IP, int(PORT)))
            credentials = f"register:{username}:{password}"
            s.send(credentials.encode())

            # Recevoir la réponse du serveur
            response = s.recv(1024).decode()
            if response == "Inscription réussie":
                QMessageBox.information(self, 'Succès', 'Inscription réussie.')
                s.close()
            else:
                QMessageBox.critical(self, 'Échec de l\'inscription', response)
                s.close()
        except Exception as e:
            QMessageBox.critical(self, 'Échec de la connexion', f'Impossible de se connecter au serveur : {e}')
            if 's' in locals():
                s.close()


class main_window(QtWidgets.QMainWindow, Ui_MainWindow):

    update_txt = QtCore.pyqtSignal(list)

    def __init__(self, socket):
        super(main_window, self).__init__()
        self.s = socket  # Utiliser la connexion socket établie
        self.r = threading.Thread()
        self.chat = '------Chat de groupe-------'
        self.setupUi(self)
        self.init()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        reply = QtWidgets.QMessageBox.question(self, 'Confirmation', "Êtes-vous sûr de vouloir quitter ?",
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                               QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            if self.s:
                self.s.close()
            event.accept()
        else:
            event.ignore()

    def init(self):
        self.pushButton.clicked.connect(self.send)  # Connecter le slot d'envoi
        self.listWidget.currentItemChanged.connect(self.private)
        self.pushButton_2.clicked.connect(self.quit_app)
        self.newButton.clicked.connect(self.insert_emoji)
        self.update_txt.connect(self.update_text)
        self.plainTextEdit.setReadOnly(True)

        # Pas besoin de se reconnecter, car la connexion a déjà été établie dans login_window
        if user:
            self.s.send(user.encode())  # Envoyer le nom d'utilisateur
        else:
            self.s.send('no'.encode())  # Marquer 'no' si aucun nom d'utilisateur n'est entré

        # Initialiser le message de bienvenue du chat
        self.plainTextEdit.insertPlainText("Bienvenue dans la salle de chat !")

        # Démarrer le thread de réception des messages
        self.r = threading.Thread(target=self.recv)
        self.r.daemon = True  # Définir la propriété daemon de cette manière
        self.r.start()

    def send(self, *args):
        # S'il n'y a pas d'interlocuteur, un message d'erreur sera affiché lors de l'envoi d'un message
        users.append('------Chat de groupe-------')
        users.append('--------Informatique-------')
        users.append('---------Marketing---------')
        users.append('------Comptabilite---------')
        if self.chat not in users:
            QMessageBox.warning(self, 'Erreur d\'envoi', 'Il n\'y a personne avec qui parler !')
            return
        if self.chat == user:
            QMessageBox.warning(self, 'Erreur d\'envoi', 'Vous ne pouvez pas discuter en privé avec vous-même !')
            return
        mes = self.plainTextEdit_2.toPlainText() + ':;' + user + ':;' + self.chat  # Ajouter le marqueur de l'interlocuteur
        self.s.send(mes.encode())
        self.plainTextEdit_2.setPlainText('')  # Vider la zone de texte après l'envoi

    def quit_app(self):
        # Close the socket connection safely
        if self.s:
            self.s.close()
        self.close()

    def insert_emoji(self):
        current_text = self.plainTextEdit_2.toPlainText()
        emoji = "😊"  # 示例表情符号
        new_text = current_text + emoji
        self.plainTextEdit_2.setPlainText(new_text)

    def recv(self):
        global users
        while True:
            try:
                data = self.s.recv(1024).decode()
                if not data:
                    break  # Si aucune donnée, sortir de la boucle

                if data.startswith('kick:'):
                    # Traiter les messages d'expulsion d'utilisateurs
                    kicked_user = data.split(':')[1]
                    if kicked_user == user:
                        # Si l'utilisateur expulsé est l'utilisateur actuel
                        QMessageBox.information(self, 'Expulsion', 'Vous avez été expulsé du serveur.')
                        self.s.close()
                        self.close()
                        return

                if data == "Le serveur va bientôt fermer":
                    # Si un message indiquant la fermeture du serveur est reçu
                    QMessageBox.information(self, 'Notification', 'Le serveur va bientôt fermer.')
                    self.s.close()  # Fermer la connexion socket
                    self.close()  # Fermer la fenêtre du client
                    return

                elif ":;" in data:
                    # Traiter les données non-JSON (peut-être des messages de chat ordinaires)
                    data = data.split(':;')
                    data1 = data[0].strip()  # Message
                    data2 = data[1]  # Nom d'utilisateur qui envoie le message
                    data3 = data[2]  # Interlocuteur
                    list_signal = [data1, data2, data3]
                    self.update_txt.emit(list_signal)
                else:
                    # Traiter les données JSON (peut-être la liste des utilisateurs en ligne)
                    try:
                        users = json.loads(data)
                        self.listWidget.clear()
                        number = ('   Utilisateurs en ligne : ' + str(len(users)))
                        item1 = QListWidgetItem(number)
                        item1.setForeground(QColor("green"))
                        item1.setBackground(QColor("#f0f0ff"))
                        self.listWidget.addItem(item1)

                        for channel in ['------Chat de groupe-------', '-------Informatique--------', '----------Marketing---------', '--------Comptabilité--------']:
                            channel_item = QListWidgetItem(channel)
                            self.listWidget.addItem(channel_item)

                        for i in range(len(users)):
                            item = QListWidgetItem(users[i])
                            item.setForeground(QColor("green"))
                            self.listWidget.addItem(item)
                    except json.JSONDecodeError:
                        print("Données non-JSON reçues :", data)

            except Exception as e:
                print(f"Erreur lors de la réception des données : {e}")
                break

    def update_text(self, textlist):
        data1 = textlist[0]
        data2 = textlist[1]
        data3 = textlist[2]
        color_format = QTextCharFormat()
        if data3 == '------Chat de groupe-------':
            if data2 == user:  # Si c'est soi-même, changer la couleur de la police en bleu
                color_format.setForeground(QColor("blue"))
                self.plainTextEdit.setCurrentCharFormat(color_format)
                self.plainTextEdit.appendPlainText(data1)
            else:
                color_format.setForeground(QColor("green"))
                self.plainTextEdit.setCurrentCharFormat(color_format)
                self.plainTextEdit.appendPlainText(data1)  # Ajouter le message à la fin
        elif data2 == user or data3 == user:  # Afficher les discussions privées
            color_format.setForeground(QColor("red"))
            self.plainTextEdit.setCurrentCharFormat(color_format)
            self.plainTextEdit.appendPlainText(data1)  # Ajouter le message à la fin
        QApplication.processEvents()

    def private(self, item):
        # Fonctionnalité de chat privé
        # Obtenir l'index cliqué puis récupérer le contenu (nom d'utilisateur)
        self.chat = item.text()
        # Modifier le titre du client
        if self.chat == '------Chat de groupe-------':
            self.setWindowTitle(user)
            return
        ti = user + '  -->  ' + self.chat
        self.setWindowTitle(ti)

if __name__ == '__main__':
    from PyQt5 import QtCore
    QtCore.QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)  # Adapter automatiquement la rés
    app = QtWidgets.QApplication(sys.argv)
    window = login_window()
    window.show()
    sys.exit(app.exec_())
