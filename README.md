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

## Explications sur les fichiers V3/V4

**V3** correspond à un serveur textuel avec un client graphique, et remplit toutes les exigences de SAE302. 

**V4**, quant à lui, représente un serveur graphique et un client graphique. Toutefois, des problèmes sont survenus lors des interactions entre le client et le serveur, empêchant l'affichage correct sur l'interface utilisateur du client. Bien que le système permette à l'administrateur d'approuver les demandes d'accès aux canaux privés, les problèmes d'interaction ont causé une défaillance dans la réception des messages de réponse appropriés par le client, l'empêchant ainsi de rejoindre les canaux.
![image du mode chat privé](/etage4.png)
Vous pouvez voir sur la console que le message envoyé par le client a été reçu avec succès mais qu'il y a eu un problème avec le retour.
## Analyse du Problème

Je pense que le problème réside dans les fonctions d'envoi et de réception, mais la complexité du code a augmenté en raison de la nécessité d'adapter le serveur graphique à l'interface utilisateur. Ce problème pourrait être résolu si nous avions plus de temps. L'utilisation de QT pour la création de l'interface utilisateur est très pratique, mais le débogage du code nécessite plus de temps.

## supplémentaire
Pour ajouter la prise en charge des emoji à votre discussion, vous pouvez ajouter un bouton emoji à côté de la zone de saisie de texte. Lorsque l'utilisateur clique sur ce bouton, une petite fenêtre contenant des emojis s'ouvre parmi lesquelles l'utilisateur peut choisir.

Étant donné que la mise en œuvre d'un sélecteur d'émoticônes complet nécessite davantage de conception d'interface utilisateur et de gestion des événements, une méthode simplifiée est fournie ici, en insérant simplement une émoticône fixe dans la zone de texte à titre d'exemple.
![image du mode chat privé](/etage5.png)

Dans votre code, la fonction de notification des messages est constituée de plusieurs éléments clés au sein de la classe `main_window` :
1. **Définition du Signal** :
   Un signal nommé `new_message_signal` est défini dans la classe `main_window`. Ce signal est utilisé pour communiquer lors de la réception d'un nouveau message. Le signal est défini comme `QtCore.pyqtSignal(str)`, ce qui signifie qu'il transmettra un argument de type chaîne de caractères (le contenu du message).

2. **Connexion du Signal** :
   Dans la méthode d'initialisation (`__init__`) de `main_window`, le signal `new_message_signal` est connecté à la méthode `show_notification`. Cela signifie que lorsque le signal est déclenché, la méthode `show_notification` est appelée.

   ```python
   self.new_message_signal.connect(self.show_notification)
   ```

3. **Réception du Message et Déclenchement du Signal** :
   Dans la méthode `recv`, lorsque de nouvelles données de message sont reçues du serveur, ces données sont analysées et le signal `new_message_signal` est émis pour gérer le message. Ce signal porte le contenu du message reçu du serveur.

   ```python
   self.new_message_signal.emit(actual_message)
   ```

4. **Méthode de Notification des Messages** (`show_notification`) :
   C'est une méthode slot qui traite le signal `new_message_signal`. Elle reçoit un argument de type chaîne de caractères (le contenu du message).
![image du mode chat privé](/etage6.png)