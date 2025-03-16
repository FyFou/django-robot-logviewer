"""
Module pour parser les fichiers MDF (Measurement Data Format) de Vector.
Version améliorée pour gérer les canaux dupliqués et les données CAN.
"""
import os
import json
import tempfile
import binascii
from datetime import datetime
import numpy as np
from asammdf import MDF
import logging
from PIL import Image
import io

from django.conf import settings
from django.core.files.base import ContentFile

from .models import RobotLog, CurveMeasurement, Laser2DScan, ImageData, MDFFile, CANMessage, CANSignal, LogGroup
from .can_parser import DBCParser, extract_can_messages_from_mdf

logger = logging.getLogger(__name__)

class MDFParser:
    """Classe pour parser et traiter les fichiers MDF"""
    
    def __init__(self, file_path, mdf_file_obj=None):
        """
        Initialise le parser MDF
        
        Args:
            file_path: Chemin vers le fichier MDF
            mdf_file_obj: Instance de MDFFile liée au fichier
        """
        self.file_path = file_path
        self.mdf_file = mdf_file_obj
        self._mdf = None
        self._dbc_parser = None
        self._log_group = None
        
    def open(self):
        """Ouvre le fichier MDF"""
        try:
            self._mdf = MDF(self.file_path)
            if self.mdf_file:
                self.mdf_file.mdf_version = f"MDF {self._mdf.version}"
                self.mdf_file.save()
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'ouverture du fichier MDF: {e}")
            return False
    
    def close(self):
        """Ferme le fichier MDF"""
        if self._mdf:
            self._mdf.close()
            self._mdf = None
    
    def initialize_dbc_parser(self, dbc_file):
        """Initialise le parseur DBC si un fichier est fourni"""
        try:
            if dbc_file and dbc_file.file:
                self._dbc_parser = DBCParser(dbc_file.file.path)
                logger.info(f"Parseur DBC initialisé avec le fichier {dbc_file.name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du parseur DBC: {e}")
            return False
    
    def get_channels(self):
        """Retourne la liste des canaux disponibles dans le fichier MDF"""
        if not self._mdf:
            if not self.open():
                return []
        
        # Filtrer les canaux dupliqués pour n'avoir que les noms uniques
        unique_channels = []
        seen_channels = set()
        
        for channel_name in self._mdf.channels_db.keys():
            # Ignorer les canaux de temps pour éviter les erreurs
            if channel_name.lower() in ('time', 'timestamp'):
                continue
            
            if channel_name not in seen_channels:
                unique_channels.append(channel_name)
                seen_channels.add(channel_name)
        
        return unique_channels
    
    def _find_channel_location(self, channel_name):
        """
        Trouve la localisation (groupe, index) d'un canal dans le fichier MDF.
        
        Args:
            channel_name: Nom du canal à trouver
            
        Returns:
            Tuple (group, index) ou None si non trouvé
        """
        if channel_name in self._mdf.channels_db:
            # Prendre la première occurrence du canal
            return self._mdf.channels_db[channel_name][0]
        return None
    
    def get_channel_info(self, channel_name):
        """Retourne les informations sur un canal spécifique"""
        if not self._mdf:
            if not self.open():
                return None
                
        try:
            # Trouver la localisation correcte du canal
            location = self._find_channel_location(channel_name)
            if location:
                group, index = location
                signal = self._mdf.get(channel_name, group=group, index=index)
                return {
                    'name': channel_name,
                    'unit': signal.unit if hasattr(signal, 'unit') else '',
                    'comment': signal.comment if hasattr(signal, 'comment') else '',
                    'samples_count': len(signal.samples) if hasattr(signal, 'samples') else 0,
                    'data_type': str(signal.samples.dtype) if hasattr(signal, 'samples') else '',
                }
            else:
                logger.error(f"Canal {channel_name} non trouvé dans le fichier MDF")
                return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des infos du canal {channel_name}: {e}")
            return None
    
    # Fonctions de détection du type de canal
    from .mdf_detector import (
        _is_text_event, _is_curve_data, _is_laser_data, 
        _is_image_data, _is_can_data
    )
    
    # Fonctions de traitement des différents types de canaux
    from .mdf_processors import (
        _process_text_event, _process_curve_data, _process_laser_data,
        _process_image_data, _process_can_data
    )
    
    def process_channel(self, channel_name):
        """
        Traite un canal spécifique du fichier MDF
        
        Args:
            channel_name: Nom du canal à traiter
            
        Returns:
            Tuple contenant (logs, curve_measurements, laser_scans, images, can_messages)
        """
        if not self._mdf:
            if not self.open():
                return [], [], [], [], []
        
        try:
            # Trouver la localisation correcte du canal
            location = self._find_channel_location(channel_name)
            if not location:
                logger.error(f"Canal {channel_name} non trouvé dans le fichier MDF")
                # Créer un log d'erreur
                error_log = RobotLog(
                    timestamp=datetime.now(),
                    robot_id="MDF_Import",
                    level="ERROR",
                    message=f"Canal {channel_name} non trouvé dans le fichier MDF",
                    source=f"MDF Import: {self.mdf_file.name if self.mdf_file else 'Unknown'}",
                    log_type="TEXT",
                    group=self._log_group  # Assignation au groupe
                )
                return [error_log], [], [], [], []
            
            group, index = location
            signal = self._mdf.get(channel_name, group=group, index=index)
            
            # Déterminer le type de données
            if self._is_text_event(channel_name, signal):
                logs = self._process_text_event(channel_name, signal)
                # Associer les logs au groupe
                for log in logs:
                    log.group = self._log_group
                return logs, [], [], [], []
                
            elif self._is_curve_data(channel_name, signal):
                main_log, curve_measurements = self._process_curve_data(channel_name, signal)
                main_log.group = self._log_group  # Assignation au groupe
                return [main_log], curve_measurements, [], [], []
                
            elif self._is_laser_data(channel_name, signal):
                main_log, laser_scan = self._process_laser_data(channel_name, signal)
                main_log.group = self._log_group  # Assignation au groupe
                return [main_log], [], [laser_scan], [], []
                
            elif self._is_image_data(channel_name, signal):
                main_log, image = self._process_image_data(channel_name, signal)
                main_log.group = self._log_group  # Assignation au groupe
                return [main_log], [], [], [image] if image else [], []
                
            elif self._is_can_data(channel_name, signal):
                main_log, can_messages = self._process_can_data(channel_name, signal)
                main_log.group = self._log_group  # Assignation au groupe
                return [main_log], [], [], [], can_messages
                
            else:
                # Canal non reconnu, créer un log simple
                log = RobotLog(
                    timestamp=datetime.fromtimestamp(signal.timestamps[0]),
                    robot_id="MDF_Import",
                    level="INFO",
                    message=f"Données non classifiées pour {channel_name}",
                    source=f"MDF Import: {self.mdf_file.name if self.mdf_file else 'Unknown'}",
                    log_type="TEXT",
                    group=self._log_group  # Assignation au groupe
                )
                
                # Ajouter des métadonnées
                metadata = {
                    'channel_name': channel_name,
                    'samples_count': len(signal.samples),
                    'data_type': str(signal.samples.dtype),
                    'unit': signal.unit if hasattr(signal, 'unit') else None,
                }
                log.set_metadata_from_dict(metadata)
                
                return [log], [], [], [], []
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement du canal {channel_name}: {e}")
            # Créer un log d'erreur
            error_log = RobotLog(
                timestamp=datetime.now(),
                robot_id="MDF_Import",
                level="ERROR",
                message=f"Erreur lors du traitement du canal {channel_name}: {e}",
                source=f"MDF Import: {self.mdf_file.name if self.mdf_file else 'Unknown'}",
                log_type="TEXT",
                group=self._log_group  # Assignation au groupe
            )
            return [error_log], [], [], [], []
    
    def process_file(self, dbc_file=None, log_group=None):
        """
        Traite l'ensemble du fichier MDF et importe tous les canaux
        
        Args:
            dbc_file: Fichier DBC optionnel pour décoder les messages CAN
            log_group: Groupe de logs auquel associer les logs générés
            
        Returns:
            Dictionnaire contenant des statistiques sur les données importées
        """
        if not self._mdf:
            if not self.open():
                return {'error': 'Impossible d\'ouvrir le fichier MDF'}
        
        # Stocker le groupe de logs pour l'utiliser lors du traitement
        self._log_group = log_group
        
        # Initialiser le parseur DBC si un fichier est fourni
        if dbc_file:
            self.initialize_dbc_parser(dbc_file)
            # Associer le fichier DBC au fichier MDF
            if self.mdf_file:
                self.mdf_file.dbc_file = dbc_file
                self.mdf_file.save()
        
        statistics = {
            'total_channels': 0,
            'text_logs': 0,
            'curve_logs': 0,
            'laser_logs': 0,
            'image_logs': 0,
            'can_logs': 0,
            'curve_measurements': 0,
            'can_messages': 0,
            'can_signals': 0,
            'errors': 0
        }
        
        # Récupérer tous les canaux (version améliorée qui filtre les canaux de temps)
        channels = self.get_channels()
        statistics['total_channels'] = len(channels)
        
        # Traiter chaque canal
        for channel_name in channels:
            logs, curve_measurements, laser_scans, images, can_messages = self.process_channel(channel_name)
            
            # Sauvegarder les logs
            for log in logs:
                try:
                    # Le log est déjà associé au groupe dans process_channel
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
                    
                    # Associer les messages CAN au log principal
                    elif log.log_type == 'CAN' and can_messages:
                        for can_message in can_messages:
                            can_message.log = log
                            can_message.save()
                            
                            # Si le message a des signaux décodés, les enregistrer
                            if hasattr(can_message, 'signals_data') and can_message.signals_data:
                                for name, signal_info in can_message.signals_data.items():
                                    signal = CANSignal(
                                        can_message=can_message,
                                        name=name,
                                        value=signal_info['value'] if isinstance(signal_info, dict) else signal_info,
                                        unit=signal_info.get('unit', '') if isinstance(signal_info, dict) else ''
                                    )
                                    signal.save()
                                    statistics['can_signals'] += 1
                        
                        statistics['can_messages'] += len(can_messages)
                        statistics['can_logs'] += 1
                    
                    # Comptabiliser les logs textuels
                    elif log.log_type == 'TEXT':
                        statistics['text_logs'] += 1
                        
                except Exception as e:
                    logger.error(f"Erreur lors de la sauvegarde des données pour {channel_name}: {e}")
                    statistics['errors'] += 1
        
        # Marquer le fichier MDF comme traité
        if self.mdf_file:
            self.mdf_file.processed = True
            if log_group:
                self.mdf_file.log_group = log_group
            self.mdf_file.save()
            
        return statistics
