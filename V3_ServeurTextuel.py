import socket
import threading
import queue
import json  # json.dumps(some)打包   json.loads(some)解包
import time
import os
import os.path
import requests
import sys
import mysql.connector

# IP = socket.gethostbyname(socket.getfqdn(socket.gethostname()))
IP = ''
PORT = 8008
msg = queue.Queue()                             # File d'attente pour stocker les messages envoyés par les clients
users = []                                      # Liste pour stocker les informations des utilisateurs en ligne [conn, user, addr]
lock = threading.Lock()                         # Création d'un verrou pour éviter le désordre dans l'écriture des données par plusieurs threads

# Informations de connexion à la base de données
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'toto'
DB_DATABASE = 'SAE302'

# Fonction pour obtenir la liste des utilisateurs en ligne et la retourner
def onlines():
    online = []
    for i in range(len(users)):
        online.append(users[i][1])
    return online

# Fonction pour se connecter à la base de données
def connect_to_database():
    try:
        db = mysql.connector.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_DATABASE)
        print("[INFO] Connexion à la base de données réussie.")
        return db
    except Exception as e:
        print("[ERREUR] Échec de la connexion à la base de données:", e)
        raise


class ChatServer(threading.Thread):
    global users, msg, lock

    def __init__(self, port):
        threading.Thread.__init__(self)
        self.ADDR = ('', port)
        os.chdir(sys.path[0])  # Ouvre le répertoire du script
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

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
            print("[ERROR] lors de la validation de l'utilisateur:", e)
            return False
        finally:
            cursor.close()
            db.close()

    def tcp_connect(self, conn, addr):
        try:
            # Recevoir les informations du client
            credentials = conn.recv(1024).decode()

            # Vérifier si c'est une demande de connexion ou d'enregistrement
            if credentials.startswith('register:'):
                # Gérer la demande d'enregistrement
                self.register_new_user(credentials[len('register:'):], conn)
            else:
                # Gérer la demande de connexion
                username, password = credentials.split(':')  # Format "nom_utilisateur:mot_de_passe"

                if self.validate_user(username, password):
                    conn.send("Connexion réussie".encode())
                    print(f"L'utilisateur {username} a été validé avec succès et est maintenant connecté.")
                    users.append((conn, username, addr))
                    print('Nouvelle connexion:', addr, ':', username)
                    d = onlines()
                    self.recv(d, addr)
                else:
                    conn.send("Échec de la connexion".encode())
                    print(f"Échec de la validation pour l'utilisateur {username}.")
                    conn.close()
                    return

            # Continuer à recevoir les informations du client
            try:
                while True:
                    data = conn.recv(1024).decode()
                    if not data:
                        break
                    self.recv(data, addr)
            except Exception as e:
                print(f"Perte de connexion avec {username} : {e}")
            finally:
                self.delUsers(conn, addr)
                conn.close()

        except ValueError as ve:
            print(f"Erreur d'analyse des données : {ve}")
            conn.send("Format de données incorrect".encode())
            conn.close()
            return
        except Exception as e:
            print(f"Erreur inconnue : {e}")
            conn.close()
            return

    def register_new_user(self, credentials, conn):
        username, password = credentials.split(':')
        db = connect_to_database()
        cursor = db.cursor()

        try:
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s", (username,))
            if cursor.fetchone()[0] > 0:
                conn.send("Nom d'utilisateur déjà existant".encode())
                return

            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            db.commit()
            conn.send("Inscription réussie".encode())
        except Exception as e:
            print(f"Erreur lors de l'inscription : {e}")
            conn.send("Échec de l'inscription".encode())
        finally:
            cursor.close()
            db.close()

    # Identifier l'utilisateur déconnecté dans la liste des utilisateurs et le retirer, rafraîchir l'affichage des utilisateurs en ligne
    def delUsers(self, conn, addr):
        a = 0
        for i in users:
            if i[0] == conn:
                users.pop(a)
                print('Utilisateurs en ligne restants : ', end='')  # Afficher les utilisateurs en ligne restants (conn)
                d = onlines()
                self.recv(d, addr)
                print(d)
                break
            a += 1

    # Stocker les informations reçues (IP, port et message envoyé) dans la file d'attente msg
    def recv(self, data, addr):
        lock.acquire()
        try:
            msg.put((addr, data))
        finally:
            lock.release()

    # Envoyer les messages de la file d'attente msg à tous les utilisateurs connectés
    def sendData(self):
        while True:
            if not msg.empty():
                data = ''
                reply_text = ''
                message = msg.get()  # Prendre le premier élément de la file
                if isinstance(message[1], str):  # Si le message est une chaîne de caractères
                    for i in range(len(users)):
                        # user[i][1] est le nom d'utilisateur, users[i][2] est l'adresse, remplacer message[0] par le nom d'utilisateur
                        for j in range(len(users)):
                            if message[0] == users[j][2]:
                                print('Ce message vient de l\'utilisateur[{}]'.format(j))
                                data = ' ' + users[j][1] + ' : ' + message[1]
                                break
                        users[i][0].send(data.encode())
                if isinstance(message[1], list):  # Si le message est une liste (lors de la connexion du client)
                    # Si c'est une liste, l'empaqueter puis l'envoyer directement
                    data = json.dumps(message[1])
                    for i in range(len(users)):
                        try:
                            users[i][0].send(data.encode())
                        except:
                            pass

    def run(self):
        # Associer le socket du serveur à l'adresse spécifiée
        self.s.bind(self.ADDR)
        # Le serveur commence à écouter le port
        self.s.listen(5)
        print('Le serveur de chat commence à fonctionner...')

        # Lancer un thread pour gérer les données de la file d'attente et les envoyer à tous les clients
        q = threading.Thread(target=self.sendData)
        q.start()

        # Nouveau : Lancer un thread pour recevoir les commandes de l'administrateur
        admin_thread = threading.Thread(target=self.receive_admin_command)
        admin_thread.start()

        # Boucle principale : attendre et accepter de nouvelles connexions client
        while True:
            conn, addr = self.s.accept()
            # Créer un nouveau thread pour chaque connexion client pour gérer la réception des données
            t = threading.Thread(target=self.tcp_connect, args=(conn, addr))
            t.start()

    # Nouvelle méthode pour recevoir les commandes de l'administrateur
    def receive_admin_command(self):
        while True:
            cmd = input("Entrez la commande de l'administrateur : ")
            if cmd == "show users":
                self.show_all_users()
            if cmd.startswith("kick"):
                parts = cmd.split(" ")
                if len(parts) >= 3 and parts[2].isdigit():
                    username = parts[1].lstrip('@')
                    duration = int(parts[2])
                    self.kick_user(username, duration)
            elif cmd == "kill":
                # Exécuter la méthode kill_server lorsque la commande "kill" est reçue
                self.kill_server()

    # Méthode pour réautoriser la connexion d'un utilisateur
    def reallow_user(self, username):
        print(f"L'utilisateur {username} peut maintenant se reconnecter.")

    # Nouvelle méthode pour gérer l'expulsion des utilisateurs
    def kick_user(self, username, duration):
        global users, lock
        lock.acquire()
        try:
            for user in users:
                conn, uname, addr = user
                if uname == username:
                    try:
                        conn.send(f"Expulsion:{username}:{duration}".encode())
                    except:
                        pass
                    # Configurer un minuteur pour réautoriser la connexion de l'utilisateur après un certain temps
                    threading.Timer(duration * 3600, self.reallow_user, args=(username,)).start()
                    # Fermer la connexion de l'utilisateur
                    conn.close()
                    users.remove(user)
                    print(f"L'utilisateur {username} a été expulsé pour une durée de {duration} heures.")
                    break
        finally:
            lock.release()

    def kill_server(self):
        global users, lock
        lock.acquire()
        try:
            # Envoyer un message à tous les utilisateurs indiquant que le serveur va bientôt fermer
            for conn, _, _ in users:
                try:
                    conn.send("Le serveur va bientôt fermer".encode())
                except Exception as e:
                    print(f"Échec de l'envoi du message de fermeture : {e}")
            time.sleep(1)  # Attendre brièvement pour s'assurer que le message est envoyé
        finally:
            lock.release()
            os._exit(0)  # Arrêter immédiatement le programme

    def show_all_users(self):
        # This new method prints the list of all currently connected users
        with lock:  # Make sure to use the lock to prevent concurrent access
            print("Liste des utilisateurs connectés :")
            for conn, username, addr in users:
                print(f"{username} - {addr[0]}:{addr[1]}")

if __name__ == '__main__':
    cserver = ChatServer(PORT)
    cserver.start()
    while True:
        time.sleep(1)
        if not cserver.is_alive():
            print("Connexion au chat perdue...")
            sys.exit(0)
