"""
Module pour parser les fichiers MDF (Measurement Data Format) pour l'application django-robot-logviewer.
Cette version utilise la bibliothèque mdfreader avec repli sur asammdf pour les formats non supportés.
"""
import os
import json
import tempfile
from datetime import datetime
import numpy as np
import logging
from PIL import Image
import io
import traceback

from django.conf import settings
from django.core.files.base import ContentFile

# Import des deux bibliothèques avec gestion d'erreur
try:
    from mdfreader import Mdf as MdfReader
    MDFREADER_AVAILABLE = True
except ImportError:
    MDFREADER_AVAILABLE = False

try:
    from asammdf import MDF as AsamMDF
    ASAMMDF_AVAILABLE = True
except ImportError:
    ASAMMDF_AVAILABLE = False

from .models import RobotLog, CurveMeasurement, Laser2DScan, ImageData, MDFFile

logger = logging.getLogger(__name__)

class MDFParser:
    """Classe pour parser et traiter les fichiers MDF avec support mdfreader et asammdf"""
    
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
        self._parser_type = None  # 'mdfreader' ou 'asammdf'
        
    def open(self):
        """Ouvre le fichier MDF avec mdfreader ou asammdf"""
        # D'abord, essayer avec mdfreader
        if MDFREADER_AVAILABLE:
            try:
                logger.info(f"Tentative d'ouverture avec mdfreader: {self.file_path}")
                self._mdf = MdfReader(self.file_path, no_data_loading=True)
                self._parser_type = 'mdfreader'
                
                if self.mdf_file:
                    self.mdf_file.mdf_version = f"MDF {self._mdf.MDFVersionNumber}"
                    self.mdf_file.save()
                
                logger.info(f"Fichier MDF ouvert avec succès avec mdfreader: {self.file_path}")
                return True
            except Exception as e:
                logger.error(f"Échec de l'ouverture avec mdfreader: {str(e)}")
                logger.error(traceback.format_exc())
                # Continuer avec asammdf en cas d'échec
        
        # Ensuite, essayer avec asammdf si mdfreader a échoué
        if ASAMMDF_AVAILABLE:
            try:
                logger.info(f"Tentative d'ouverture avec asammdf: {self.file_path}")
                self._mdf = AsamMDF(self.file_path)
                self._parser_type = 'asammdf'
                
                if self.mdf_file:
                    self.mdf_file.mdf_version = f"MDF {self._mdf.version}"
                    self.mdf_file.save()
                
                logger.info(f"Fichier MDF ouvert avec succès avec asammdf: {self.file_path}")
                return True
            except Exception as e:
                logger.error(f"Échec de l'ouverture avec asammdf: {str(e)}")
                logger.error(traceback.format_exc())
        
        # Si nous arrivons ici, aucune des bibliothèques n'a pu ouvrir le fichier
        logger.error(f"Impossible d'ouvrir le fichier MDF avec mdfreader ou asammdf: {self.file_path}")
        return False
    
    def close(self):
        """Ferme le fichier MDF"""
        if self._mdf:
            if self._parser_type == 'asammdf':
                self._mdf.close()
            self._mdf = None
            logger.info(f"Fichier MDF fermé ({self._parser_type})")
            self._parser_type = None
    
    def get_channels(self):
        """Retourne la liste des canaux disponibles dans le fichier MDF"""
        if not self._mdf:
            if not self.open():
                return []
        
        channels = []
        
        if self._parser_type == 'mdfreader':
            # Récupérer les canaux avec mdfreader
            for master in self._mdf.masterChannelList:
                for channel in self._mdf.masterChannelList[master]:
                    if channel not in channels:
                        channels.append(channel)
        else:  # asammdf
            # Récupérer les canaux avec asammdf
            for channel in self._mdf.channels_db:
                if channel not in channels:
                    channels.append(channel)
        
        logger.info(f"Nombre de canaux trouvés: {len(channels)}")
        return channels
    
    def get_channel_info(self, channel_name):
        """Retourne les informations sur un canal spécifique"""
        if not self._mdf:
            if not self.open():
                return None
                
        try:
            if self._parser_type == 'mdfreader':
                # Obtenir les infos avec mdfreader
                data = self._mdf.get_channel_data(channel_name)
                unit = self._mdf.get_channel_unit(channel_name)
                description = self._mdf.get_channel_desc(channel_name)
                
                return {
                    'name': channel_name,
                    'unit': unit if unit else '',
                    'comment': description if description else '',
                    'samples_count': len(data) if data is not None else 0,
                    'data_type': str(data.dtype) if hasattr(data, 'dtype') else '',
                }
            else:  # asammdf
                # Obtenir les infos avec asammdf
                signal = self._mdf.get(channel_name)
                return {
                    'name': channel_name,
                    'unit': signal.unit if hasattr(signal, 'unit') else '',
                    'comment': signal.comment if hasattr(signal, 'comment') else '',
                    'samples_count': len(signal.samples) if hasattr(signal, 'samples') else 0,
                    'data_type': str(signal.samples.dtype) if hasattr(signal, 'samples') else '',
                }
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des infos du canal {channel_name}: {str(e)}")
            logger.error(traceback.format_exc())
            return None
    
    def _is_text_event(self, channel_name, data):
        """Détermine si un canal contient des événements textuels"""
        # Vérification par le nom du canal
        if 'event' in channel_name.lower() or 'message' in channel_name.lower() or 'text' in channel_name.lower():
            return True
        
        # Vérification par le type de données
        if hasattr(data, 'dtype') and data.dtype.kind in ['S', 'U']:
            return True
            
        return False
    
    def _is_curve_data(self, channel_name, data):
        """Détermine si un canal contient des données de courbe"""
        # Vérification si c'est une série de valeurs numériques
        if (hasattr(data, 'dtype') and 
            data.dtype.kind in ['i', 'u', 'f'] and 
            hasattr(data, '__len__') and len(data) > 1):
            return True
            
        return False
    
    def _is_laser_data(self, channel_name, data):
        """Détermine si un canal contient des données laser 2D"""
        # Vérification par le nom du canal
        if 'laser' in channel_name.lower() or 'scan' in channel_name.lower() or 'lidar' in channel_name.lower():
            # Vérification des données (tableau de distances)
            if (hasattr(data, 'dtype') and 
                data.dtype.kind in ['i', 'u', 'f'] and 
                hasattr(data, '__len__') and len(data) > 10):
                return True
                
        return False
    
    def _is_image_data(self, channel_name, data):
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
    
    def _process_text_event(self, channel_name, data, timestamps):
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
            }
            
            if self._parser_type == 'mdfreader':
                metadata.update({
                    'unit': self._mdf.get_channel_unit(channel_name),
                    'description': self._mdf.get_channel_desc(channel_name),
                })
            
            log.set_metadata_from_dict(metadata)
            logs.append(log)
            
        return logs
    
    def _get_unit_and_desc(self, channel_name):
        """Récupère l'unité et la description d'un canal selon le parser utilisé"""
        if self._parser_type == 'mdfreader':
            return {
                'unit': self._mdf.get_channel_unit(channel_name),
                'description': self._mdf.get_channel_desc(channel_name)
            }
        else:  # asammdf
            try:
                signal = self._mdf.get(channel_name)
                return {
                    'unit': signal.unit if hasattr(signal, 'unit') else '',
                    'description': signal.comment if hasattr(signal, 'comment') else ''
                }
            except:
                return {'unit': '', 'description': ''}
    
    def _process_curve_data(self, channel_name, data, timestamps):
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
        
        # Récupérer l'unité et la description
        channel_info = self._get_unit_and_desc(channel_name)
        
        # Ajouter des métadonnées
        metadata = {
            'channel_name': channel_name,
            'samples_count': len(data),
            'unit': channel_info['unit'],
            'description': channel_info['description'],
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
            plt.ylabel(channel_info['unit'] or "Valeur")
            plt.grid(True)
            
            # Sauvegarder l'image dans un buffer
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='PNG')
            img_buffer.seek(0)
            plt.close()
            
            # Attacher l'image au log
            main_log.data_file.save(
                f"{channel_name}_preview.png",
                ContentFile(img_buffer.getvalue()),
                save=False
            )
        except Exception as e:
            logger.error(f"Erreur lors de la génération du graphique pour {channel_name}: {str(e)}")
            logger.error(traceback.format_exc())
        
        # Créer les mesures de courbe associées
        curve_measurements = []
        for i, (ts, value) in enumerate(zip(timestamps, data)):
            measurement = CurveMeasurement(
                timestamp=datetime.fromtimestamp(ts),
                sensor_name=channel_name,
                value=float(value) if hasattr(value, 'dtype') else float(value)
            )
            curve_measurements.append(measurement)
        
        return main_log, curve_measurements
    
    def _process_laser_data(self, channel_name, data, timestamps):
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
        
        # Récupérer l'unité et la description
        channel_info = self._get_unit_and_desc(channel_name)
        
        # Estimer les paramètres du laser (par défaut)
        angle_min = -np.pi / 2  # Par défaut, scan de 180 degrés
        angle_max = np.pi / 2
        angle_increment = np.pi / len(data)
        
        # Ajouter des métadonnées
        metadata = {
            'channel_name': channel_name,
            'points_count': len(data),
            'unit': channel_info['unit'] or 'm',
            'description': channel_info['description'],
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
                f"{channel_name}_laser_preview.png",
                ContentFile(img_buffer.getvalue()),
                save=False
            )
        except Exception as e:
            logger.error(f"Erreur lors de la génération de la visualisation laser pour {channel_name}: {str(e)}")
            logger.error(traceback.format_exc())
        
        return main_log, laser_scan
    
    def _process_image_data(self, channel_name, data, timestamps):
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
        
        # Récupérer l'unité et la description pour les métadonnées
        channel_info = self._get_unit_and_desc(channel_name)
        
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
                f"{channel_name}_image.jpg",
                ContentFile(img_io.getvalue()),
                save=False
            )
            
            # Utiliser la même image comme aperçu pour le log
            main_log.data_file.save(
                f"{channel_name}_image_preview.jpg",
                ContentFile(img_io.getvalue()),
                save=False
            )
            
            return main_log, image_obj
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'image pour {channel_name}: {str(e)}")
            logger.error(traceback.format_exc())
            
            # En cas d'échec, créer une entrée de journal simple
            metadata = {
                'channel_name': channel_name,
                'data_size': len(data),
                'unit': channel_info['unit'],
                'description': channel_info['description'],
                'error': str(e)
            }
            main_log.set_metadata_from_dict(metadata)
            
            return main_log, None
    
    def _get_channel_data_and_timestamps(self, channel_name):
        """Récupère les données et timestamps d'un canal en fonction du parser utilisé"""
        if self._parser_type == 'mdfreader':
            data = self._mdf.get_channel_data(channel_name)
            
            # Récupérer les timestamps du canal
            master_name = self._mdf.get_channel_master(channel_name)
            if master_name:
                timestamps = self._mdf.get_channel_data(master_name)
            else:
                # Si pas de master channel, créer des timestamps artificiels
                timestamps = np.arange(len(data))
                
            return data, timestamps
        else:  # asammdf
            signal = self._mdf.get(channel_name)
            return signal.samples, signal.timestamps
    
    def process_channel(self, channel_name):
        """
        Traite un canal spécifique du fichier MDF
        
        Args:
            channel_name: Nom du canal à traiter
            
        Returns:
            Tuple contenant (logs, curve_measurements, laser_scans, images)
        """
        if not self._mdf:
            if not self.open():
                return [], [], [], []
        
        try:
            # Récupérer les données et timestamps du canal
            data, timestamps = self._get_channel_data_and_timestamps(channel_name)
            
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
            
            # Déterminer le type de données
            if self._is_text_event(channel_name, data):
                logs = self._process_text_event(channel_name, data, timestamps)
                return logs, [], [], []
                
            elif self._is_curve_data(channel_name, data):
                main_log, curve_measurements = self._process_curve_data(channel_name, data, timestamps)
                return [main_log], curve_measurements, [], []
                
            elif self._is_laser_data(channel_name, data):
                main_log, laser_scan = self._process_laser_data(channel_name, data, timestamps)
                return [main_log], [], [laser_scan], []
                
            elif self._is_image_data(channel_name, data):
                main_log, image = self._process_image_data(channel_name, data, timestamps)
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
                
                # Récupérer l'unité et la description
                channel_info = self._get_unit_and_desc(channel_name)
                
                # Ajouter des métadonnées
                metadata = {
                    'channel_name': channel_name,
                    'samples_count': len(data),
                    'data_type': str(data.dtype) if hasattr(data, 'dtype') else str(type(data)),
                    'unit': channel_info['unit'],
                    'description': channel_info['description'],
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
        if not self._mdf:
            if not self.open():
                return {'error': 'Impossible d\'ouvrir le fichier MDF'}
        
        logger.info(f"Traitement du fichier MDF avec {self._parser_type}")
        
        statistics = {
            'total_channels': 0,
            'text_logs': 0,
            'curve_logs': 0,
            'laser_logs': 0,
            'image_logs': 0,
            'curve_measurements': 0,
            'errors': 0,
            'parser_used': self._parser_type
        }
        
        # Récupérer tous les canaux
        channels = self.get_channels()
        statistics['total_channels'] = len(channels)
        
        # Traiter chaque canal
        for channel_name in channels:
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
