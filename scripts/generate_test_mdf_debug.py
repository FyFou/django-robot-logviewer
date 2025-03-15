"""
Script de débogage pour générer un fichier MDF de test.

Ce script utilise un chemin absolu pour la sauvegarde et affiche des informations détaillées sur l'environnement.
"""

import os
import sys
import numpy as np
import logging
import tempfile
import platform
import shutil

# Configuration du logger pour plus de détails
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('mdf_generator_debug')

# Informations sur l'environnement
logger.info(f"Python version: {sys.version}")
logger.info(f"Système d'exploitation: {platform.platform()}")
logger.info(f"Répertoire de travail: {os.getcwd()}")
logger.info(f"Droits d'écriture dans le répertoire courant: {os.access(os.getcwd(), os.W_OK)}")

# Import de asammdf avec gestion d'erreur détaillée
try:
    from asammdf import MDF
    from asammdf import Signal
    
    # Vérifier la version d'asammdf
    from asammdf import __version__ as asammdf_version
    logger.info(f"Version d'asammdf: {asammdf_version}")
except ImportError as e:
    logger.error(f"Erreur d'importation: {e}")
    sys.exit(1)
except Exception as e:
    logger.error(f"Erreur inattendue lors de l'importation: {e}")
    sys.exit(1)

def main():
    # Utiliser un fichier temporaire pour éviter les problèmes de chemin/permissions
    temp_dir = tempfile.gettempdir()
    temp_file = os.path.join(temp_dir, 'test_mdf_file_debug.mdf')
    final_file = os.path.join(os.getcwd(), 'test_mdf_file_debug.mdf')
    
    logger.info(f"Fichier temporaire: {temp_file}")
    logger.info(f"Fichier final: {final_file}")
    
    # Vérifier les droits d'écriture
    logger.info(f"Droits d'écriture dans le répertoire temporaire: {os.access(temp_dir, os.W_OK)}")
    
    # Supprimer le fichier s'il existe déjà
    if os.path.exists(temp_file):
        try:
            os.remove(temp_file)
            logger.info(f"Fichier temporaire existant supprimé: {temp_file}")
        except Exception as e:
            logger.error(f"Impossible de supprimer le fichier temporaire existant: {e}")
    
    # Créer un objet MDF
    logger.info("Création d'un objet MDF...")
    mdf = MDF()
    
    # Créer des données simples
    logger.info("Création de données de test...")
    samples = 50  # Utiliser encore moins de points
    timestamps = np.arange(samples, dtype=np.float64)
    sinewave = np.sin(timestamps * 0.1) * 10
    
    # Créer et ajouter le signal
    logger.info("Création du signal de test...")
    try:
        signal = Signal(
            samples=sinewave,
            timestamps=timestamps,
            name='test_signal',
            unit='unit'
        )
        
        logger.info("Ajout du signal à l'objet MDF...")
        mdf.append([signal])
        logger.info("Signal ajouté avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout du signal: {e}")
        return 1
    
    # Sauvegarder dans le fichier temporaire
    logger.info(f"Sauvegarde dans le fichier temporaire: {temp_file}")
    try:
        mdf.save(temp_file, overwrite=True)
        logger.info("Fichier temporaire sauvegardé")
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du fichier temporaire: {e}")
        return 1
    
    # Vérifier que le fichier temporaire existe
    if os.path.exists(temp_file):
        file_size = os.path.getsize(temp_file)
        logger.info(f"Fichier temporaire créé, taille: {file_size} octets")
        
        # Tenter d'ouvrir le fichier pour vérification
        try:
            logger.info("Vérification du fichier temporaire...")
            verification_mdf = MDF(temp_file)
            channels = list(verification_mdf.channels_db.keys())
            logger.info(f"Nombre de canaux: {len(channels)}")
            verification_mdf.close()
            logger.info("Vérification réussie")
            
            # Copier vers le fichier final
            try:
                shutil.copy2(temp_file, final_file)
                logger.info(f"Fichier copié vers: {final_file}")
                logger.info("SUCCÈS: Fichier MDF créé et vérifié!")
                return 0
            except Exception as e:
                logger.error(f"Erreur lors de la copie du fichier: {e}")
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du fichier: {e}")
    else:
        logger.error(f"Le fichier temporaire n'a pas été créé: {temp_file}")
    
    return 1

if __name__ == "__main__":
    result = main()
    sys.exit(result)
