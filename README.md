# LogViewer - Application Django pour visualiser les logs de robots

Cette application permet de visualiser, filtrer et exporter les logs de robots dans une interface web intuitive.

## Fonctionnalités

- Affichage des logs avec pagination
- Filtrage par niveau de log, robot, date et recherche
- Exportation des logs en CSV
- Interface d'administration pour la gestion des logs
- Actualisation automatique des logs
- Support pour les fichiers MDF (Measurement Data Format)
- Support des channel groups pour une meilleure organisation des données
- Visualisation de courbes, données laser 2D et images

## Installation

1. Cloner le dépôt
2. Créer un environnement virtuel:
   ```bash
   python -m venv logviewer_env
   source logviewer_env/bin/activate  # Sur macOS/Linux
   source logviewer_env/Scripts/activate  # Sur macOS/Linux
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
   # Générer uniquement des logs de test
   python manage.py generate_test_logs 1000
   
   # Générer des logs et des fichiers MDF de test
   python manage.py generate_test_logs 1000 --mdf
   
   # Spécifier le nombre de fichiers MDF à générer
   python manage.py generate_test_logs 1000 --mdf --mdf-count 5
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
4. Activez ou désactivez l'option "Utiliser les channel groups" selon vos besoins
5. Confirmez l'importation
6. Consultez les logs générés dans l'interface principale

Les différents types de données (texte, courbes, laser 2D, images) seront automatiquement détectés et des visualisations appropriées seront générées.

### Support des Channel Groups

La fonctionnalité de channel groups permet d'organiser les logs selon la structure originale du fichier MDF:

- Lors de l'importation, un groupe principal est créé pour le fichier
- Des sous-groupes sont créés pour chaque channel group du fichier MDF
- Les logs sont organisés hiérarchiquement dans ces groupes
- La navigation et l'analyse sont ainsi facilitées

Pour plus de détails, consultez la [documentation des channel groups](README_CHANNEL_GROUPS.md).

### Support des données CAN

Pour les données CAN, consultez la [documentation spécifique](README_CAN_DBC.md).

### Support des courbes

Pour les données de courbes, consultez la [documentation dédiée](README_CURVES.md).

### Générer un fichier MDF de test

Si vous n'avez pas de fichier MDF à disposition, vous pouvez en générer un avec le script fourni:

```bash
# Assurer que asammdf est installé
pip install asammdf numpy

# Générer un fichier MDF
python scripts/generate_test_mdf.py
```

Le fichier sera généré dans le répertoire courant sous le nom `test_mdf_file.mdf`.

## Résolution des problèmes

Si vous rencontrez des difficultés lors de l'installation ou de l'utilisation de LogViewer, consultez la [FAQ](docs/FAQ.md) qui couvre les problèmes les plus courants et leurs solutions.

## Structure du projet

- `logViewer/` : Répertoire principal du projet Django
- `robot_logs/` : Application Django pour la gestion des logs
- `robot_logs/models.py` : Modèle de données pour les logs
- `robot_logs/views.py` : Vues pour l'affichage et l'exportation des logs
- `robot_logs/templates/` : Templates HTML pour l'interface utilisateur
- `robot_logs/mdf_parser.py` : Utilitaire pour parser les fichiers MDF
- `scripts/` : Scripts utilitaires (génération de fichiers MDF de test)
- `docs/` : Documentation supplémentaire, incluant la FAQ
