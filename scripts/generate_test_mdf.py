"""
Script pour générer un fichier MDF de test avec différents types de données
pour tester l'application LogViewer.

Ce script crée un fichier MDF contenant :
- Données textuelles (événements)
- Au moins 4 courbes (signaux sinusoïdaux, carrés, etc.)
- Au moins 3 scans laser 2D
- Au moins 5 images simples

Utilisation :
    python generate_test_mdf.py [chemin_de_sortie]

Le fichier sera sauvegardé comme 'test_mdf_file.mdf' par défaut.
"""

import os
import sys
import numpy as np
import datetime
import argparse
from PIL import Image, ImageDraw
import io

try:
    from asammdf import MDF
    from asammdf.blocks.utils import MdfException
except ImportError:
    print("Erreur: La bibliothèque asammdf n'est pas installée.")
    print("Installez-la avec: pip install asammdf numpy pillow")
    sys.exit(1)

def create_text_events():
    """Crée des événements textuels"""
    timestamps = np.linspace(0, 100, 50)  # Augmenté à 50 événements
    
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
        "Transmission des données terminée",
        "Détection d'obstacle avant",
        "Évitement d'obstacle activé",
        "Navigation modifiée",
        "Capteur de proximité activé",
        "Point de passage atteint",
        "Rotation du robot initiée",
        "Changement de vitesse",
        "Position GPS mise à jour",
        "Communication établie avec robot #2",
        "Synchronisation des données",
        "Validation de la route",
        "Prise de décision algorithmique",
        "Mesure de distance effectuée",
        "Réception de commande externe",
        "Ajustement de trajectoire",
        "Détection de marqueur visuel",
        "Lecture de code QR réussie",
        "Base de données mise à jour",
        "Recherche de point de charge",
        "Changement d'état interne",
        "Surveillance de température activée",
        "Paramètres environnementaux enregistrés",
        "Détection de mouvement",
        "Configuration des actionneurs terminée",
        "Message reçu de l'opérateur",
        "Vérification de sécurité réussie",
        "Calibration d'urgence",
        "Retour à la position d'origine",
        "Fin de mission"
    ]
    
    # S'assurer que nous avons suffisamment d'événements pour tous les timestamps
    if len(events) < len(timestamps):
        # Répéter les événements si nécessaire
        events = (events * (len(timestamps) // len(events) + 1))[:len(timestamps)]
    
    # Convertir en tableau numpy de chaînes de caractères
    events_array = np.array(events, dtype='U100')
    
    return timestamps, events_array

def create_error_log_events():
    """Crée des événements de journal d'erreur"""
    timestamps = np.linspace(10, 90, 15)  # 15 erreurs réparties
    
    errors = [
        "ERREUR: Échec de connexion au serveur",
        "ALERTE: Anomalie détectée dans le moteur gauche",
        "ERREUR: Capteur de température hors limites",
        "ALERTE: Tension d'alimentation faible",
        "CRITIQUE: Perte de communication avec le système central",
        "ERREUR: Surintensité dans le circuit de contrôle",
        "ALERTE: Obstruction détectée, arrêt d'urgence",
        "ERREUR: Échec de reconnaissance d'environnement",
        "CRITIQUE: Surchauffe du processeur principal",
        "ERREUR: Échec de la mise à jour du firmware",
        "ALERTE: Chute de performance des capteurs laser",
        "ERREUR: Mémoire insuffisante pour le traitement d'image",
        "CRITIQUE: Défaillance gyroscopique, perte d'orientation",
        "ERREUR: Échec de la routine d'auto-diagnostic",
        "ALERTE: Anomalie dans le comportement de navigation"
    ]
    
    # Convertir en tableau numpy de chaînes de caractères
    errors_array = np.array(errors, dtype='U100')
    
    return timestamps, errors_array

def create_debug_log_events():
    """Crée des événements de journal de débogage"""
    timestamps = np.linspace(5, 95, 20)
    
    debug_messages = [
        "DEBUG: Chargement module de navigation...",
        "DEBUG: Initialisation des paramètres de calibration",
        "DEBUG: Vérification des capteurs: OK",
        "DEBUG: Chargement des cartes locales",
        "DEBUG: Connexion établie [192.168.1.15:8080]",
        "DEBUG: Vérification de l'intégrité des données",
        "DEBUG: Calcul de l'itinéraire optimal",
        "DEBUG: Buffer circulaire initialisé",
        "DEBUG: Traitement des données laser à 40Hz",
        "DEBUG: Analyse des données d'image en cours",
        "DEBUG: Mise à jour de la matrice d'état",
        "DEBUG: Application du filtre de Kalman",
        "DEBUG: Mise à jour de la position relative",
        "DEBUG: Planification de trajectoire terminée",
        "DEBUG: Délai de traitement: 12ms",
        "DEBUG: Envoi des commandes aux moteurs",
        "DEBUG: Réception de 128 trames de données",
        "DEBUG: Enregistrement des métriques de performance",
        "DEBUG: Vérification des points de passage",
        "DEBUG: Rotation du lidar terminée"
    ]
    
    # Convertir en tableau numpy de chaînes de caractères
    debug_array = np.array(debug_messages, dtype='U100')
    
    return timestamps, debug_array

def create_sine_wave(freq=0.2, amplitude=10.0, offset=0.0, samples=1000):
    """Crée une onde sinusoïdale personnalisable"""
    timestamps = np.linspace(0, 100, samples)
    values = np.sin(timestamps * freq) * amplitude + offset
    return timestamps, values

def create_square_wave(freq=0.1, amplitude=5.0, offset=0.0, samples=1000):
    """Crée une onde carrée personnalisable"""
    timestamps = np.linspace(0, 100, samples)
    values = np.sign(np.sin(timestamps * freq)) * amplitude + offset
    return timestamps, values

def create_triangle_wave(freq=0.05, amplitude=3.0, offset=0.0, samples=1000):
    """Crée une onde triangulaire personnalisable"""
    timestamps = np.linspace(0, 100, samples)
    values = 2 * np.abs(2 * (timestamps * freq - np.floor(timestamps * freq + 0.5))) * amplitude + offset
    return timestamps, values

def create_sawtooth_wave(freq=0.05, amplitude=4.0, offset=0.0, samples=1000):
    """Crée une onde en dents de scie"""
    timestamps = np.linspace(0, 100, samples)
    values = (2 * (timestamps * freq - np.floor(0.5 + timestamps * freq))) * amplitude + offset
    return timestamps, values

def create_exponential_curve(rate=0.03, amplitude=5.0, offset=0.0, samples=1000):
    """Crée une courbe exponentielle"""
    timestamps = np.linspace(0, 100, samples)
    values = amplitude * np.exp(rate * timestamps) + offset
    # Limiter les valeurs pour éviter des nombres trop grands
    values = np.clip(values, 0, amplitude * 20)
    return timestamps, values

def create_random_walk(step_size=0.1, amplitude=10.0, offset=0.0, samples=1000):
    """Crée une marche aléatoire"""
    timestamps = np.linspace(0, 100, samples)
    steps = np.random.normal(0, step_size, samples)
    # Intégrer les étapes pour obtenir la marche aléatoire
    values = np.cumsum(steps) * amplitude + offset
    return timestamps, values

def create_laser_scan(center=50.0, angle_count=360, base_distance=5.0, variations_scale=1.0):
    """Crée des données simulant un scan laser 2D"""
    timestamps = np.array([center] * angle_count)  # timestamp fixe pour tous les points
    
    # Angles en radians (0 à 2π)
    angles = np.linspace(0, 2*np.pi, angle_count, endpoint=False)
    
    # Créer une forme circulaire avec des "obstacles" simulés
    
    # Ajouter des variations pour simuler un environnement
    variations = np.zeros(angle_count)
    
    # Ajouter quelques "murs" et obstacles
    # Un "mur" de 30 degrés
    wall_start = int(angle_count * 0.1)
    wall_end = int(angle_count * 0.2)
    variations[wall_start:wall_end] = -2.0 * variations_scale
    
    # Un obstacle rond
    obstacle_center = int(angle_count * 0.5)
    obstacle_width = int(angle_count * 0.05)
    for i in range(obstacle_center - obstacle_width // 2, obstacle_center + obstacle_width // 2):
        idx = i % angle_count
        dist = abs(i - obstacle_center)
        variations[idx] = -2.0 * variations_scale + 0.05 * dist
    
    # Un autre obstacle plus petit
    obstacle2_center = int(angle_count * 0.75)
    obstacle2_width = int(angle_count * 0.025)
    for i in range(obstacle2_center - obstacle2_width // 2, obstacle2_center + obstacle2_width // 2):
        idx = i % angle_count
        variations[idx] = -1.5 * variations_scale
    
    # Ajouter un peu de bruit aléatoire
    noise = np.random.normal(0, 0.1, angle_count)
    
    # Calculer les distances finales
    distances = base_distance + variations + noise
    
    # Assurer que toutes les distances sont positives
    distances = np.maximum(distances, 0.1)
    
    return timestamps, distances

def create_laser_scan_corridor(center=60.0, angle_count=360, base_distance=10.0):
    """Crée des données laser simulant un corridor"""
    timestamps = np.array([center] * angle_count)
    
    # Définir les limites du corridor (en indices d'angle)
    left_wall_start = int(angle_count * 0.3)
    left_wall_end = int(angle_count * 0.5)
    
    right_wall_start = int(angle_count * 0.7)
    right_wall_end = int(angle_count * 0.9)
    
    # Initialiser les distances (par défaut, base_distance partout)
    distances = np.ones(angle_count) * base_distance
    
    # Ajouter les murs du corridor (plus proches)
    distances[left_wall_start:left_wall_end] = base_distance * 0.4
    distances[right_wall_start:right_wall_end] = base_distance * 0.4
    
    # Ajouter quelques irrégularités aux murs
    for i in range(left_wall_start, left_wall_end):
        # Ajouter un peu de variation pour rendre le mur irrégulier
        distances[i] += np.random.normal(0, 0.2)
    
    for i in range(right_wall_start, right_wall_end):
        # Ajouter un peu de variation pour rendre le mur irrégulier
        distances[i] += np.random.normal(0, 0.2)
    
    # Ajouter un léger bruit aléatoire partout
    distances += np.random.normal(0, 0.1, angle_count)
    
    # Assurer que toutes les distances sont positives
    distances = np.maximum(distances, 0.1)
    
    return timestamps, distances

def create_laser_scan_room(center=75.0, angle_count=360, room_size=8.0):
    """Crée des données laser simulant une pièce fermée"""
    timestamps = np.array([center] * angle_count)
    
    # Angles en radians (0 à 2π)
    angles = np.linspace(0, 2*np.pi, angle_count, endpoint=False)
    
    # Initialiser les distances pour une pièce rectangulaire
    distances = np.ones(angle_count) * room_size
    
    # Créer une pièce rectangulaire
    for i in range(angle_count):
        angle = angles[i]
        # Calculer la distance au mur le plus proche
        x_dist = room_size / np.abs(np.cos(angle)) if np.cos(angle) != 0 else 1000
        y_dist = room_size / np.abs(np.sin(angle)) if np.sin(angle) != 0 else 1000
        distances[i] = min(x_dist, y_dist)
    
    # Ajouter quelques obstacles dans la pièce
    # Table au centre
    center_obstacle_start = int(angle_count * 0.4)
    center_obstacle_end = int(angle_count * 0.6)
    for i in range(center_obstacle_start, center_obstacle_end):
        distances[i] = min(distances[i], room_size * 0.3)
    
    # Quelques petits objets éparpillés
    for _ in range(5):
        pos = np.random.randint(0, angle_count)
        width = np.random.randint(5, 15)
        for i in range(pos - width//2, pos + width//2):
            idx = i % angle_count
            distances[idx] = min(distances[idx], room_size * np.random.uniform(0.4, 0.7))
    
    # Ajouter un léger bruit aléatoire
    distances += np.random.normal(0, 0.1, angle_count)
    
    # Assurer que toutes les distances sont positives et raisonnables
    distances = np.maximum(distances, 0.1)
    distances = np.minimum(distances, room_size * 1.1)  # Éviter des valeurs trop grandes
    
    return timestamps, distances

def create_circle_image(timestamp=20.0, size=50):
    """Crée une image simple d'un cercle"""
    timestamp = np.array([timestamp])
    
    # Créer une image vide (blanc)
    img = Image.new('L', (size, size), 255)
    draw = ImageDraw.Draw(img)
    
    # Dessiner un cercle noir
    margin = size // 10
    draw.ellipse((margin, margin, size - margin, size - margin), fill=0)
    
    # Convertir en tableau numpy
    image_array = np.array(img).flatten()
    
    return timestamp, image_array

def create_grid_image(timestamp=30.0, size=64):
    """Crée une image simple avec une grille"""
    timestamp = np.array([timestamp])
    
    # Créer une image blanche
    img = Image.new('L', (size, size), 255)
    draw = ImageDraw.Draw(img)
    
    # Dessiner une grille
    grid_size = 8
    for i in range(0, size, grid_size):
        # Lignes horizontales
        draw.line([(0, i), (size, i)], fill=0)
        # Lignes verticales
        draw.line([(i, 0), (i, size)], fill=0)
    
    # Convertir en tableau numpy
    image_array = np.array(img).flatten()
    
    return timestamp, image_array

def create_cross_image(timestamp=40.0, size=64):
    """Crée une image simple avec une croix"""
    timestamp = np.array([timestamp])
    
    # Créer une image blanche
    img = Image.new('L', (size, size), 255)
    draw = ImageDraw.Draw(img)
    
    # Dessiner une croix
    margin = size // 10
    # Ligne diagonale de haut à gauche à bas à droite
    draw.line([(margin, margin), (size - margin, size - margin)], fill=0, width=3)
    # Ligne diagonale de haut à droite à bas à gauche
    draw.line([(size - margin, margin), (margin, size - margin)], fill=0, width=3)
    
    # Convertir en tableau numpy
    image_array = np.array(img).flatten()
    
    return timestamp, image_array

def create_star_image(timestamp=50.0, size=80):
    """Crée une image simple d'une étoile"""
    timestamp = np.array([timestamp])
    
    # Créer une image vide (blanc)
    img = Image.new('L', (size, size), 255)
    draw = ImageDraw.Draw(img)
    
    # Dessiner une étoile à 5 branches
    center_x, center_y = size // 2, size // 2
    radius_outer = size // 2 - 5
    radius_inner = radius_outer // 2
    
    # Calculer les points de l'étoile
    points = []
    for i in range(10):
        angle = np.pi / 2 + i * 2 * np.pi / 10
        radius = radius_outer if i % 2 == 0 else radius_inner
        x = center_x + int(radius * np.cos(angle))
        y = center_y - int(radius * np.sin(angle))
        points.append((x, y))
    
    # Dessiner l'étoile
    draw.polygon(points, fill=0)
    
    # Convertir en tableau numpy
    image_array = np.array(img).flatten()
    
    return timestamp, image_array

def create_rectangle_image(timestamp=60.0, size=60):
    """Crée une image simple d'un rectangle"""
    timestamp = np.array([timestamp])
    
    # Créer une image vide (blanc)
    img = Image.new('L', (size, size), 255)
    draw = ImageDraw.Draw(img)
    
    # Dessiner un rectangle
    margin = size // 6
    draw.rectangle((margin, margin * 2, size - margin, size - margin * 2), fill=0)
    
    # Convertir en tableau numpy
    image_array = np.array(img).flatten()
    
    return timestamp, image_array

def create_gradient_image(timestamp=70.0, size=100):
    """Crée une image d'un dégradé"""
    timestamp = np.array([timestamp])
    
    # Créer un gradient
    gradient = np.zeros((size, size), dtype=np.uint8)
    for i in range(size):
        gradient[i, :] = i * 255 // size
    
    # Convertir en tableau 1D
    image_array = gradient.flatten()
    
    return timestamp, image_array

def append_simplified(mdf, timestamps, values, name, **kwargs):
    """Version simplifiée de la méthode append qui fonctionne avec différentes versions de asammdf"""
    try:
        # Essayer avec les arguments nommés
        mdf.append(timestamps, values, name, **kwargs)
    except (TypeError, AttributeError):
        try:
            # Essayer sans les arguments nommés
            mdf.append(timestamps, values, name)
        except (TypeError, AttributeError) as e:
            print(f"Erreur lors de l'ajout du signal {name}: {e}")
            print("Essai d'une méthode alternative...")
            
            try:
                # Méthode alternative - créer un groupe de signaux et l'ajouter
                from asammdf.blocks.mdf_v4 import Signal
                signal = Signal(samples=values, timestamps=timestamps, name=name)
                signals = [signal]
                mdf.append(signals)
            except Exception as e2:
                print(f"Échec de la méthode alternative: {e2}")
                print("Impossible d'ajouter le signal.")

def main():
    parser = argparse.ArgumentParser(description='Générer un fichier MDF de test')
    parser.add_argument('output_path', nargs='?', default='.', help='Chemin de sortie pour le fichier MDF')
    args = parser.parse_args()
    
    output_dir = args.output_path
    output_file = os.path.join(output_dir, 'test_mdf_file.mdf')
    
    try:
        # Vérifier la version de asammdf
        from asammdf import __version__ as asammdf_version
        print(f"Version de asammdf: {asammdf_version}")
    except ImportError:
        print("Impossible de déterminer la version de asammdf")
    
    # Créer un nouveau fichier MDF (version 4.10)
    try:
        mdf = MDF(version='4.10')
    except Exception as e:
        print(f"Erreur lors de la création du fichier MDF: {e}")
        print("Essai avec la version par défaut...")
        try:
            mdf = MDF()
        except Exception as e2:
            print(f"Erreur lors de la création du fichier MDF avec version par défaut: {e2}")
            return 1
    
    print("Génération des données...")
    
    # Ajouter des événements textuels
    print("- Ajout des événements textuels")
    text_timestamps, text_events = create_text_events()
    append_simplified(mdf, text_timestamps, text_events, 'evenements_texte')
    
    # Ajouter des erreurs
    error_timestamps, error_events = create_error_log_events()
    append_simplified(mdf, error_timestamps, error_events, 'erreurs_log')
    
    # Ajouter des messages de debug
    debug_timestamps, debug_events = create_debug_log_events()
    append_simplified(mdf, debug_timestamps, debug_events, 'debug_log')
    
    # Ajouter au moins 4 courbes
    print("- Ajout d'au moins 4 courbes")
    
    # 1. Onde sinusoïdale
    sine_timestamps, sine_values = create_sine_wave(freq=0.2, amplitude=10.0)
    append_simplified(mdf, sine_timestamps, sine_values, 'onde_sinus', unit='m/s')
    
    # 2. Onde carrée
    square_timestamps, square_values = create_square_wave(freq=0.1, amplitude=5.0)
    append_simplified(mdf, square_timestamps, square_values, 'onde_carree', unit='V')
    
    # 3. Onde triangulaire
    triangle_timestamps, triangle_values = create_triangle_wave(freq=0.05, amplitude=3.0)
    append_simplified(mdf, triangle_timestamps, triangle_values, 'onde_triangle', unit='A')
    
    # 4. Onde en dents de scie
    sawtooth_timestamps, sawtooth_values = create_sawtooth_wave(freq=0.08, amplitude=4.0)
    append_simplified(mdf, sawtooth_timestamps, sawtooth_values, 'onde_dents_de_scie', unit='°C')
    
    # 5. Courbe exponentielle
    exp_timestamps, exp_values = create_exponential_curve(rate=0.02, amplitude=2.0, offset=1.0)
    append_simplified(mdf, exp_timestamps, exp_values, 'courbe_exponentielle', unit='Pa')
    
    # 6. Marche aléatoire
    random_timestamps, random_values = create_random_walk(step_size=0.08, amplitude=8.0)
    append_simplified(mdf, random_timestamps, random_values, 'marche_aleatoire', unit='rad/s')
    
    # Ajouter au moins 3 scans laser
    print("- Ajout d'au moins 3 scans laser")
    
    # 1. Scan laser avec obstacles
    laser_timestamps, laser_distances = create_laser_scan(center=25.0, variations_scale=1.2)
    append_simplified(mdf, laser_timestamps, laser_distances, 'scan_laser_1', unit='m')
    
    # 2. Scan laser d'un corridor
    corridor_timestamps, corridor_distances = create_laser_scan_corridor(center=50.0)
    append_simplified(mdf, corridor_timestamps, corridor_distances, 'scan_laser_corridor', unit='m')
    
    # 3. Scan laser d'une pièce
    room_timestamps, room_distances = create_laser_scan_room(center=75.0)
    append_simplified(mdf, room_timestamps, room_distances, 'scan_laser_piece', unit='m')
    
    # Ajouter au moins 5 images
    print("- Ajout d'au moins 5 images différentes")
    
    # 1. Image d'un cercle
    circle_timestamp, circle_data = create_circle_image(timestamp=20.0)
    append_simplified(mdf, circle_timestamp, circle_data, 'image_cercle')
    
    # 2. Image d'une grille
    grid_timestamp, grid_data = create_grid_image(timestamp=35.0)
    append_simplified(mdf, grid_timestamp, grid_data, 'image_grille')
    
    # 3. Image d'une croix
    cross_timestamp, cross_data = create_cross_image(timestamp=50.0)
    append_simplified(mdf, cross_timestamp, cross_data, 'image_croix')
    
    # 4. Image d'une étoile
    star_timestamp, star_data = create_star_image(timestamp=65.0)
    append_simplified(mdf, star_timestamp, star_data, 'image_etoile')
    
    # 5. Image d'un rectangle
    rect_timestamp, rect_data = create_rectangle_image(timestamp=80.0)
    append_simplified(mdf, rect_timestamp, rect_data, 'image_rectangle')
    
    # 6. Image d'un gradient
    gradient_timestamp, gradient_data = create_gradient_image(timestamp=95.0)
    append_simplified(mdf, gradient_timestamp, gradient_data, 'image_gradient')
    
    # Sauvegarder le fichier
    print(f"Sauvegarde du fichier MDF dans {output_file}...")
    try:
        mdf.save(output_file, overwrite=True)
        print(f"Fichier MDF créé avec succès: {output_file}")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde du fichier MDF: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
