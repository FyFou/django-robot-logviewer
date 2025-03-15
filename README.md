# LogViewer - Application Django pour visualiser les logs de robots

Cette application permet de visualiser, filtrer et exporter les logs de robots dans une interface web intuitive.

## Fonctionnalités

- Affichage des logs avec pagination
- Filtrage par niveau de log, robot, date et recherche
- Exportation des logs en CSV
- Interface d'administration pour la gestion des logs
- Actualisation automatique des logs

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
4. Effectuer les migrations:
   ```bash
   python manage.py migrate
   ```
5. Créer un superutilisateur:
   ```bash
   python manage.py createsuperuser
   ```
6. Générer des données de test (optionnel):
   ```bash
   python manage.py generate_test_logs 1000
   ```
7. Lancer le serveur de développement:
   ```bash
   python manage.py runserver
   ```

## Utilisation

- Accédez à l'interface d'administration via /admin/
- Consultez les logs via l'interface principale à la racine du site
- Utilisez les filtres pour affiner votre recherche
- Exportez les logs filtrés en CSV

## Structure du projet

- `logViewer/` : Répertoire principal du projet Django
- `robot_logs/` : Application Django pour la gestion des logs
- `robot_logs/models.py` : Modèle de données pour les logs
- `robot_logs/views.py` : Vues pour l'affichage et l'exportation des logs
- `robot_logs/templates/` : Templates HTML pour l'interface utilisateur
