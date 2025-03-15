"""
Module pour parser les fichiers MDF (Measurement Data Format) de Vector.
Version corrigée pour gérer les canaux dupliqués dans les fichiers MDF.
"""
import os
import json
import tempfile
from datetime import datetime
import numpy as np
from asammdf import MDF
import logging
from PIL import Image
import io

from django.conf import settings
from django.core.files.base import ContentFile

from .models import RobotLog, CurveMeasurement, Laser2DScan, ImageData, MDFFile

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
                source="MDF Import",
                log_type="TEXT"
            )
            
            # Ajouter des métadonnées
            metadata = {
                'channel_name': channel_name,
                'sample_index': i,
                'unit': signal.unit if hasattr(signal, 'unit') else None,
                'comment': signal.comment if hasattr(signal, 'comment') else None,
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
            source="MDF Import",
            log_type="CURVE"
        )
        
        # Ajouter des métadonnées
        metadata = {
            'channel_name': channel_name,
            'samples_count': len(signal.samples),
            'unit': signal.unit if hasattr(signal, 'unit') else None,
            'start_time': signal.timestamps[0],
            'end_time': signal.timestamps[-1],
            'duration': signal.timestamps[-1] - signal.timestamps[0],
        }
        main_log.set_metadata_from_dict(metadata)
        
        # Générer un graphique de la courbe pour prévisualisation
        try:
            import matplotlib.pyplot as plt
            plt.figure(figsize=(10, 6))
            plt.plot(signal.timestamps, signal.samples)
            plt.title(f"Courbe: {channel_name}")
            plt.xlabel("Temps (s)")
            plt.ylabel(signal.unit if hasattr(signal, 'unit') else "Valeur")
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
            logger.error(f"Erreur lors de la génération du graphique pour {channel_name}: {e}")
        
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
            source="MDF Import",
            log_type="LASER2D"
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
            'angle_increment': angle_increment,
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
            logger.error(f"Erreur lors de la génération de la visualisation laser pour {channel_name}: {e}")
        
        return main_log, laser_scan
    
    def _process_image_data(self, channel_name, signal):
        """Traite un canal comme des données d'image"""
        # Créer un log principal pour cette image
        main_log = RobotLog(
            timestamp=datetime.fromtimestamp(signal.timestamps[0]),
            robot_id="MDF_Import",
            level="INFO",
            message=f"Image pour {channel_name}",
            source="MDF Import",
            log_type="IMAGE"
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
            
            # Utiliser la même image comme aperçu pour le log
            main_log.data_file.save(
                f"{channel_name}_image_preview.jpg",
                ContentFile(img_io.getvalue()),
                save=False
            )
            
            return main_log, image_obj
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'image pour {channel_name}: {e}")
            
            # En cas d'échec, créer une entrée de journal simple
            metadata = {
                'channel_name': channel_name,
                'data_size': len(signal.samples),
                'error': str(e)
            }
            main_log.set_metadata_from_dict(metadata)
            
            return main_log, None
    
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
                    source="MDF Import",
                    log_type="TEXT"
                )
                return [error_log], [], [], []
            
            group, index = location
            signal = self._mdf.get(channel_name, group=group, index=index)
            
            # Déterminer le type de données
            if self._is_text_event(channel_name, signal):
                logs = self._process_text_event(channel_name, signal)
                return logs, [], [], []
                
            elif self._is_curve_data(channel_name, signal):
                main_log, curve_measurements = self._process_curve_data(channel_name, signal)
                return [main_log], curve_measurements, [], []
                
            elif self._is_laser_data(channel_name, signal):
                main_log, laser_scan = self._process_laser_data(channel_name, signal)
                return [main_log], [], [laser_scan], []
                
            elif self._is_image_data(channel_name, signal):
                main_log, image = self._process_image_data(channel_name, signal)
                return [main_log], [], [], [image] if image else []
                
            else:
                # Canal non reconnu, créer un log simple
                log = RobotLog(
                    timestamp=datetime.fromtimestamp(signal.timestamps[0]),
                    robot_id="MDF_Import",
                    level="INFO",
                    message=f"Données non classifiées pour {channel_name}",
                    source="MDF Import",
                    log_type="TEXT"
                )
                
                # Ajouter des métadonnées
                metadata = {
                    'channel_name': channel_name,
                    'samples_count': len(signal.samples),
                    'data_type': str(signal.samples.dtype),
                    'unit': signal.unit if hasattr(signal, 'unit') else None,
                }
                log.set_metadata_from_dict(metadata)
                
                return [log], [], [], []
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement du canal {channel_name}: {e}")
            # Créer un log d'erreur
            error_log = RobotLog(
                timestamp=datetime.now(),
                robot_id="MDF_Import",
                level="ERROR",
                message=f"Erreur lors du traitement du canal {channel_name}: {e}",
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
        
        statistics = {
            'total_channels': 0,
            'text_logs': 0,
            'curve_logs': 0,
            'laser_logs': 0,
            'image_logs': 0,
            'curve_measurements': 0,
            'errors': 0
        }
        
        # Récupérer tous les canaux (version améliorée qui filtre les canaux de temps)
        channels = self.get_channels()
        statistics['total_channels'] = len(channels)
        
        # Traiter chaque canal
        for channel_name in channels:
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
                    logger.error(f"Erreur lors de la sauvegarde des données pour {channel_name}: {e}")
                    statistics['errors'] += 1
        
        # Marquer le fichier MDF comme traité
        if self.mdf_file:
            self.mdf_file.processed = True
            self.mdf_file.save()
            
        return statistics
