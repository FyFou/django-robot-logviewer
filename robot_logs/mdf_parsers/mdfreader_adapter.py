"""
Adaptateur pour la bibliothèque mdfreader
"""
import numpy as np
import logging
import traceback

logger = logging.getLogger(__name__)

try:
    from mdfreader import Mdf as MdfReader
    MDFREADER_AVAILABLE = True
except ImportError:
    MDFREADER_AVAILABLE = False
    logger.warning("La bibliothèque mdfreader n'est pas installée. L'adaptateur ne sera pas disponible.")

class MdfReaderAdapter:
    """Adaptateur pour la bibliothèque mdfreader"""
    
    def __init__(self):
        self.mdf = None
        self.file_path = None
        
    @staticmethod
    def is_available():
        """Vérifie si mdfreader est disponible"""
        return MDFREADER_AVAILABLE
    
    def open(self, file_path):
        """Ouvre le fichier MDF avec mdfreader"""
        try:
            self.file_path = file_path
            logger.info(f"Tentative d'ouverture avec mdfreader: {file_path}")
            self.mdf = MdfReader(file_path, no_data_loading=True)
            logger.info(f"Fichier MDF ouvert avec succès avec mdfreader: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Échec de l'ouverture avec mdfreader: {str(e)}")
            logger.error(traceback.format_exc())
            self.mdf = None
            return False
    
    def close(self):
        """Ferme le fichier MDF"""
        self.mdf = None
        logger.info("Fichier MDF fermé (mdfreader)")
    
    def get_version(self):
        """Récupère la version du fichier MDF"""
        if self.mdf:
            return self.mdf.MDFVersionNumber
        return None
    
    def get_channels(self):
        """Retourne la liste des canaux disponibles dans le fichier MDF"""
        channels = []
        if not self.mdf:
            return channels
        
        # Récupérer les canaux
        for master in self.mdf.masterChannelList:
            for channel in self.mdf.masterChannelList[master]:
                if channel not in channels:
                    channels.append(channel)
        
        return channels
    
    def get_channel_info(self, channel_name):
        """Retourne les informations sur un canal spécifique"""
        if not self.mdf:
            return None
            
        try:
            # Obtenir les infos
            data = self.mdf.get_channel_data(channel_name)
            unit = self.mdf.get_channel_unit(channel_name)
            description = self.mdf.get_channel_desc(channel_name)
            
            return {
                'name': channel_name,
                'unit': unit if unit else '',
                'comment': description if description else '',
                'samples_count': len(data) if data is not None else 0,
                'data_type': str(data.dtype) if hasattr(data, 'dtype') else '',
            }
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des infos du canal {channel_name}: {str(e)}")
            logger.error(traceback.format_exc())
            return None
    
    def get_channel_data_and_timestamps(self, channel_name):
        """Récupère les données et timestamps d'un canal"""
        if not self.mdf:
            return None, None
        
        try:
            data = self.mdf.get_channel_data(channel_name)
            
            # Récupérer les timestamps du canal
            master_name = self.mdf.get_channel_master(channel_name)
            if master_name:
                timestamps = self.mdf.get_channel_data(master_name)
            else:
                # Si pas de master channel, créer des timestamps artificiels
                timestamps = np.arange(len(data))
                
            return data, timestamps
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données avec mdfreader pour {channel_name}: {str(e)}")
            logger.error(traceback.format_exc())
            return None, None
    
    def get_unit_and_desc(self, channel_name):
        """Récupère l'unité et la description d'un canal"""
        if not self.mdf:
            return {'unit': '', 'description': ''}
        
        try:
            return {
                'unit': self.mdf.get_channel_unit(channel_name),
                'description': self.mdf.get_channel_desc(channel_name)
            }
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'unité et la description pour {channel_name}: {str(e)}")
            return {'unit': '', 'description': ''}
