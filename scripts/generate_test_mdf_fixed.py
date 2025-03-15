"""
Script corrigé pour générer un fichier MDF de test.

Ce script génère un fichier MDF contenant uniquement des données numériques,
en évitant les types problématiques (comme les chaînes de caractères).

Conçu pour fonctionner de manière fiable avec différentes versions d'asammdf.
"""

import os
import sys
import numpy as np
import datetime
import argparse
import logging

# Configuration du logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('mdf_generator')

try:
    from asammdf import MDF
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

def create_sine_wave(freq=0.2, amplitude=10.0, offset=0.0, samples=1000):
    """Crée une onde sinusoïdale simple"""
    timestamps = np.linspace(0, 100, samples)
    values = np.sin(timestamps * freq) * amplitude + offset
    return timestamps, values

def create_square_wave(freq=0.1, amplitude=5.0, offset=0.0, samples=1000):
    """Crée une onde carrée simple"""
    timestamps = np.linspace(0, 100, samples)
    values = np.sign(np.sin(timestamps * freq)) * amplitude + offset
    return timestamps, values

def create_triangle_wave(freq=0.05, amplitude=3.0, offset=0.0, samples=1000):
    """Crée une onde triangulaire simple"""
    timestamps = np.linspace(0, 100, samples)
    values = 2 * np.abs(2 * (timestamps * freq - np.floor(timestamps * freq + 0.5))) * amplitude + offset
    return timestamps, values

def create_sawtooth_wave(freq=0.08, amplitude=4.0, offset=0.0, samples=1000):
    """Crée une onde en dents de scie"""
    timestamps = np.linspace(0, 100, samples)
    values = (2 * (timestamps * freq - np.floor(0.5 + timestamps * freq))) * amplitude + offset
    return timestamps, values

def create_laser_scan(center=50.0, angle_count=360, base_distance=5.0):
    """Crée des données simulant un scan laser 2D"""
    timestamps = np.linspace(center, center + 0.1, angle_count)  # Timestamps légèrement différents
    
    # Simuler des distances (uniquement des valeurs numériques)
    distances = np.ones(angle_count) * base_distance
    
    # Ajouter des "obstacles"
    for i in range(angle_count // 6, angle_count // 3):
        distances[i] = base_distance * 0.5
    
    for i in range(angle_count // 2, 2 * angle_count // 3):
        distances[i] = base_distance * 0.7
    
    # Ajouter un peu de bruit
    distances += np.random.normal(0, 0.2, angle_count)
    
    # Assurer que toutes les distances sont positives
    distances = np.maximum(distances, 0.1)
    
    return timestamps, distances

def verify_mdf_file(file_path):
    """Vérifie que le fichier MDF contient des données"""
    logger.info(f"Vérification du fichier MDF: {file_path}")
    
    try:
        # Vérifier que le fichier existe et a une taille non nulle
        if not os.path.exists(file_path):
            logger.error(f"  - Le fichier n'existe pas")
            return False
        
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            logger.error(f"  - Le fichier est vide (0 octets)")
            return False
        
        logger.info(f"  - Taille du fichier: {file_size} octets")
        
        # Essayer d'ouvrir le fichier avec asammdf
        try:
            mdf = MDF(file_path)
            channels = list(mdf.channels_db.keys())
            logger.info(f"  - Nombre de canaux: {len(channels)}")
            
            if len(channels) == 0:
                logger.warning("  - Le fichier ne contient aucun canal")
                return False
            
            # Afficher les premiers canaux
            for i, channel in enumerate(channels[:5]):
                logger.info(f"  - Canal {i+1}: {channel}")
            
            return True
        except Exception as e:
            logger.error(f"  - Erreur lors de l'ouverture du fichier: {str(e)}")
            return False
            
    except Exception as e:
        logger.error(f"  - Erreur lors de la vérification du fichier: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Générer un fichier MDF de test simplifié')
    parser.add_argument('output_path', nargs='?', default='.', help='Chemin de sortie pour le fichier MDF')
    parser.add_argument('--verbose', '-v', action='store_true', help='Afficher plus d\'informations de débogage')
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    output_dir = args.output_path
    output_file = os.path.join(output_dir, 'test_mdf_file_fixed.mdf')
    
    # Tenter de créer un MDF avec différentes versions pour maximiser la compatibilité
    try:
        logger.info("Création du fichier MDF avec version par défaut")
        mdf = MDF()
    except Exception as e:
        logger.error(f"Erreur lors de la création du fichier MDF: {e}")
        return 1
        
    logger.info("Génération des données...")
    
    # Ajouter une onde sinusoïdale
    try:
        logger.info("- Ajout d'une onde sinusoïdale")
        sine_timestamps, sine_values = create_sine_wave()
        mdf.append(sine_timestamps, sine_values, 'onde_sinus')
        logger.info("  - Onde sinusoïdale ajoutée")
    except Exception as e:
        logger.error(f"  - Erreur: {e}")
    
    # Ajouter une onde carrée
    try:
        logger.info("- Ajout d'une onde carrée")
        square_timestamps, square_values = create_square_wave()
        mdf.append(square_timestamps, square_values, 'onde_carree')
        logger.info("  - Onde carrée ajoutée")
    except Exception as e:
        logger.error(f"  - Erreur: {e}")
    
    # Ajouter une onde triangulaire
    try:
        logger.info("- Ajout d'une onde triangulaire")
        triangle_timestamps, triangle_values = create_triangle_wave()
        mdf.append(triangle_timestamps, triangle_values, 'onde_triangle')
        logger.info("  - Onde triangulaire ajoutée")
    except Exception as e:
        logger.error(f"  - Erreur: {e}")
    
    # Ajouter une onde en dents de scie
    try:
        logger.info("- Ajout d'une onde en dents de scie")
        sawtooth_timestamps, sawtooth_values = create_sawtooth_wave()
        mdf.append(sawtooth_timestamps, sawtooth_values, 'onde_dents_de_scie')
        logger.info("  - Onde en dents de scie ajoutée")
    except Exception as e:
        logger.error(f"  - Erreur: {e}")
    
    # Ajouter un scan laser
    try:
        logger.info("- Ajout d'un scan laser")
        laser_timestamps, laser_values = create_laser_scan()
        mdf.append(laser_timestamps, laser_values, 'scan_laser')
        logger.info("  - Scan laser ajouté")
    except Exception as e:
        logger.error(f"  - Erreur: {e}")
    
    # Sauvegarder le fichier
    logger.info(f"Sauvegarde du fichier MDF dans {output_file}...")
    try:
        mdf.save(output_file, overwrite=True)
        logger.info(f"Fichier MDF sauvegardé: {output_file}")
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du fichier MDF: {e}")
        return 1
    
    # Vérifier le fichier
    if verify_mdf_file(output_file):
        logger.info("Vérification du fichier MDF réussie!")
    else:
        logger.error("Le fichier MDF généré semble incorrect ou incomplet")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
