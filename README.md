# SAE302 BUT COLMAR RT231
# Chatroom PyQt
Un programme de chat basé sur PyQt5 offrant des communications en temps réel entre utilisateurs.

## Fonctionnalités

- Chat de groupe : communiquez avec plusieurs utilisateurs dans un espace commun.
- Chat privé : engagez des conversations privées avec d'autres utilisateurs sélectionnés.
- Visualisation des utilisateurs connectés : voyez qui est en ligne en temps réel.
- Commandes d'administration : les administrateurs peuvent gérer les utilisateurs et voir qui est en ligne.
- Interface utilisateur basée sur PyQt5 : une expérience utilisateur moderne et réactive.

## Commandes Administrateur

En plus des commandes standard pour démarrer et arrêter le serveur, une commande d'administration a été ajoutée pour permettre à l'administrateur de voir tous les utilisateurs actuellement connectés.

### Commandes Disponibles

- `show users` : Affiche la liste de tous les utilisateurs actuellement connectés avec leurs adresses IP et ports. Cette commande permet à l'administrateur de surveiller les utilisateurs actifs sur le serveur.

- `kick` : Permet à l'administrateur d'expulser un utilisateur du chat. Utilisez la commande suivie de l'identifiant de l'utilisateur et de la durée de l'expulsion en heures. Par exemple, `kick username 1` expulsera l'utilisateur `username` pendant 1 heure.

- `kill` : Cette commande arrête le serveur de chat immédiatement. Elle doit être utilisée avec précaution car elle déconnectera tous les utilisateurs actuellement en ligne.

### Utilisation des Commandes

Pour utiliser ces commandes, l'administrateur doit accéder à la console du serveur et saisir la commande souhaitée. Un retour approprié sera affiché dans la console pour confirmer l'action effectuée.


## Serveur

Le serveur est configuré pour fonctionner sur le port `8008` et utilise l'adresse IP locale `127.0.0.1`.

### Fonctionnalités du Serveur

- Gestion des connexions simultanées dans des threads séparés.
- Authentification des utilisateurs via une base de données MySQL.
- Prise en charge de l'enregistrement de nouveaux comptes utilisateur.
- Transmission des messages reçus aux clients appropriés.

## Client

### Fenêtre de Connexion (login_window)

- Recueille les informations de connexion des utilisateurs, telles que l'IP, le port, le nom d'utilisateur et le mot de passe.
- Donne la possibilité aux nouveaux utilisateurs de créer un compte.

### Fenêtre Principale (main_window)

- Affiche les messages du chat de groupe et permet de sélectionner des utilisateurs pour un chat privé.
- Met à jour la liste des utilisateurs en ligne en temps réel.

### Protocole de Communication

Les messages sont envoyés en suivant un format spécifique :

```plaintext
"texte_du_message ':;' nom_utilisateur ':;' nom_destinataire"
```

- Les messages de chat de groupe n'incluent pas de destinataire spécifique, tandis que les messages privés incluent le nom d'utilisateur du destinataire.
- Le serveur utilise le séparateur `':;'` pour analyser les messages et déterminer leur type et destination.

## Instructions d'utilisation

### Démarrage du Serveur

![image de démarrage du serveur](/etage1.png)

Lancez le script `server.py` pour démarrer le serveur. Si le message "Le serveur de chat commence à fonctionner..." s'affiche, le serveur est prêt.

### Lancement des Clients

#### Mode Chat de Groupe

Les messages envoyés par vous-même apparaissent en bleu, et ceux reçus des autres en vert.

![image du mode chat de groupe](/etage2.png)

#### Mode Chat Privé

Sélectionnez un utilisateur pour entrer en mode chat privé avec cette personne. Les messages apparaissent en rouge.

![image du mode chat privé](/etage3.png)

En sélectionnant '------Chat de groupe-------', vous revenez au mode chat de groupe.
```

