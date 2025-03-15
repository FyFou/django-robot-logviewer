"""
Script simplifié pour générer un fichier MDF de test avec un focus sur la fiabilité.

Ce script crée un fichier MDF contenant :
- Données textuelles (événements)
- Quelques courbes simples

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
    # Importer Signal directement pour éviter les problèmes d'import conditionnel
    try:
        from asammdf.blocks.mdf_v4 import Signal
    except ImportError:
        logger.warning("Impossible d'importer Signal depuis asammdf.blocks.mdf_v4")
        try:
            from asammdf import Signal
        except ImportError:
            logger.warning("Impossible d'importer Signal depuis asammdf")
    
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

def create_text_events():
    """Crée des événements textuels simples"""
    # Utiliser moins d'événements (10 seulement)
    timestamps = np.linspace(0, 100, 10)
    
    events = [
        "Démarrage du système",
        "Initialisation des capteurs",
        "Connexion établie",
        "Récupération des données",
        "Analyse des résultats",
        "Erreur détectée dans le module X",
        "Recalibration des capteurs",
        "Avertissement: niveau batterie faible",
        "Traitement terminé",
        "Arrêt du système"
    ]
    
    # Convertir en tableau numpy de chaînes de caractères
    events_array = np.array(events, dtype='U100')
    
    return timestamps, events_array

def create_sine_wave():
    """Crée une onde sinusoïdale simple"""
    # Utiliser moins d'échantillons (100 au lieu de 1000)
    timestamps = np.linspace(0, 100, 100)
    values = np.sin(timestamps * 0.2) * 10
    return timestamps, values

def create_square_wave():
    """Crée une onde carrée simple"""
    # Utiliser moins d'échantillons (100 au lieu de 1000)
    timestamps = np.linspace(0, 100, 100)
    values = np.sign(np.sin(timestamps * 0.1)) * 5
    return timestamps, values

def append_signal(mdf, timestamps, values, name, unit=None):
    """
    Méthode simplifiée et robuste pour ajouter un signal au fichier MDF
    avec plus de débogage
    """
    logger.info(f"Ajout du signal '{name}' au fichier MDF")
    logger.info(f"  - Timestamps: {len(timestamps)} valeurs, type={timestamps.dtype}")
    logger.info(f"  - Valeurs: {len(values)} valeurs, type={values.dtype}")
    
    success = False
    
    # Méthode 1: Utiliser directement Signal si disponible
    if 'Signal' in globals():
        try:
            logger.info("  - Tentative avec Signal()")
            signal = Signal(
                samples=values,
                timestamps=timestamps,
                name=name,
                unit=unit
            )
            signals = [signal]
            mdf.append(signals)
            logger.info("  - Signal ajouté avec succès (méthode 1)")
            success = True
        except Exception as e:
            logger.error(f"  - Erreur avec Signal(): {str(e)}")
    
    # Méthode 2: Utiliser append directement si Méthode 1 a échoué
    if not success:
        try:
            logger.info("  - Tentative avec mdf.append()")
            if unit:
                mdf.append(timestamps, values, name, unit=unit)
            else:
                mdf.append(timestamps, values, name)
            logger.info("  - Signal ajouté avec succès (méthode 2)")
            success = True
        except Exception as e:
            logger.error(f"  - Erreur avec mdf.append(): {str(e)}")
    
    # Vérifier si le signal a bien été ajouté
    if not success:
        logger.error(f"  - ÉCHEC: Impossible d'ajouter le signal '{name}'")
        return False
    
    return True

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
    output_file = os.path.join(output_dir, 'test_mdf_file_simple.mdf')
    
    # Créer un nouveau fichier MDF 
    # Essayer d'abord avec version='4.10'
    mdf = None
    try:
        logger.info("Création du fichier MDF avec version='4.10'")
        mdf = MDF(version='4.10')
    except Exception as e:
        logger.warning(f"Erreur lors de la création du fichier MDF avec version='4.10': {e}")
        
        # Essayer avec version='4.00'
        try:
            logger.info("Tentative avec version='4.00'")
            mdf = MDF(version='4.00')
        except Exception as e:
            logger.warning(f"Erreur lors de la création du fichier MDF avec version='4.00': {e}")
            
            # Essayer sans spécifier la version
            try:
                logger.info("Tentative sans spécifier la version")
                mdf = MDF()
            except Exception as e:
                logger.error(f"Erreur lors de la création du fichier MDF sans version: {e}")
                return 1
    
    if not mdf:
        logger.error("Impossible de créer un objet MDF")
        return 1
        
    logger.info("Génération des données...")
    
    signals_added = 0
    
    # Ajouter des événements textuels
    logger.info("- Ajout des événements textuels")
    text_timestamps, text_events = create_text_events()
    if append_signal(mdf, text_timestamps, text_events, 'evenements_texte'):
        signals_added += 1
    
    # Ajouter une onde sinusoïdale
    logger.info("- Ajout d'une onde sinusoïdale")
    sine_timestamps, sine_values = create_sine_wave()
    if append_signal(mdf, sine_timestamps, sine_values, 'onde_sinus', unit='m/s'):
        signals_added += 1
    
    # Ajouter une onde carrée
    logger.info("- Ajout d'une onde carrée")
    square_timestamps, square_values = create_square_wave()
    if append_signal(mdf, square_timestamps, square_values, 'onde_carree', unit='V'):
        signals_added += 1
    
    # Vérifier si des signaux ont été ajoutés
    if signals_added == 0:
        logger.error("Aucun signal n'a pu être ajouté au fichier MDF")
        return 1
    
    logger.info(f"{signals_added} signaux ajoutés avec succès")
    
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
