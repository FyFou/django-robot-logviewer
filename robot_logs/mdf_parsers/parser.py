"""
Classe principale du parser MDF avec choix automatique de l'implémentation
"""
import logging
import traceback
from datetime import datetime
import re

from .mdfreader_adapter import MdfReaderAdapter, MDFREADER_AVAILABLE
from .asammdf_adapter import AsamMdfAdapter, ASAMMDF_AVAILABLE
from .utils import (
    is_text_event, is_curve_data, is_laser_data, is_image_data,
    process_text_event, process_curve_data, process_laser_data, process_image_data
)
from ..models import RobotLog

logger = logging.getLogger(__name__)

class MDFParser:
    """
    Classe principale pour parser les fichiers MDF avec détection automatique
    de la bibliothèque à utiliser (mdfreader ou asammdf)
    """
    
    def __init__(self, file_path, mdf_file_obj=None):
        """
        Initialise le parser MDF
        
        Args:
            file_path: Chemin vers le fichier MDF
            mdf_file_obj: Instance de MDFFile liée au fichier
        """
        self.file_path = file_path
        self.mdf_file = mdf_file_obj
        self._adapter = None
        self._adapter_type = None  # 'mdfreader' ou 'asammdf'
        
    def open(self):
        """
        Ouvre le fichier MDF avec mdfreader ou asammdf, en fonction des bibliothèques disponibles
        Essaie d'abord mdfreader, puis asammdf si échec
        """
        # D'abord, essayer avec mdfreader
        if MDFREADER_AVAILABLE:
            adapter = MdfReaderAdapter()
            if adapter.open(self.file_path):
                self._adapter = adapter
                self._adapter_type = 'mdfreader'
                
                if self.mdf_file:
                    self.mdf_file.mdf_version = f"MDF {adapter.get_version()}"
                    self.mdf_file.save()
                
                return True
        
        # Ensuite, essayer avec asammdf si mdfreader a échoué
        if ASAMMDF_AVAILABLE:
            adapter = AsamMdfAdapter()
            if adapter.open(self.file_path):
                self._adapter = adapter
                self._adapter_type = 'asammdf'
                
                if self.mdf_file:
                    self.mdf_file.mdf_version = f"MDF {adapter.get_version()}"
                    self.mdf_file.save()
                
                return True
        
        # Si nous arrivons ici, aucune des bibliothèques n'a pu ouvrir le fichier
        logger.error(f"Impossible d'ouvrir le fichier MDF avec mdfreader ou asammdf: {self.file_path}")
        return False
    
    def close(self):
        """Ferme le fichier MDF"""
        if self._adapter:
            self._adapter.close()
            self._adapter = None
            self._adapter_type = None
    
    def get_channels(self):
        """Retourne la liste des canaux disponibles dans le fichier MDF"""
        if not self._adapter:
            if not self.open():
                return []
        
        return self._adapter.get_channels()
    
    def get_channel_info(self, channel_name):
        """Retourne les informations sur un canal spécifique"""
        if not self._adapter:
            if not self.open():
                return None
        
        return self._adapter.get_channel_info(channel_name)
    
    def process_channel(self, channel_name):
        """
        Traite un canal spécifique du fichier MDF
        
        Args:
            channel_name: Nom du canal à traiter
            
        Returns:
            Tuple contenant (logs, curve_measurements, laser_scans, images)
        """
        if not self._adapter:
            if not self.open():
                return [], [], [], []
        
        try:
            # Récupérer les données et timestamps du canal
            data, timestamps = self._adapter.get_channel_data_and_timestamps(channel_name)
            
            # Si aucune donnée n'est disponible
            if data is None or (hasattr(data, '__len__') and len(data) == 0):
                logger.error(f"Canal {channel_name} sans données")
                error_log = RobotLog(
                    timestamp=datetime.now(),
                    robot_id="MDF_Import",
                    level="ERROR",
                    message=f"Canal {channel_name} sans données",
                    source="MDF Import",
                    log_type="TEXT"
                )
                return [error_log], [], [], []
            
            # Obtenir les informations d'unité et description
            channel_info = self._adapter.get_unit_and_desc(channel_name)
            unit = channel_info['unit']
            description = channel_info['description']
            
            # Déterminer le type de données et le traiter
            if is_text_event(channel_name, data):
                logs = process_text_event(channel_name, data, timestamps, unit, description)
                return logs, [], [], []
                
            elif is_curve_data(channel_name, data):
                main_log, curve_measurements = process_curve_data(channel_name, data, timestamps, unit, description)
                return [main_log], curve_measurements, [], []
                
            elif is_laser_data(channel_name, data):
                main_log, laser_scan = process_laser_data(channel_name, data, timestamps, unit, description)
                return [main_log], [], [laser_scan], []
                
            elif is_image_data(channel_name, data):
                main_log, image = process_image_data(channel_name, data, timestamps, unit, description)
                if image:
                    return [main_log], [], [], [image]
                else:
                    return [main_log], [], [], []
                
            else:
                # Canal non reconnu, créer un log simple
                log = RobotLog(
                    timestamp=datetime.fromtimestamp(timestamps[0]),
                    robot_id="MDF_Import",
                    level="INFO",
                    message=f"Données non classifiées pour {channel_name}",
                    source="MDF Import",
                    log_type="TEXT"
                )
                
                # Ajouter des métadonnées
                metadata = {
                    'channel_name': channel_name,
                    'samples_count': len(data),
                    'data_type': str(data.dtype) if hasattr(data, 'dtype') else str(type(data)),
                    'unit': unit,
                    'description': description,
                }
                log.set_metadata_from_dict(metadata)
                
                return [log], [], [], []
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement du canal {channel_name}: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Créer un log d'erreur
            error_log = RobotLog(
                timestamp=datetime.now(),
                robot_id="MDF_Import",
                level="ERROR",
                message=f"Erreur lors du traitement du canal {channel_name}: {str(e)}",
                source="MDF Import",
                log_type="TEXT"
            )
            return [error_log], [], [], []
    
    def process_file(self):
        """
        Traite l'ensemble du fichier MDF et importe tous les canaux
        
        Returns:
            Dictionnaire contenant des statistiques sur les données importées
        """
        if not self._adapter:
            if not self.open():
                return {'error': 'Impossible d\'ouvrir le fichier MDF'}
        
        logger.info(f"Traitement du fichier MDF avec {self._adapter_type}")
        
        statistics = {
            'total_channels': 0,
            'text_logs': 0,
            'curve_logs': 0,
            'laser_logs': 0,
            'image_logs': 0,
            'curve_measurements': 0,
            'errors': 0,
            'parser_used': self._adapter_type
        }
        
        # Récupérer tous les canaux
        channels = self.get_channels()
        statistics['total_channels'] = len(channels)
        
        # Traiter chaque canal
        for channel_name in channels:
            # Si asammdf, ignorer les canaux générés avec des suffixes sauf si le canal original n'existe pas
            if self._adapter_type == 'asammdf' and re.search(r'_g\d+_i\d+$', channel_name):
                original_name = channel_name.split('_g')[0]
                # Vérifier auprès de l'adaptateur si le canal original existe
                if hasattr(self._adapter, 'channel_map') and original_name in self._adapter.channel_map:
                    logger.info(f"Ignorer le canal dupliqué: {channel_name}, utiliser le canal original: {original_name}")
                    continue
            
            logger.info(f"Traitement du canal: {channel_name}")
            logs, curve_measurements, laser_scans, images = self.process_channel(channel_name)
            
            # Sauvegarder les logs
            for log in logs:
                try:
                    log.save()
                    
                    # Associer les mesures de courbe au log principal
                    if log.log_type == 'CURVE' and curve_measurements:
                        for measurement in curve_measurements:
                            measurement.log = log
                            measurement.save()
                        statistics['curve_measurements'] += len(curve_measurements)
                        statistics['curve_logs'] += 1
                    
                    # Associer le scan laser au log principal
                    elif log.log_type == 'LASER2D' and laser_scans:
                        for scan in laser_scans:
                            scan.log = log
                            scan.save()
                        statistics['laser_logs'] += 1
                    
                    # Associer l'image au log principal
                    elif log.log_type == 'IMAGE' and images:
                        for image in images:
                            image.log = log
                            image.save()
                        statistics['image_logs'] += 1
                    
                    # Comptabiliser les logs textuels
                    elif log.log_type == 'TEXT':
                        statistics['text_logs'] += 1
                        
                except Exception as e:
                    logger.error(f"Erreur lors de la sauvegarde des données pour {channel_name}: {str(e)}")
                    logger.error(traceback.format_exc())
                    statistics['errors'] += 1
        
        # Marquer le fichier MDF comme traité
        if self.mdf_file:
            self.mdf_file.processed = True
            self.mdf_file.save()
            
        return statistics
