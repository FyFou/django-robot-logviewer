"""
Script basique pour générer un fichier MDF de test.

Ce script utilise l'approche la plus simple possible pour créer un fichier MDF
avec quelques signaux numériques. Il est conçu pour fonctionner même avec
des installations problématiques d'asammdf.
"""

import os
import sys
import numpy as np
import logging

# Configuration du logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('mdf_generator')

# Import de asammdf et vérification de la classe Signal
try:
    from asammdf import MDF
    
    # Tenter d'importer Signal directement d'asammdf (méthode recommandée)
    try:
        from asammdf import Signal
        logger.info("Signal importé depuis asammdf")
    except ImportError:
        # Si cela échoue, essayer d'importer depuis les sous-modules
        try:
            from asammdf.blocks.mdf_v4 import Signal
            logger.info("Signal importé depuis asammdf.blocks.mdf_v4")
        except ImportError:
            logger.error("Impossible d'importer la classe Signal d'asammdf")
            sys.exit(1)
    
    # Vérifier la version d'asammdf
    try:
        from asammdf import __version__ as asammdf_version
        logger.info(f"Version d'asammdf: {asammdf_version}")
    except ImportError:
        logger.warning("Impossible de déterminer la version d'asammdf")
except ImportError:
    logger.error("La bibliothèque asammdf n'est pas installée.")
    logger.error("Installez-la avec: pip install asammdf numpy")
    sys.exit(1)

def main():
    output_file = 'test_mdf_file_basic.mdf'
    
    logger.info("Création d'un fichier MDF...")
    
    # Utiliser la version par défaut
    mdf = MDF()
    
    # Créer des données simples pour un signal
    # Utiliser moins de points pour plus de fiabilité
    samples = 100
    
    # Signal 1: Onde sinusoïdale
    logger.info("Création du signal 'onde_sinus'...")
    timestamps1 = np.arange(samples, dtype=np.float64)
    sinewave = np.sin(timestamps1 * 0.1) * 10
    
    try:
        # Créer un objet Signal avec les données
        signal1 = Signal(
            samples=sinewave,
            timestamps=timestamps1,
            name='onde_sinus',
            unit='m/s'
        )
        
        # Ajouter le signal au MDF
        mdf.append([signal1])
        logger.info("Signal 'onde_sinus' ajouté")
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout du signal 'onde_sinus': {e}")
    
    # Signal 2: Onde carrée
    logger.info("Création du signal 'onde_carree'...")
    timestamps2 = np.arange(samples, dtype=np.float64)
    squarewave = np.sign(np.sin(timestamps2 * 0.05)) * 5
    
    try:
        # Créer un objet Signal avec les données
        signal2 = Signal(
            samples=squarewave,
            timestamps=timestamps2,
            name='onde_carree',
            unit='V'
        )
        
        # Ajouter le signal au MDF
        mdf.append([signal2])
        logger.info("Signal 'onde_carree' ajouté")
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout du signal 'onde_carree': {e}")
    
    # Sauvegarder le fichier
    logger.info(f"Sauvegarde du fichier MDF dans {output_file}...")
    try:
        mdf.save(output_file, overwrite=True)
        logger.info(f"Fichier MDF sauvegardé avec succès: {output_file}")
        
        # Vérifier que le fichier existe et a une taille non nulle
        if os.path.exists(output_file):
            size = os.path.getsize(output_file)
            logger.info(f"Taille du fichier: {size} octets")
            if size > 0:
                logger.info("Génération réussie!")
            else:
                logger.error("Le fichier a été créé mais il est vide!")
        else:
            logger.error("Le fichier n'a pas été créé!")
            
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du fichier MDF: {e}")
    
    # Tenter d'ouvrir le fichier pour vérification
    if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
        try:
            logger.info("Ouverture du fichier pour vérification...")
            verification_mdf = MDF(output_file)
            channels = list(verification_mdf.channels_db.keys())
            logger.info(f"Nombre de canaux trouvés: {len(channels)}")
            for i, channel in enumerate(channels):
                logger.info(f"Canal {i+1}: {channel}")
                
            verification_mdf.close()
            logger.info("Vérification réussie!")
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du fichier: {e}")

if __name__ == "__main__":
    main()
