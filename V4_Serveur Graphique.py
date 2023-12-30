import socket
import threading
import queue
import json
import sys
import mysql.connector
from PyQt5 import QtWidgets, QtCore
from Server_output import Ui_MainWindow  # 替换为您的UI类
import logging

# 设置日志
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    handlers=[logging.FileHandler("server_debug.log", encoding='utf-8'), 
                              logging.StreamHandler()])
logger = logging.getLogger(__name__)

# 数据库和其他全局变量配置
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'toto'
DB_DATABASE = 'SAE302'
IP = ''
PORT = 8008
msg = queue.Queue()
users = []
lock = threading.Lock()

# 连接到数据库的函数
def connect_to_database():
    try:
        db = mysql.connector.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_DATABASE)
        logger.info("数据库连接成功。")
        return db
    except Exception as e:
        logger.error("连接数据库失败:", e)
        raise

# 将在线用户存入online列表并返回
def onlines(users):
    return [user[1] for user in users]

class ChatServer(QtCore.QObject):
    update_user_list = QtCore.pyqtSignal(list)

    def __init__(self, port, parent=None):
        super().__init__(parent)
        self.ADDR = ('', port)
        self.is_running = False
        self.server_socket = None
        self.users = []
        self.msg_queue = queue.Queue()
        self.lock = threading.Lock()
        self.banned_users = set()

    def start_server(self):
        if not self.is_running:
            self.is_running = True
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind(self.ADDR)
            self.server_socket.listen(5)
            logger.info('Chat server starts running...')
            threading.Thread(target=self.accept_connections, daemon=True).start()
            threading.Thread(target=self.sendData, daemon=True).start()

    def stop_server(self):
        if self.is_running:
            self.is_running = False
            if self.server_socket:
                self.server_socket.close()
                self.server_socket = None
            logger.info('Chat server stopped.')

    def accept_connections(self):
        while self.is_running:
            conn, addr = self.server_socket.accept()
            threading.Thread(target=self.tcp_connect, args=(conn, addr), daemon=True).start()

    def tcp_connect(self, conn, addr):
        try:
            credentials = conn.recv(1024).decode()
            username, password = credentials.split(':')
            if username in self.banned_users:
                conn.send("You are banned.".encode())
                conn.close()
                return
            if self.validate_user(username, password):
                conn.send("登录成功".encode())
                with lock:
                    self.users.append((conn, username, addr))
                self.update_online_users()
                threading.Thread(target=self.recv, args=(conn, addr), daemon=True).start()
            else:
                conn.send("登录失败".encode())
                conn.close()
        except Exception as e:
            logger.error(f"Connection error: {e}")
            conn.close()

    def update_online_users(self):
        online_users = onlines(self.users)
        self.update_user_list.emit(online_users)

    def recv(self, conn, addr):
        while True:
            try:
                data = conn.recv(1024).decode()
                logger.debug(f"Raw data received from {addr}: {data}")
                if data:
                    with lock:
                        self.msg_queue.put((addr, data))
                else:
                    break
            except Exception as e:
                logger.error(f"Error receiving data from {addr}: {e}")
                break
        self.delUsers(conn, addr)
        
    def sendData(self):
        while True:
            if not self.msg_queue.empty():
                with lock:
                    addr, data = self.msg_queue.get()
                try:
                    if data.count(':;') != 2:
                        logger.error(f"Received data in wrong format: {data}")
                        continue
                    message, sender, receiver = data.split(':;')
                    send_data = f"{message}:;{sender}:;{receiver}"
                    if receiver == "ALL":
                        for user in self.users:
                            try:
                                user[0].send(send_data.encode())
                            except Exception as e:
                                logger.error(f"Error sending message to {user[1]}: {e}")
                                self.delUsers(user[0], user[2])
                    else:
                        for user in self.users:
                            if user[1] == receiver:
                                try:
                                    user[0].send(send_data.encode())
                                    break
                                except Exception as e:
                                    logger.error(f"Error sending private message to {user[1]}: {e}")
                                    self.delUsers(user[0], user[2])
                                    break
                except Exception as e:
                    logger.error(f"Error processing message: {e}")

    def delUsers(self, conn, addr):
        with lock:
            for i, user in enumerate(self.users):
                if user[0] == conn:
                    self.users.pop(i)
                    leave_msg = f"{user[1]} has left the chat room."
                    self.broadcast(leave_msg)
                    break
        conn.close()
        self.update_online_users()

    def validate_user(self, username, password):
        db = connect_to_database()
        cursor = db.cursor()
        try:
            cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
            result = cursor.fetchone()
            if result and result[0] == password:
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"验证用户时出错: {e}")
            return False
        finally:
            cursor.close()
            db.close()

    def broadcast(self, message):
        for user in self.users:
            try:
                user[0].send(message.encode())
            except Exception as e:
                logger.error(f"Error sending message to {user[1]}: {e}")
                self.delUsers(user[0], user[2])

    def kick_user(self, username):
        for user in self.users:
            if user[1] == username:
                try:
                    user[0].send("You have been kicked out.".encode())
                    user[0].close()
                    self.delUsers(user[0], user[2])
                except Exception as e:
                    logger.error(f"Error kicking out {username}: {e}")
                break

    def ban_user(self, username):
        self.banned_users.add(username)
        self.kick_user(username)

class ServerWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(ServerWindow, self).__init__()
        self.setupUi(self)
        self.server = ChatServer(PORT)
        self.server.update_user_list.connect(self.refresh_user_list)
        self.startServerButton.clicked.connect(self.start_server)
        self.stopServerButton.clicked.connect(self.stop_server)

    def start_server(self):
        self.server.start_server()

    def stop_server(self):
        self.server.stop_server()

    def refresh_user_list(self, user_list):
        self.userTable.setRowCount(len(user_list))
        for row, username in enumerate(user_list):
            self.userTable.setItem(row, 0, QtWidgets.QTableWidgetItem(username))
            kick_button = QtWidgets.QPushButton('踢出')
            kick_button.clicked.connect(lambda checked, user=username: self.kick_user(user))
            self.userTable.setCellWidget(row, 1, kick_button)
            ban_button = QtWidgets.QPushButton('封禁')
            ban_button.clicked.connect(lambda checked, user=username: self.ban_user(user))
            self.userTable.setCellWidget(row, 2, ban_button)

    def kick_user(self, username):
        self.server.kick_user(username)

    def ban_user(self, username):
        self.server.ban_user(username)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    mainWindow = ServerWindow()
    mainWindow.show()
    sys.exit(app.exec_())
