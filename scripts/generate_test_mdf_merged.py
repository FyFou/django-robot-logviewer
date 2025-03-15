"""
Script pour générer un fichier MDF avec tous les signaux partageant un même canal de temps.

Ce script utilise l'approche "maître-esclave" d'asammdf pour que tous les signaux
partagent un même canal de temps, évitant ainsi les erreurs de canaux dupliqués.
"""

import os
import sys
import numpy as np
import logging

# Configuration du logger
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('mdf_merged')

# Import
try:
    from asammdf import MDF, Signal
    logger.info(f"asammdf importé avec succès")
except ImportError as e:
    logger.error(f"Erreur d'importation: {e}")
    sys.exit(1)

def main():
    # Créer un fichier dans le dossier courant
    output_file = 'test_mdf_merged.mdf'
    
    logger.info(f"Création d'un fichier MDF version 3.30...")
    
    # Créer un MDF version 3.30
    try:
        mdf = MDF(version='3.30')
        logger.info(f"Objet MDF créé avec version 3.30")
    except Exception as e:
        logger.error(f"Erreur lors de la création de l'objet MDF: {e}")
        return 1
    
    # Créer une grille de temps commune pour tous les signaux
    # Utiliser un nombre réduit de points pour plus de fiabilité
    sample_count = 100
    common_timestamps = np.linspace(0, 10, sample_count, dtype=np.float64)
    
    # Créer des signaux avec les mêmes timestamps
    # Signal 1: Onde sinusoïdale
    sine_values = np.sin(common_timestamps) * 5.0
    
    # Signal 2: Onde carrée
    square_values = np.sign(np.sin(common_timestamps * 2)) * 3.0
    
    # Signal 3: Onde triangulaire
    triangle_values = np.abs((common_timestamps * 0.4) % 2 - 1) * 4.0
    
    # Créer les signaux avec un canal de temps commun
    try:
        # Créer le premier signal qui sera maître pour le temps
        sine_sig = Signal(
            samples=sine_values,
            timestamps=common_timestamps,
            name='sine_signal'
        )
        
        # Créer les autres signaux qui utiliseront le même temps
        square_sig = Signal(
            samples=square_values,
            timestamps=common_timestamps,
            name='square_signal'
        )
        
        triangle_sig = Signal(
            samples=triangle_values,
            timestamps=common_timestamps,
            name='triangle_signal'
        )
        
        # Ajouter tous les signaux en une seule fois
        # Cela devrait les regrouper dans un seul groupe de données
        mdf.append([sine_sig, square_sig, triangle_sig])
        
        logger.info(f"Tous les signaux ajoutés avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout des signaux: {e}")
        return 1
    
    # Sauvegarder le fichier
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
            
            # Tenter de le relire pour vérification et afficher tous les canaux
            try:
                logger.info(f"Tentative d'ouverture du fichier pour vérification...")
                verification_mdf = MDF(output_file)
                
                # Lister tous les canaux avec leur groupe
                channels_db = verification_mdf.channels_db
                logger.info(f"Nombre total de canaux: {len(channels_db)}")
                
                # Afficher la structure des canaux pour débogage
                for i, (channel_name, occurrences) in enumerate(channels_db.items()):
                    logger.info(f"Canal {i+1}: {channel_name} - {len(occurrences)} occurrences")
                    for j, (group, index) in enumerate(occurrences):
                        logger.info(f"  - Occurrence {j+1}: groupe {group}, index {index}")
                
                # Essayer d'accéder à chaque signal par son nom (uniquement le premier si plusieurs occurrences)
                signals = ['sine_signal', 'square_signal', 'triangle_signal']
                for signal_name in signals:
                    if signal_name in channels_db:
                        try:
                            signal = verification_mdf.get(signal_name)
                            logger.info(f"Signal '{signal_name}' lu avec succès: {len(signal.samples)} points")
                        except Exception as e:
                            logger.error(f"Erreur lors de la lecture du signal '{signal_name}': {e}")
                
                verification_mdf.close()
                logger.info("Vérification réussie!")
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
