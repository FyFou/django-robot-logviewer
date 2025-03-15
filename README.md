# LogViewer - Application Django pour visualiser les logs de robots

Cette application permet de visualiser, filtrer et exporter les logs de robots dans une interface web intuitive.

## Fonctionnalités

- Affichage des logs avec pagination
- Filtrage par niveau de log, robot, date et recherche
- Exportation des logs en CSV
- Interface d'administration pour la gestion des logs
- Actualisation automatique des logs
- Support pour les fichiers MDF (Measurement Data Format)
- Visualisation de courbes, données laser 2D et images

## Installation

1. Cloner le dépôt
2. Créer un environnement virtuel:
   ```bash
   python -m venv logviewer_env
   source logviewer_env/bin/activate  # Sur macOS/Linux
   logviewer_env\Scripts\activate  # Sur Windows
   ```
3. Installer les dépendances:
   ```bash
   pip install -r requirements.txt
   ```
4. Créer les migrations:
   ```bash
   python manage.py makemigrations
   ```
5. Effectuer les migrations:
   ```bash
   python manage.py migrate
   ```
6. Créer un superutilisateur:
   ```bash
   python manage.py createsuperuser
   ```
7. Générer des données de test (optionnel):
   ```bash
   python manage.py generate_test_logs 1000
   ```
8. Lancer le serveur de développement:
   ```bash
   python manage.py runserver
   ```

## Utilisation

- Accédez à l'interface d'administration via /admin/
- Consultez les logs via l'interface principale à la racine du site
- Utilisez les filtres pour affiner votre recherche
- Exportez les logs filtrés en CSV

### Support MDF

L'application prend en charge l'importation de fichiers MDF (Measurement Data Format) développés par Vector Informatik GmbH. Pour importer un fichier MDF:

1. Cliquez sur le bouton "Importer fichier MDF" sur la page principale
2. Sélectionnez votre fichier MDF et donnez-lui un nom descriptif
3. Choisissez si vous souhaitez prévisualiser le contenu avant l'importation
4. Confirmez l'importation
5. Consultez les logs générés dans l'interface principale

Les différents types de données (texte, courbes, laser 2D, images) seront automatiquement détectés et des visualisations appropriées seront générées.

## Structure du projet

- `logViewer/` : Répertoire principal du projet Django
- `robot_logs/` : Application Django pour la gestion des logs
- `robot_logs/models.py` : Modèle de données pour les logs
- `robot_logs/views.py` : Vues pour l'affichage et l'exportation des logs
- `robot_logs/templates/` : Templates HTML pour l'interface utilisateur
- `robot_logs/mdf_parser.py` : Utilitaire pour parser les fichiers MDF
