"""
Module contenant les fonctions de détection du type de canal MDF.
"""
import logging

logger = logging.getLogger(__name__)

def _is_text_event(self, channel_name, signal):
    """Détermine si un canal contient des événements textuels"""
    # Logique pour détecter un canal d'événements textuels
    # Par exemple, vérifie si le canal contient des chaînes ou si son nom suggère un événement
    if 'event' in channel_name.lower() or 'message' in channel_name.lower():
        return True
    
    # Vérifie le type de données
    if hasattr(signal, 'samples') and signal.samples.dtype.kind in ['S', 'U']:
        return True
        
    return False

def _is_curve_data(self, channel_name, signal):
    """Détermine si un canal contient des données de courbe"""
    # Vérifie si c'est une série de valeurs numériques
    if (hasattr(signal, 'samples') and 
        signal.samples.dtype.kind in ['i', 'u', 'f'] and 
        len(signal.samples) > 1):
        return True
        
    return False

def _is_laser_data(self, channel_name, signal):
    """Détermine si un canal contient des données laser 2D"""
    # Logique pour détecter un canal de données laser
    # Par exemple, vérifie si le nom du canal contient des mots-clés comme "laser" ou "scan"
    if 'laser' in channel_name.lower() or 'scan' in channel_name.lower() or 'lidar' in channel_name.lower():
        # Vérifie également si les données ressemblent à un scan laser (tableau de distances)
        if (hasattr(signal, 'samples') and 
            signal.samples.dtype.kind in ['i', 'u', 'f'] and 
            len(signal.samples) > 10):
            return True
            
    return False

def _is_image_data(self, channel_name, signal):
    """Détermine si un canal contient des données d'image"""
    # Logique pour détecter un canal d'image
    if 'image' in channel_name.lower() or 'camera' in channel_name.lower() or 'photo' in channel_name.lower():
        return True
        
    # Vérifier si c'est un tableau d'octets assez grand pour être une image
    if (hasattr(signal, 'samples') and 
        signal.samples.dtype.kind == 'u' and 
        signal.samples.dtype.itemsize == 1 and
        len(signal.samples) > 1000):  # Disons qu'une image fait au moins 1 Ko
        return True
        
    return False

def _is_can_data(self, channel_name, signal):
    """Détermine si un canal contient des données CAN"""
    # Logique pour détecter un canal de données CAN
    # Par exemple, vérifie si le nom du canal contient "can" ou "bus"
    if 'can' in channel_name.lower() or 'bus' in channel_name.lower():
        return True
        
    return False
