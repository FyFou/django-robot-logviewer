"""
Script minimal pour générer un fichier MDF valide.

Ce script utilise les paramètres les plus basiques possibles avec une version 3.30 du format MDF
qui est généralement mieux supportée par les anciennes versions d'asammdf.
"""

import os
import sys
import numpy as np
import logging
import tempfile

# Configuration du logger
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('mdf_minimal')

# Import
try:
    from asammdf import MDF, Signal
    logger.info(f"asammdf importé avec succès")
except ImportError as e:
    logger.error(f"Erreur d'importation: {e}")
    sys.exit(1)

def main():
    # Créer un fichier dans le dossier courant
    output_file = 'test_mdf_minimal.mdf'
    
    logger.info(f"Création d'un fichier MDF version 3.30 (ancienne version compatible)...")
    
    # Créer un MDF version 3.30 (beaucoup plus simple et plus compatible)
    try:
        mdf = MDF(version='3.30')
        logger.info(f"Objet MDF créé avec version 3.30")
    except Exception as e:
        logger.error(f"Erreur lors de la création de l'objet MDF: {e}")
        return 1
    
    # Créer un signal extrêmement simple
    try:
        # Données les plus simples possibles
        timestamps = np.array([0.0, 1.0, 2.0, 3.0, 4.0], dtype=np.float64)
        values = np.array([0.0, 1.0, 0.0, 1.0, 0.0], dtype=np.float64)
        
        logger.info(f"Données créées: {len(timestamps)} points")
        
        # Créer le signal
        signal = Signal(
            samples=values,
            timestamps=timestamps,
            name='test_signal'
        )
        
        logger.info(f"Signal créé")
        
        # Ajouter le signal
        mdf.append([signal])
        logger.info(f"Signal ajouté à l'objet MDF")
    except Exception as e:
        logger.error(f"Erreur lors de la création ou de l'ajout du signal: {e}")
        return 1
    
    # Sauvegarder le fichier avec vérification directe du fichier système
    try:
        # Supprimer le fichier s'il existe déjà
        if os.path.exists(output_file):
            os.remove(output_file)
            logger.info(f"Ancien fichier supprimé")
        
        # Sauvegarder
        logger.info(f"Sauvegarde du fichier MDF dans {output_file}...")
        mdf.save(output_file, overwrite=True)
        
        # Vérifier immédiatement si le fichier existe
        if os.path.exists(output_file):
            size = os.path.getsize(output_file)
            logger.info(f"Fichier créé avec succès! Taille: {size} octets")
            
            # Tenter de le relire pour vérification
            try:
                logger.info(f"Tentative d'ouverture du fichier pour vérification...")
                verification_mdf = MDF(output_file)
                channels = list(verification_mdf.channels_db.keys())
                logger.info(f"Fichier ouvert avec succès, {len(channels)} canaux trouvés")
                for i, channel in enumerate(channels):
                    logger.info(f"Canal {i+1}: {channel}")
                verification_mdf.close()
                
                logger.info("SUCCÈS: Fichier MDF généré et vérifié!")
                return 0
            except Exception as e:
                logger.error(f"Erreur lors de la vérification du fichier: {e}")
        else:
            logger.error(f"Échec: Le fichier n'a pas été créé après save()")
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du fichier: {e}")
    
    return 1

if __name__ == "__main__":
    result = main()
    sys.exit(result)
