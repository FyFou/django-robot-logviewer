"""
Module contenant les fonctions de traitement des différents types de canaux MDF.
"""
import logging
import io
import binascii
import numpy as np
from datetime import datetime

from django.core.files.base import ContentFile

from .models import RobotLog, CurveMeasurement, Laser2DScan, ImageData, CANMessage
from .can_parser import extract_can_messages_from_mdf

logger = logging.getLogger(__name__)

def _process_text_event(self, channel_name, signal):
    """Traite un canal comme un événement textuel et crée des logs"""
    logs = []
    
    # Convertir les timestamps en datetime
    timestamps = [datetime.fromtimestamp(ts) for ts in signal.timestamps]
    
    # Traiter chaque échantillon
    for i, (ts, value) in enumerate(zip(timestamps, signal.samples)):
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
            robot_id="MDF_Import",  # À adapter selon les métadonnées
            level="INFO",  # Niveau par défaut
            message=f"{channel_name}: {value}",
            source=f"MDF Import: {self.mdf_file.name if self.mdf_file else 'Unknown'}",
            log_type="TEXT"
            # Ne pas assigner au groupe ici, cela sera fait par process_channel
        )
        
        # Ajouter des métadonnées
        metadata = {
            'channel_name': channel_name,
            'sample_index': i,
            'unit': signal.unit if hasattr(signal, 'unit') else None,
            'comment': signal.comment if hasattr(signal, 'comment') else None
            # Ne pas ajouter group_id ici, cela sera fait par process_channel
        }
        log.set_metadata_from_dict(metadata)
        
        logs.append(log)
        
    return logs

def _process_curve_data(self, channel_name, signal):
    """Traite un canal comme des données de courbe"""
    # Créer un log principal pour cette courbe
    main_log = RobotLog(
        timestamp=datetime.fromtimestamp(signal.timestamps[0]),
        robot_id="MDF_Import",
        level="INFO",
        message=f"Données de courbe pour {channel_name}",
        source=f"MDF Import: {self.mdf_file.name if self.mdf_file else 'Unknown'}",
        log_type="CURVE"
        # Ne pas assigner au groupe ici, cela sera fait par process_channel
    )
    
    # Ajouter des métadonnées
    metadata = {
        'channel_name': channel_name,
        'samples_count': len(signal.samples),
        'unit': signal.unit if hasattr(signal, 'unit') else None,
        'start_time': signal.timestamps[0],
        'end_time': signal.timestamps[-1],
        'duration': signal.timestamps[-1] - signal.timestamps[0]
        # Ne pas ajouter group_id ici, cela sera fait par process_channel
    }
    main_log.set_metadata_from_dict(metadata)
    
    # Créer les mesures de courbe associées
    curve_measurements = []
    for i, (ts, value) in enumerate(zip(signal.timestamps, signal.samples)):
        measurement = CurveMeasurement(
            timestamp=datetime.fromtimestamp(ts),
            sensor_name=channel_name,
            value=float(value)
        )
        curve_measurements.append(measurement)
    
    return main_log, curve_measurements

def _process_laser_data(self, channel_name, signal):
    """Traite un canal comme des données laser 2D"""
    # Créer un log principal pour ces données laser
    main_log = RobotLog(
        timestamp=datetime.fromtimestamp(signal.timestamps[0]),
        robot_id="MDF_Import",
        level="INFO",
        message=f"Données laser 2D pour {channel_name}",
        source=f"MDF Import: {self.mdf_file.name if self.mdf_file else 'Unknown'}",
        log_type="LASER2D"
        # Ne pas assigner au groupe ici, cela sera fait par process_channel
    )
    
    # Estimer les paramètres du laser
    # Ceci est une estimation - les vrais paramètres devraient être dans les métadonnées du MDF
    angle_min = -np.pi / 2  # Par défaut, supposons un scan de 180 degrés
    angle_max = np.pi / 2
    angle_increment = np.pi / len(signal.samples)
    
    # Ajouter des métadonnées
    metadata = {
        'channel_name': channel_name,
        'points_count': len(signal.samples),
        'unit': signal.unit if hasattr(signal, 'unit') else 'm',
        'angle_min': angle_min,
        'angle_max': angle_max,
        'angle_increment': angle_increment
        # Ne pas ajouter group_id ici, cela sera fait par process_channel
    }
    main_log.set_metadata_from_dict(metadata)
    
    # Créer l'objet de scan laser
    laser_scan = Laser2DScan(
        timestamp=datetime.fromtimestamp(signal.timestamps[0]),
        angle_min=angle_min,
        angle_max=angle_max,
        angle_increment=angle_increment
    )
    
    # Convertir les données de plage en liste et les stocker
    range_data = signal.samples.tolist()
    laser_scan.set_range_data_from_list(range_data)
    
    return main_log, laser_scan

def _process_image_data(self, channel_name, signal):
    """Traite un canal comme des données d'image"""
    from PIL import Image
    
    # Créer un log principal pour cette image
    main_log = RobotLog(
        timestamp=datetime.fromtimestamp(signal.timestamps[0]),
        robot_id="MDF_Import",
        level="INFO",
        message=f"Image pour {channel_name}",
        source=f"MDF Import: {self.mdf_file.name if self.mdf_file else 'Unknown'}",
        log_type="IMAGE"
        # Ne pas assigner au groupe ici, cela sera fait par process_channel
    )
    
    # Essayer de déterminer le type d'image et de la décoder
    try:
        # Convertir les données en tableau d'octets
        image_data = signal.samples.tobytes()
        
        # Essayer de créer une image à partir des données
        img = Image.open(io.BytesIO(image_data))
        
        # Créer l'objet ImageData
        image_obj = ImageData(
            timestamp=datetime.fromtimestamp(signal.timestamps[0]),
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
            f"{channel_name}_image.jpg",
            ContentFile(img_io.getvalue()),
            save=False
        )
        
        # Ajouter des métadonnées sans l'ID du groupe
        metadata = {
            'channel_name': channel_name,
            'width': img.width,
            'height': img.height,
            'format': img.format if img.format else 'JPEG'
            # Ne pas ajouter group_id ici, cela sera fait par process_channel
        }
        main_log.set_metadata_from_dict(metadata)
        
        return main_log, image_obj
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement de l'image pour {channel_name}: {e}")
        
        # En cas d'échec, créer une entrée de journal simple
        metadata = {
            'channel_name': channel_name,
            'data_size': len(signal.samples),
            'error': str(e)
            # Ne pas ajouter group_id ici, cela sera fait par process_channel
        }
        main_log.set_metadata_from_dict(metadata)
        
        return main_log, None

def _process_can_data(self, channel_name, signal):
    """Traite un canal comme des données CAN"""
    # Créer un log principal pour ces données CAN
    main_log = RobotLog(
        timestamp=datetime.fromtimestamp(signal.timestamps[0]),
        robot_id="MDF_Import",
        level="INFO",
        message=f"Données CAN pour {channel_name}",
        source=f"MDF Import: {self.mdf_file.name if self.mdf_file else 'Unknown'}",
        log_type="CAN"
        # Ne pas assigner au groupe ici, cela sera fait par process_channel
    )
    
    # Ajouter des métadonnées
    metadata = {
        'channel_name': channel_name,
        'samples_count': len(signal.samples),
        'start_time': signal.timestamps[0],
        'end_time': signal.timestamps[-1],
        'duration': signal.timestamps[-1] - signal.timestamps[0]
        # Ne pas ajouter group_id ici, cela sera fait par process_channel
    }
    
    # Si nous avons un parser DBC, ajouter l'info
    if hasattr(self, '_dbc_parser') and self._dbc_parser:
        metadata['dbc_file'] = self.mdf_file.dbc_file.name if hasattr(self, 'mdf_file') and self.mdf_file and self.mdf_file.dbc_file else "Non spécifié"
    
    main_log.set_metadata_from_dict(metadata)
    
    # Extraire les messages CAN
    try:
        # Extraire et traiter les messages CAN
        can_messages = []
        
        # Méthode 1: Utiliser notre fonction d'extraction
        if hasattr(signal, 'samples') and len(signal.samples) > 0:
            # Essayer d'extraire les messages CAN du signal
            extracted_messages = extract_can_messages_from_mdf(self._mdf, channel_name)
            
            # Traiter chaque message extrait
            for timestamp, can_id, can_data in extracted_messages:
                # Convertir l'identifiant en hexadécimal
                can_id_hex = f"0x{can_id:X}"
                
                # Convertir les données en hexadécimal
                data_hex = binascii.hexlify(can_data).decode('utf-8')
                
                # Créer l'objet message CAN
                can_message = CANMessage(
                    timestamp=datetime.fromtimestamp(timestamp),
                    can_id=can_id_hex,
                    raw_data=data_hex
                )
                
                # Si on a un parseur DBC, décoder le message
                if hasattr(self, '_dbc_parser') and self._dbc_parser:
                    message_name, signals = self._dbc_parser.decode_message(can_id, can_data)
                    
                    if message_name:
                        can_message.message_name = message_name
                        
                        # On stockera les signaux dans la base de données plus tard
                        can_message.signals_data = signals
                
                can_messages.append(can_message)
        
        return main_log, can_messages
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement des données CAN pour {channel_name}: {e}")
        
        # En cas d'échec, mettre à jour les métadonnées
        metadata['error'] = str(e)
        main_log.set_metadata_from_dict(metadata)
        
        return main_log, []
