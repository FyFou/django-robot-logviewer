"""
Script pour générer un fichier MDF de test avec différents types de données
pour tester l'application LogViewer.

Ce script crée un fichier MDF contenant :
- Données textuelles (événements)
- Données de courbes (signaux sinusoïdaux, carrés, etc.)
- Données simulant un scan laser 2D
- Une image simple (simulée)

Utilisation :
    python generate_test_mdf.py [chemin_de_sortie]

Le fichier sera sauvegardé comme 'test_mdf_file.mdf' par défaut.
"""

import os
import sys
import numpy as np
import datetime
from asammdf import MDF
from asammdf.blocks.utils import MdfException
import argparse

def create_text_events():
    """Crée des événements textuels"""
    timestamps = np.linspace(0, 100, 20)
    
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
        "Test de performance démarré",
        "Test de performance complété",
        "Mise à jour des paramètres",
        "Données enregistrées",
        "Mode économie d'énergie activé",
        "Alerte: conditions environnementales anormales",
        "Chargement des configurations",
        "Déconnexion imminente",
        "Arrêt du système",
        "Redémarrage programmé",
        "Transmission des données terminée"
    ]
    
    # Convertir en tableau numpy de chaînes de caractères
    events_array = np.array(events, dtype='U100')
    
    return timestamps, events_array

def create_sine_wave():
    """Crée une onde sinusoïdale"""
    timestamps = np.linspace(0, 100, 1000)
    values = np.sin(timestamps * 0.2) * 10
    return timestamps, values

def create_square_wave():
    """Crée une onde carrée"""
    timestamps = np.linspace(0, 100, 1000)
    values = np.sign(np.sin(timestamps * 0.1)) * 5
    return timestamps, values

def create_triangle_wave():
    """Crée une onde triangulaire"""
    timestamps = np.linspace(0, 100, 1000)
    values = 2 * np.abs(2 * (timestamps * 0.05 - np.floor(timestamps * 0.05 + 0.5))) * 3
    return timestamps, values

def create_laser_scan():
    """Crée des données simulant un scan laser 2D"""
    # 360 points pour un scan complet (1 degré par point)
    angle_count = 360
    timestamps = np.array([50.0] * angle_count)  # timestamp fixe pour tous les points
    
    # Angles en radians (0 à 2π)
    angles = np.linspace(0, 2*np.pi, angle_count, endpoint=False)
    
    # Créer une forme circulaire avec des "obstacles" simulés
    base_distance = 5.0  # distance de base en mètres
    
    # Ajouter des variations pour simuler un environnement
    variations = np.zeros(angle_count)
    
    # Ajouter quelques "murs" et obstacles
    # Un "mur" de 30 degrés
    wall_start = 40
    wall_end = 70
    variations[wall_start:wall_end] = -2.0
    
    # Un obstacle rond
    obstacle_center = 180
    obstacle_width = 20
    for i in range(obstacle_center - obstacle_width // 2, obstacle_center + obstacle_width // 2):
        idx = i % angle_count
        dist = abs(i - obstacle_center)
        variations[idx] = -2.0 + 0.05 * dist
    
    # Un autre obstacle plus petit
    obstacle2_center = 270
    obstacle2_width = 10
    for i in range(obstacle2_center - obstacle2_width // 2, obstacle2_center + obstacle2_width // 2):
        idx = i % angle_count
        variations[idx] = -1.5
    
    # Ajouter un peu de bruit aléatoire
    noise = np.random.normal(0, 0.1, angle_count)
    
    # Calculer les distances finales
    distances = base_distance + variations + noise
    
    # Assurer que toutes les distances sont positives
    distances = np.maximum(distances, 0.1)
    
    return timestamps, distances

def create_image_data():
    """Crée une 'image' simple comme un tableau 2D"""
    # Simuler une petite image 50x50
    timestamp = np.array([75.0])  # Un seul timestamp pour l'image
    
    # Créer un motif simple (un cercle)
    x = np.linspace(-1, 1, 50)
    y = np.linspace(-1, 1, 50)
    X, Y = np.meshgrid(x, y)
    R = np.sqrt(X**2 + Y**2)
    
    # Créer un cercle avec un peu de dégradé
    image = (R < 0.7) * 255
    image = image.astype(np.uint8)
    
    # Convertir en tableau 1D pour stocker dans MDF
    image_1d = image.flatten()
    
    return timestamp, image_1d

def main():
    parser = argparse.ArgumentParser(description='Générer un fichier MDF de test')
    parser.add_argument('output_path', nargs='?', default='.', help='Chemin de sortie pour le fichier MDF')
    args = parser.parse_args()
    
    output_dir = args.output_path
    output_file = os.path.join(output_dir, 'test_mdf_file.mdf')
    
    # Créer un nouveau fichier MDF (version 4.10)
    mdf = MDF(version='4.10')
    
    print("Génération des données...")
    
    # Ajouter des événements textuels
    print("- Ajout des événements textuels")
    text_timestamps, text_events = create_text_events()
    mdf.append(text_timestamps, text_events, 'événements_texte', comment="Événements système")
    
    # Ajouter des courbes
    print("- Ajout des données de courbes")
    sine_timestamps, sine_values = create_sine_wave()
    mdf.append(sine_timestamps, sine_values, 'onde_sinus', comment="Onde sinusoïdale", unit="volts")
    
    square_timestamps, square_values = create_square_wave()
    mdf.append(square_timestamps, square_values, 'onde_carrée', comment="Onde carrée", unit="ampères")
    
    triangle_timestamps, triangle_values = create_triangle_wave()
    mdf.append(triangle_timestamps, triangle_values, 'onde_triangle', comment="Onde triangulaire", unit="degrés")
    
    # Ajouter un scan laser 2D
    print("- Ajout des données laser 2D")
    laser_timestamps, laser_distances = create_laser_scan()
    mdf.append(laser_timestamps, laser_distances, 'scan_laser', comment="Scan laser 2D", unit="mètres")
    
    # Ajouter des données d'image
    print("- Ajout des données d'image")
    image_timestamps, image_data = create_image_data()
    mdf.append(image_timestamps, image_data, 'image_simple', comment="Image test 50x50")
    
    # Sauvegarder le fichier
    print(f"Sauvegarde du fichier MDF dans {output_file}...")
    try:
        mdf.save(output_file, overwrite=True)
        print(f"Fichier MDF créé avec succès: {output_file}")
    except MdfException as e:
        print(f"Erreur lors de la sauvegarde du fichier MDF: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
