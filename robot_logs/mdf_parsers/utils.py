"""
Fonctions utilitaires pour le parsing des fichiers MDF
"""
import logging
import io
import re
from datetime import datetime
from PIL import Image
import numpy as np

from django.core.files.base import ContentFile

from ..models import RobotLog, CurveMeasurement, Laser2DScan, ImageData

logger = logging.getLogger(__name__)

def is_text_event(channel_name, data):
    """Détermine si un canal contient des événements textuels"""
    # Vérification par le nom du canal
    if 'event' in channel_name.lower() or 'message' in channel_name.lower() or 'text' in channel_name.lower():
        return True
    
    # Vérification par le type de données
    if hasattr(data, 'dtype') and data.dtype.kind in ['S', 'U']:
        return True
        
    return False

def is_curve_data(channel_name, data):
    """Détermine si un canal contient des données de courbe"""
    # Vérification si c'est une série de valeurs numériques
    if (hasattr(data, 'dtype') and 
        data.dtype.kind in ['i', 'u', 'f'] and 
        hasattr(data, '__len__') and len(data) > 1):
        return True
        
    return False

def is_laser_data(channel_name, data):
    """Détermine si un canal contient des données laser 2D"""
    # Vérification par le nom du canal
    if 'laser' in channel_name.lower() or 'scan' in channel_name.lower() or 'lidar' in channel_name.lower():
        # Vérification des données (tableau de distances)
        if (hasattr(data, 'dtype') and 
            data.dtype.kind in ['i', 'u', 'f'] and 
            hasattr(data, '__len__') and len(data) > 10):
            return True
            
    return False

def is_image_data(channel_name, data):
    """Détermine si un canal contient des données d'image"""
    # Vérification par le nom du canal
    if 'image' in channel_name.lower() or 'camera' in channel_name.lower() or 'photo' in channel_name.lower():
        return True
        
    # Vérification par le type et la taille des données
    if (hasattr(data, 'dtype') and 
        data.dtype.kind == 'u' and 
        hasattr(data, '__len__') and len(data) > 1000):  # Au moins 1 Ko
        return True
        
    return False

def process_text_event(channel_name, data, timestamps, unit='', description=''):
    """Traite un canal comme un événement textuel et crée des logs"""
    logs = []
    
    # Convertir les timestamps en datetime
    timestamps_dt = [datetime.fromtimestamp(ts) for ts in timestamps]
    
    # Traiter chaque échantillon
    for i, (ts, value) in enumerate(zip(timestamps_dt, data)):
        # Convertir la valeur en chaîne si nécessaire
        if isinstance(value, (bytes, bytearray)):
            try:
                value = value.decode('utf-8')
            except UnicodeDecodeError:
                value = f"Données binaires ({len(value)} octets)"
        elif not isinstance(value, str):
            value = str(value)
            
        log = RobotLog(
            timestamp=ts,
            robot_id="MDF_Import",
            level="INFO",
            message=f"{channel_name}: {value}",
            source="MDF Import",
            log_type="TEXT"
        )
        
        # Ajouter des métadonnées
        metadata = {
            'channel_name': channel_name,
            'sample_index': i,
            'unit': unit,
            'description': description,
        }
        
        log.set_metadata_from_dict(metadata)
        logs.append(log)
        
    return logs

def process_curve_data(channel_name, data, timestamps, unit='', description=''):
    """Traite un canal comme des données de courbe"""
    # Créer un log principal pour cette courbe
    main_log = RobotLog(
        timestamp=datetime.fromtimestamp(timestamps[0]),
        robot_id="MDF_Import",
        level="INFO",
        message=f"Données de courbe pour {channel_name}",
        source="MDF Import",
        log_type="CURVE"
    )
    
    # Ajouter des métadonnées
    metadata = {
        'channel_name': channel_name,
        'samples_count': len(data),
        'unit': unit,
        'description': description,
        'start_time': timestamps[0],
        'end_time': timestamps[-1],
        'duration': timestamps[-1] - timestamps[0],
    }
    main_log.set_metadata_from_dict(metadata)
    
    # Générer un graphique de la courbe pour prévisualisation
    try:
        import matplotlib.pyplot as plt
        plt.figure(figsize=(10, 6))
        plt.plot(timestamps, data)
        plt.title(f"Courbe: {channel_name}")
        plt.xlabel("Temps (s)")
        plt.ylabel(unit or "Valeur")
        plt.grid(True)
        
        # Sauvegarder l'image dans un buffer
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='PNG')
        img_buffer.seek(0)
        plt.close()
        
        # Attacher l'image au log
        main_log.data_file.save(
            f"{channel_name.replace('.', '_')}_preview.png",
            ContentFile(img_buffer.getvalue()),
            save=False
        )
    except Exception as e:
        logger.error(f"Erreur lors de la génération du graphique pour {channel_name}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    
    # Créer les mesures de courbe associées
    curve_measurements = []
    for i, (ts, value) in enumerate(zip(timestamps, data)):
        try:
            # Convertir en float (peut nécessiter un casting spécial pour certains types)
            if hasattr(value, 'dtype'):
                value = float(value)
            else:
                value = float(value)
                
            measurement = CurveMeasurement(
                timestamp=datetime.fromtimestamp(ts),
                sensor_name=channel_name,
                value=value
            )
            curve_measurements.append(measurement)
        except (ValueError, TypeError) as e:
            logger.warning(f"Impossible de convertir la valeur {value} en float pour {channel_name}: {str(e)}")
    
    return main_log, curve_measurements

def process_laser_data(channel_name, data, timestamps, unit='', description=''):
    """Traite un canal comme des données laser 2D"""
    # Créer un log principal pour ces données laser
    main_log = RobotLog(
        timestamp=datetime.fromtimestamp(timestamps[0]),
        robot_id="MDF_Import",
        level="INFO",
        message=f"Données laser 2D pour {channel_name}",
        source="MDF Import",
        log_type="LASER2D"
    )
    
    # Estimer les paramètres du laser (par défaut)
    angle_min = -np.pi / 2  # Par défaut, scan de 180 degrés
    angle_max = np.pi / 2
    angle_increment = np.pi / len(data)
    
    # Ajouter des métadonnées
    metadata = {
        'channel_name': channel_name,
        'points_count': len(data),
        'unit': unit or 'm',
        'description': description,
        'angle_min': angle_min,
        'angle_max': angle_max,
        'angle_increment': angle_increment,
    }
    main_log.set_metadata_from_dict(metadata)
    
    # Créer l'objet de scan laser
    laser_scan = Laser2DScan(
        timestamp=datetime.fromtimestamp(timestamps[0]),
        angle_min=angle_min,
        angle_max=angle_max,
        angle_increment=angle_increment
    )
    
    # Convertir les données de plage en liste et les stocker
    range_data = data.tolist() if hasattr(data, 'tolist') else list(data)
    laser_scan.set_range_data_from_list(range_data)
    
    # Générer une visualisation du scan laser
    try:
        import matplotlib.pyplot as plt
        
        # Créer un graphique polaire
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(111, projection='polar')
        
        # Calculer les angles pour chaque mesure
        angles = np.linspace(angle_min, angle_max, len(range_data))
        
        # Tracer les points du scan
        ax.scatter(angles, range_data, s=2)
        ax.set_title(f"Scan Laser: {channel_name}")
        ax.grid(True)
        
        # Sauvegarder l'image dans un buffer
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='PNG')
        img_buffer.seek(0)
        plt.close()
        
        # Attacher l'image au log
        main_log.data_file.save(
            f"{channel_name.replace('.', '_')}_laser_preview.png",
            ContentFile(img_buffer.getvalue()),
            save=False
        )
    except Exception as e:
        logger.error(f"Erreur lors de la génération de la visualisation laser pour {channel_name}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    
    return main_log, laser_scan

def process_image_data(channel_name, data, timestamps, unit='', description=''):
    """Traite un canal comme des données d'image"""
    # Créer un log principal pour cette image
    main_log = RobotLog(
        timestamp=datetime.fromtimestamp(timestamps[0]),
        robot_id="MDF_Import",
        level="INFO",
        message=f"Image pour {channel_name}",
        source="MDF Import",
        log_type="IMAGE"
    )
    
    # Essayer de déterminer le type d'image et de la décoder
    try:
        # Convertir les données en tableau d'octets
        image_data = data.tobytes() if hasattr(data, 'tobytes') else bytes(data)
        
        # Essayer de créer une image à partir des données
        img = Image.open(io.BytesIO(image_data))
        
        # Créer l'objet ImageData
        image_obj = ImageData(
            timestamp=datetime.fromtimestamp(timestamps[0]),
            width=img.width,
            height=img.height,
            format=img.format if img.format else 'JPEG',
            description=f"Image extraite du canal {channel_name}"
        )
        
        # Enregistrer l'image
        img_io = io.BytesIO()
        img.save(img_io, format=img.format if img.format else 'JPEG')
        img_io.seek(0)
        
        # Sauvegarder l'image dans le champ image_file
        image_obj.image_file.save(
            f"{channel_name.replace('.', '_')}_image.jpg",
            ContentFile(img_io.getvalue()),
            save=False
        )
        
        # Utiliser la même image comme aperçu pour le log
        main_log.data_file.save(
            f"{channel_name.replace('.', '_')}_image_preview.jpg",
            ContentFile(img_io.getvalue()),
            save=False
        )
        
        return main_log, image_obj
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement de l'image pour {channel_name}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # En cas d'échec, créer une entrée de journal simple
        metadata = {
            'channel_name': channel_name,
            'data_size': len(data),
            'unit': unit,
            'description': description,
            'error': str(e)
        }
        main_log.set_metadata_from_dict(metadata)
        
        return main_log, None

def sanitize_filename(filename):
    """Remplace les caractères potentiellement problématiques dans les noms de fichiers"""
    return re.sub(r'[^\w\-\.]', '_', filename)
