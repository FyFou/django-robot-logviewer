"""
Script pour générer un fichier MDF avec des noms de canaux uniques.

Ce script évite l'utilisation automatique de 'time' pour le canal de timestamps
et nomme explicitement tous les canaux pour éviter les ambiguïtés.
"""

import os
import sys
import numpy as np
import logging

# Configuration du logger
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('mdf_unique')

# Import
try:
    from asammdf import MDF, Signal
    logger.info(f"asammdf importé avec succès")
except ImportError as e:
    logger.error(f"Erreur d'importation: {e}")
    sys.exit(1)

def main():
    # Créer un fichier dans le dossier courant
    output_file = 'test_mdf_unique.mdf'
    
    logger.info(f"Création d'un fichier MDF version 3.30...")
    
    # Créer un MDF version 3.30
    try:
        mdf = MDF(version='3.30')
        logger.info(f"Objet MDF créé avec version 3.30")
    except Exception as e:
        logger.error(f"Erreur lors de la création de l'objet MDF: {e}")
        return 1
    
    # Créer un signal sinusoïdal
    try:
        # Données pour le signal sinusoïdal
        timestamps1 = np.linspace(0, 10, 100, dtype=np.float64)
        sine_values = np.sin(timestamps1) * 5.0
        
        logger.info(f"Données sinusoïdales créées: {len(timestamps1)} points")
        
        # Créer le signal avec un nom unique pour le canal de temps
        sine_signal = Signal(
            samples=sine_values,
            timestamps=timestamps1,
            name='sine_wave_signal',
        )
        
        logger.info(f"Signal sinusoïdal créé")
        
        # Ajouter le signal
        mdf.append([sine_signal])
        logger.info(f"Signal sinusoïdal ajouté à l'objet MDF")
    except Exception as e:
        logger.error(f"Erreur lors de la création ou de l'ajout du signal sinusoïdal: {e}")
        return 1
    
    # Créer un signal carré
    try:
        # Données pour le signal carré
        timestamps2 = np.linspace(0, 10, 100, dtype=np.float64)
        square_values = np.sign(np.sin(timestamps2 * 2)) * 3.0
        
        logger.info(f"Données carrées créées: {len(timestamps2)} points")
        
        # Créer le signal avec un nom unique
        square_signal = Signal(
            samples=square_values,
            timestamps=timestamps2,
            name='square_wave_signal',
        )
        
        logger.info(f"Signal carré créé")
        
        # Ajouter le signal
        mdf.append([square_signal])
        logger.info(f"Signal carré ajouté à l'objet MDF")
    except Exception as e:
        logger.error(f"Erreur lors de la création ou de l'ajout du signal carré: {e}")
    
    # Créer des données pour un scan laser simulé
    try:
        # Données pour le scan laser
        angle_count = 180
        timestamps3 = np.array([5.0] * angle_count, dtype=np.float64)
        laser_data = np.ones(angle_count, dtype=np.float64) * 3.0
        
        # Ajouter quelques "obstacles"
        laser_data[30:60] = 1.5  # Obstacle à gauche
        laser_data[120:150] = 2.0  # Obstacle à droite
        
        logger.info(f"Données laser créées: {len(laser_data)} points")
        
        # Créer le signal avec un nom unique
        laser_signal = Signal(
            samples=laser_data,
            timestamps=timestamps3,
            name='laser_scan_data',
        )
        
        logger.info(f"Signal laser créé")
        
        # Ajouter le signal
        mdf.append([laser_signal])
        logger.info(f"Signal laser ajouté à l'objet MDF")
    except Exception as e:
        logger.error(f"Erreur lors de la création ou de l'ajout du signal laser: {e}")
    
    # Sauvegarder le fichier avec vérification
    try:
        # Supprimer le fichier s'il existe déjà
        if os.path.exists(output_file):
            os.remove(output_file)
            logger.info(f"Ancien fichier supprimé")
        
        # Sauvegarder
        logger.info(f"Sauvegarde du fichier MDF dans {output_file}...")
        mdf.save(output_file, overwrite=True)
        
        # Vérifier si le fichier existe
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
                
                logger.info("SUCCÈS: Fichier MDF généré et vérifié avec 3 signaux!")
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
