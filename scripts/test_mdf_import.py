"""
Script pour tester l'importation d'un fichier MDF directement
sans passer par l'interface web.

Usage:
    python test_mdf_import.py <chemin_fichier_mdf>
"""

import os
import sys
import django
import tempfile
import shutil

# Configuration de l'environnement Django
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "logViewer.settings")
django.setup()

from robot_logs.models import MDFFile
from robot_logs.mdf_parser import MDFParser
from django.core.files.base import ContentFile

def import_mdf_file(file_path):
    """Importe un fichier MDF dans la base de données Django"""
    
    if not os.path.exists(file_path):
        print(f"Erreur: Le fichier {file_path} n'existe pas.")
        return False
    
    file_size = os.path.getsize(file_path)
    if file_size == 0:
        print(f"Erreur: Le fichier {file_path} est vide.")
        return False
    
    print(f"Fichier trouvé: {file_path}")
    print(f"Taille: {file_size} octets")
    
    try:
        # Créer un objet MDFFile
        mdf_file = MDFFile(
            name=os.path.basename(file_path)
        )
        
        # Copier le fichier vers un emplacement temporaire
        tmp_path = None
        try:
            # Créer une copie temporaire du fichier
            tmp_file = tempfile.NamedTemporaryFile(delete=False)
            tmp_path = tmp_file.name
            tmp_file.close()
            
            shutil.copy2(file_path, tmp_path)
            
            # Vérifier que la copie est correcte
            if os.path.getsize(tmp_path) != file_size:
                print(f"Erreur: La copie du fichier a échoué. Taille originale: {file_size}, taille de la copie: {os.path.getsize(tmp_path)}")
                return False
            
            # Sauvegarder le fichier
            with open(file_path, 'rb') as f:
                file_content = f.read()
                mdf_file.file.save(
                    os.path.basename(file_path),
                    ContentFile(file_content),
                    save=True
                )
            
            print(f"Fichier MDF enregistré dans la base de données (ID: {mdf_file.id})")
            
            # Parser le fichier
            parser = MDFParser(tmp_path, mdf_file)
            try:
                # Essayer d'obtenir des informations sur le fichier
                if not parser.open():
                    print("Impossible d'ouvrir le fichier MDF avec le parser.")
                    return False
                
                channels = parser.get_channels()
                print(f"Nombre de canaux détectés: {len(channels)}")
                
                if channels:
                    print("5 premiers canaux:")
                    for channel in channels[:5]:
                        info = parser.get_channel_info(channel)
                        if info:
                            print(f"  - {info.get('name')}: {info.get('samples_count')} échantillons")
                
                # Traiter le fichier
                print("Traitement du fichier...")
                stats = parser.process_file()
                
                print("Importation réussie:")
                print(f"  - {stats.get('text_logs', 0)} logs textuels")
                print(f"  - {stats.get('curve_logs', 0)} courbes")
                print(f"  - {stats.get('laser_logs', 0)} scans laser")
                print(f"  - {stats.get('image_logs', 0)} images")
                
                return True
                
            except Exception as e:
                print(f"Erreur lors du traitement du fichier MDF: {e}")
                return False
            finally:
                parser.close()
        
        finally:
            # Nettoyer
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    except Exception as e:
        print(f"Erreur lors de l'importation: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_mdf_import.py <chemin_fichier_mdf>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    success = import_mdf_file(file_path)
    
    if success:
        print("Importation réussie!")
    else:
        print("Échec de l'importation.")
