"""
Adaptateur pour la bibliothèque asammdf
"""
import re
import logging
import traceback

logger = logging.getLogger(__name__)

try:
    from asammdf import MDF as AsamMDF
    ASAMMDF_AVAILABLE = True
except ImportError:
    ASAMMDF_AVAILABLE = False
    logger.warning("La bibliothèque asammdf n'est pas installée. L'adaptateur ne sera pas disponible.")

class AsamMdfAdapter:
    """Adaptateur pour la bibliothèque asammdf"""
    
    def __init__(self):
        self.mdf = None
        self.file_path = None
        self.channel_map = {}  # Pour gérer les canaux en double
        
    @staticmethod
    def is_available():
        """Vérifie si asammdf est disponible"""
        return ASAMMDF_AVAILABLE
    
    def open(self, file_path):
        """Ouvre le fichier MDF avec asammdf"""
        try:
            self.file_path = file_path
            logger.info(f"Tentative d'ouverture avec asammdf: {file_path}")
            self.mdf = AsamMDF(file_path)
            
            # Construire un mappage pour les canaux en double
            self._build_channel_map()
            
            logger.info(f"Fichier MDF ouvert avec succès avec asammdf: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Échec de l'ouverture avec asammdf: {str(e)}")
            logger.error(traceback.format_exc())
            self.mdf = None
            return False
    
    def close(self):
        """Ferme le fichier MDF"""
        if self.mdf:
            self.mdf.close()
        self.mdf = None
        self.channel_map = {}
        logger.info("Fichier MDF fermé (asammdf)")
    
    def get_version(self):
        """Récupère la version du fichier MDF"""
        if self.mdf:
            return self.mdf.version
        return None
    
    def _build_channel_map(self):
        """Construit un mappage pour gérer les canaux en double"""
        if not self.mdf:
            return
        
        # Créer un dictionnaire pour mapper les noms de canaux aux tuples (groupe, index)
        # Ce sera utile pour les canaux qui apparaissent plusieurs fois
        self.channel_map = {}
        
        for name, occurrences in self.mdf.channels_db.items():
            if len(occurrences) == 1:
                # Canal unique, stocker le premier (et unique) tuple (groupe, index)
                self.channel_map[name] = occurrences[0]
            else:
                # Canal dupliqué, nous devons choisir une occurrence
                # Par défaut, prenons la première occurrence
                self.channel_map[name] = occurrences[0]
                
                # Créer également des entrées avec des suffixes uniques pour chaque occurrence
                for i, (group, index) in enumerate(occurrences):
                    unique_name = f"{name}_g{group}_i{index}"
                    self.channel_map[unique_name] = (group, index)
                    
                logger.info(f"Canal dupliqué détecté: {name} avec {len(occurrences)} occurrences. "
                           f"Des noms uniques ont été générés: {name}_g*_i*")
    
    def get_channels(self):
        """Retourne la liste des canaux disponibles dans le fichier MDF"""
        channels = []
        if not self.mdf:
            return channels
        
        # Récupérer les canaux avec asammdf, en utilisant le mappage
        # Pour éviter les doublons, nous utilisons les clés du channel_map
        for channel in self.channel_map.keys():
            # Exclure les noms générés avec des suffixes _g*_i* si le canal original est présent
            if not re.search(r'_g\d+_i\d+$', channel) or channel.split('_g')[0] not in self.channel_map:
                channels.append(channel)
        
        return channels
    
    def get_channel_info(self, channel_name):
        """Retourne les informations sur un canal spécifique"""
        if not self.mdf or not self.channel_map:
            return None
            
        try:
            # Obtenir les infos avec asammdf
            if channel_name in self.channel_map:
                group, index = self.channel_map[channel_name]
                signal = self.mdf.get(channel_name, group=group, index=index)
                return {
                    'name': channel_name,
                    'unit': signal.unit if hasattr(signal, 'unit') else '',
                    'comment': signal.comment if hasattr(signal, 'comment') else '',
                    'samples_count': len(signal.samples) if hasattr(signal, 'samples') else 0,
                    'data_type': str(signal.samples.dtype) if hasattr(signal, 'samples') else '',
                }
            else:
                logger.warning(f"Canal {channel_name} non trouvé dans le mappage de canaux")
                return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des infos du canal {channel_name}: {str(e)}")
            logger.error(traceback.format_exc())
            return None
    
    def get_channel_data_and_timestamps(self, channel_name):
        """Récupère les données et timestamps d'un canal"""
        if not self.mdf or not self.channel_map:
            return None, None
        
        try:
            # Utiliser le mappage pour obtenir le groupe et l'index
            if channel_name in self.channel_map:
                group, index = self.channel_map[channel_name]
                signal = self.mdf.get(channel_name, group=group, index=index)
                return signal.samples, signal.timestamps
            else:
                logger.error(f"Canal {channel_name} non trouvé dans le mappage de canaux")
                raise ValueError(f"Canal {channel_name} non trouvé dans le mappage de canaux")
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données avec asammdf pour {channel_name}: {str(e)}")
            logger.error(traceback.format_exc())
            return None, None
    
    def get_unit_and_desc(self, channel_name):
        """Récupère l'unité et la description d'un canal"""
        if not self.mdf or not self.channel_map:
            return {'unit': '', 'description': ''}
        
        try:
            if channel_name in self.channel_map:
                group, index = self.channel_map[channel_name]
                signal = self.mdf.get(channel_name, group=group, index=index)
                return {
                    'unit': signal.unit if hasattr(signal, 'unit') else '',
                    'description': signal.comment if hasattr(signal, 'comment') else ''
                }
            else:
                return {'unit': '', 'description': ''}
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'unité et la description pour {channel_name}: {str(e)}")
            return {'unit': '', 'description': ''}
    
    def is_channel_duplicated(self, channel_name):
        """Vérifie si un canal est dupliqué dans le fichier MDF"""
        if not self.mdf:
            return False
        
        # Vérifier si le canal est dans channels_db et s'il a plusieurs occurrences
        return channel_name in self.mdf.channels_db and len(self.mdf.channels_db[channel_name]) > 1
    
    def get_duplicated_channel_names(self, original_name):
        """Retourne les noms uniques générés pour un canal dupliqué"""
        if not self.mdf or not self.channel_map:
            return []
        
        # Rechercher les canaux générés avec le préfixe original_name
        duplicated_names = []
        for channel_name in self.channel_map.keys():
            if re.match(f"^{re.escape(original_name)}_g\\d+_i\\d+$", channel_name):
                duplicated_names.append(channel_name)
        
        return duplicated_names
