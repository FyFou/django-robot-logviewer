# Support pour les données CAN et les fichiers DBC

Cette branche ajoute le support pour les traces CAN et les fichiers DBC au projet LogViewer.

## Nouvelles fonctionnalités

### Import et gestion de fichiers DBC

- Téléchargement et stockage de fichiers DBC
- Visualisation du contenu des fichiers DBC (messages et signaux)
- Association des fichiers DBC aux fichiers MDF

### Support des traces CAN

- Détection automatique des canaux CAN dans les fichiers MDF
- Décodage des messages CAN à l'aide de fichiers DBC
- Visualisation des messages CAN et de leurs signaux

### Interface utilisateur améliorée

- Vue détaillée des messages CAN
- Filtrage par ID CAN
- Graphiques pour la distribution des messages CAN
- Graphiques pour l'évolution des valeurs des signaux
- Export des données CAN au format CSV

## Installation et mise à jour

Pour utiliser ces nouvelles fonctionnalités, vous devez :

1. Mettre à jour la base de données :
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

2. Installer les dépendances supplémentaires :
   ```bash
   pip install cantools  # Pour le décodage DBC (facultatif)
   ```

## Utilisation

### Import de fichiers DBC

1. Accédez à la page "Fichiers DBC" depuis le menu
2. Cliquez sur "Télécharger un fichier DBC"
3. Sélectionnez votre fichier DBC et donnez-lui un nom descriptif
4. Envoyez le formulaire pour importer le fichier

### Association de fichiers DBC aux fichiers MDF

Lors de l'import d'un fichier MDF, vous pouvez maintenant sélectionner un fichier DBC pour décoder les traces CAN présentes dans le fichier.

### Visualisation des données CAN

1. Accédez à un log de type CAN
2. Consultez les statistiques et les messages CAN
3. Filtrez par ID CAN pour explorer des messages spécifiques
4. Accédez aux détails d'un message pour voir les signaux décodés

## Mise à niveau des fichiers MDF existants

Pour les fichiers MDF déjà importés, vous pouvez associer un fichier DBC en modifiant directement l'objet MDFFile dans l'interface d'administration.

## Notes techniques

- Le décodage CAN fonctionne de manière optimale avec la bibliothèque `cantools`
- Si `cantools` n'est pas disponible, un décodeur de base est utilisé
- Les données décodées sont stockées dans la base de données pour une consultation ultérieure rapide
- Les performances peuvent être limitées pour les fichiers MDF contenant un grand nombre de messages CAN
