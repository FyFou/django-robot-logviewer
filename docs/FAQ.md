# FAQ - LogViewer

Cette FAQ recense les problèmes fréquemment rencontrés lors de l'installation et de l'utilisation de LogViewer, ainsi que leurs solutions.

## Problèmes d'installation et de configuration

### L'erreur "no such table: robot_logs_robotlog" apparaît

**Problème**: Lors de l'exécution de commandes comme `generate_test_logs`, vous obtenez une erreur indiquant que la table `robot_logs_robotlog` n'existe pas.

**Cause**: Les migrations Django n'ont pas été correctement créées ou appliquées.

**Solution**:
1. Supprimer la base de données existante (si elle existe) :
   ```bash
   rm db.sqlite3  # Sur Linux/Mac
   # Sur Windows, supprimez manuellement le fichier db.sqlite3
   ```

2. Supprimer tous les fichiers de migration existants (sauf `__init__.py`) :
   ```bash
   # Sur Linux/Mac
   rm robot_logs/migrations/0*.py
   
   # Sur Windows, supprimez manuellement les fichiers 
   # comme 0001_initial.py du dossier robot_logs/migrations/
   ```

3. Créer les nouvelles migrations :
   ```bash
   python manage.py makemigrations robot_logs
   ```

4. Appliquer les migrations :
   ```bash
   python manage.py migrate
   ```

5. Créer un superutilisateur :
   ```bash
   python manage.py createsuperuser
   ```

6. Générer les logs de test :
   ```bash
   python manage.py generate_test_logs 1000 --mdf
   ```

### Avertissement "URL namespace 'robot_logs' isn't unique"

**Problème**: Un avertissement indique que "URL namespace 'robot_logs' isn't unique".

**Cause**: Dans le fichier `logViewer/urls.py`, les URLs de l'application `robot_logs` sont incluses deux fois avec le même espace de noms.

**Solution**: Modifiez le fichier `logViewer/urls.py` comme suit :
```python
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('logs/', include('robot_logs.urls')),
    # Remplacer l'inclusion des URLs par une redirection
    path('', RedirectView.as_view(url='logs/', permanent=True)),
]
```

## Problèmes liés à la génération de fichiers MDF

### Erreur lors de la génération de fichiers MDF avec le script generate_test_mdf.py

**Problème**: Le script `generate_test_mdf.py` échoue avec une erreur comme `'str' object has no attribute 'name'`.

**Cause**: Incompatibilité avec la version d'asammdf installée.

**Solutions**:
1. Installer une version spécifique d'asammdf :
   ```bash
   pip install asammdf==5.21.0
   ```

2. Utiliser le script `simple_mdf_generator.py` qui est plus robuste face aux différentes versions :
   ```bash
   python scripts/simple_mdf_generator.py
   ```

### Erreur "Le fichier soumis est vide" lors de l'importation MDF

**Problème**: Lors de l'importation d'un fichier MDF via l'interface web, vous obtenez l'erreur "Le fichier soumis est vide" même si le fichier existe et n'est pas vide.

**Causes possibles**:
1. Le fichier MDF généré a réellement une taille de 0 octet
2. Django ne détecte pas correctement le fichier téléchargé
3. Problèmes de permissions de fichier
4. Problèmes de configuration Django

**Solutions**:

1. Vérifier la taille réelle du fichier MDF :
   ```bash
   # Sur Windows
   dir test_mdf_file.mdf
   # Sur Linux/Mac
   ls -l test_mdf_file.mdf
   ```

2. Utiliser le script `test_mdf_import.py` pour contourner l'interface web :
   ```bash
   python scripts/test_mdf_import.py test_mdf_file.mdf
   ```

3. Vérifier que les dossiers médias existent et ont les bonnes permissions :
   ```bash
   mkdir -p media/log_data media/log_images media/mdf_files
   chmod -R 755 media  # Sur Linux/Mac
   ```

4. Mettre à jour les paramètres Django (`settings.py`) avec les lignes suivantes :
   ```python
   # Media files
   MEDIA_URL = '/media/'
   MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

   # Ensure media directories exist
   os.makedirs(os.path.join(MEDIA_ROOT, 'log_data'), exist_ok=True)
   os.makedirs(os.path.join(MEDIA_ROOT, 'log_images'), exist_ok=True)
   os.makedirs(os.path.join(MEDIA_ROOT, 'mdf_files'), exist_ok=True)
   ```

5. Configurer les URLs pour servir les fichiers médias (`logViewer/urls.py`) :
   ```python
   from django.conf import settings
   from django.conf.urls.static import static

   urlpatterns = [
       # ...
   ]

   # Ajouter les URLs pour servir les fichiers médias en développement
   if settings.DEBUG:
       urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
   ```

6. Redémarrer le serveur Django

## Problèmes d'utilisation

### Les logs spéciaux (courbes, laser, images) ne s'affichent pas correctement

**Problème**: Vous ne voyez pas les visualisations des courbes, des scans laser ou des images.

**Causes possibles**:
1. Les bibliothèques JavaScript nécessaires ne sont pas chargées
2. Les données associées n'ont pas été correctement créées

**Solutions**:
1. Vérifier que les CDN pour Bootstrap, Chart.js et D3.js sont accessibles
2. Régénérer les logs avec la commande :
   ```bash
   python manage.py generate_test_logs 100 --mdf
   ```
3. Vérifier dans l'interface d'administration que les logs ont bien des données associées (CurveMeasurement, Laser2DScan, ImageData)

### Les fichiers MDF importés n'apparaissent pas dans la liste

**Problème**: Vous avez importé des fichiers MDF mais ils n'apparaissent pas dans la liste des fichiers.

**Solution**:
1. Vérifier dans l'interface d'administration (/admin) que les objets MDFFile ont bien été créés
2. Vérifier que le dossier `media/mdf_files` existe et a les bonnes permissions
3. Essayer d'importer à nouveau le fichier en cochant l'option "Prévisualiser d'abord"

## Problèmes liés à l'environnement

### Django ne trouve pas les templates

**Problème**: Erreurs "TemplateDoesNotExist" lors de l'affichage des pages.

**Solution**: Vérifier que la structure de répertoire est correcte :
```
robot_logs/
└── templates/
    └── robot_logs/
        ├── base.html
        ├── log_list.html
        ├── log_detail.html
        └── ...
```

### Problèmes avec les dépendances Python

**Problème**: Erreurs d'importation ou fonctionnalités manquantes.

**Solution**: Réinstaller toutes les dépendances avec :
```bash
pip install -r requirements.txt --upgrade
```

### Problèmes de performance avec de grandes quantités de logs

**Problème**: L'application devient lente avec beaucoup de logs.

**Solutions**:
1. Utiliser l'index par "type de log" lors des recherches
2. Limiter le nombre de logs générés pour les tests
3. Utiliser la pagination et les filtres
