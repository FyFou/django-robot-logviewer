"""
Script simplifié pour générer un fichier MDF de test minimal.
Ce script garantit la création d'un fichier MDF valide pour tester l'importation.
"""

import os
import numpy as np

try:
    from asammdf import MDF
    from asammdf.blocks.mdf_v4 import Signal
except ImportError:
    print("Erreur: La bibliothèque asammdf n'est pas installée. Installez-la avec:")
    print("pip install asammdf")
    exit(1)

# Créer un fichier MDF simple
print("Création d'un fichier MDF simple...")

try:
    # Essayer d'abord la méthode simple
    mdf = MDF()
    
    # Données simples
    timestamps = np.linspace(0, 10, 100)
    values = np.sin(timestamps)
    
    # Essayer la méthode standard d'abord
    try:
        print("Méthode 1: Utilisation de mdf.append() standard")
        mdf.append(timestamps, values, "sinus")
    except Exception as e:
        print(f"Méthode 1 a échoué: {e}")
        print("Méthode 2: Utilisation de l'objet Signal")
        
        # Utiliser l'approche avec un objet Signal
        signal = Signal(
            samples=values,
            timestamps=timestamps,
            name='sinus'
        )
        mdf.append([signal])
    
    # Sauvegarder le fichier
    output_file = "simple_test.mdf"
    mdf.save(output_file, overwrite=True)
    
    # Vérifier si le fichier a été créé et a une taille non nulle
    if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
        print(f"Succès! Fichier MDF créé: {output_file}")
        print(f"Taille du fichier: {os.path.getsize(output_file)} octets")
    else:
        print(f"Erreur: Le fichier {output_file} est vide ou n'a pas été créé.")
    
except Exception as e:
    print(f"Erreur lors de la création du fichier MDF: {e}")
    
    # Méthode alternative encore plus simple
    print("\nEssai d'une méthode alternative...")
    
    try:
        # Créer une instance MDF avec version explicite
        mdf = MDF(version='4.10')
        
        # Créer des signaux très simples
        timestamps = np.array([0, 1, 2, 3, 4, 5], dtype=np.float64)
        values = np.array([0, 1, 0, 1, 0, 1], dtype=np.float64)
        
        # Créer un signal manuellement
        signal = Signal(
            samples=values,
            timestamps=timestamps,
            name='test_signal'
        )
        
        # Ajouter le signal
        mdf.append([signal])
        
        # Sauvegarder dans un fichier avec un nom différent
        output_file = "simplest_test.mdf"
        mdf.save(output_file, overwrite=True)
        
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            print(f"Succès avec la méthode alternative! Fichier MDF créé: {output_file}")
            print(f"Taille du fichier: {os.path.getsize(output_file)} octets")
        else:
            print(f"Erreur: Le fichier {output_file} est vide ou n'a pas été créé.")
    
    except Exception as e2:
        print(f"La méthode alternative a également échoué: {e2}")
        print("Veuillez vérifier l'installation de asammdf et des dépendances.")
