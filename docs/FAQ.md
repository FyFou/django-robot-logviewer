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

2. Ou utiliser ce script plus simple qui contourne les problèmes d'API :
   ```python
   import numpy as np
   from asammdf import MDF
   from asammdf.blocks.mdf_v4 import Signal

   # Créer un fichier MDF simple
   mdf = MDF()

   # Ajouter un signal simple
   timestamps = np.linspace(0, 10, 100)
   signal = np.sin(timestamps)

   # Créer un Signal et l'ajouter
   s = Signal(
       samples=signal,
       timestamps=timestamps,
       name='sinus'
   )
   mdf.append([s])

   # Sauvegarder
   mdf.save('test_simple.mdf', overwrite=True)
   print("Fichier MDF simple créé")
   ```

### L'importation de fichiers MDF échoue

**Problème**: Vous ne pouvez pas importer de fichiers MDF depuis l'interface web.

**Causes possibles**:
1. La bibliothèque asammdf n'est pas correctement installée
2. Les permissions de fichier sont incorrectes
3. Le format MDF du fichier n'est pas compatible

**Solutions**:
1. Vérifier l'installation d'asammdf :
   ```bash
   pip install asammdf --upgrade
   ```

2. Vérifier que le dossier `media` existe et a les bonnes permissions :
   ```bash
   mkdir -p media/log_data media/log_images media/mdf_files
   chmod -R 755 media  # Sur Linux/Mac
   ```

3. Essayer avec un fichier MDF simple généré par le script fourni :
   ```bash
   python scripts/generate_test_mdf.py
   ```

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
