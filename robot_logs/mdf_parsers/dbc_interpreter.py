"""
Module pour interpréter les fichiers DBC et décoder les trames CAN
"""
import logging
import traceback

logger = logging.getLogger(__name__)

try:
    import cantools
    CANTOOLS_AVAILABLE = True
except ImportError:
    CANTOOLS_AVAILABLE = False
    logger.warning("La bibliothèque cantools n'est pas installée. Le décodage DBC ne sera pas disponible.")

class DBCInterpreter:
    """Classe pour charger et interpréter les fichiers DBC"""
    
    def __init__(self):
        self.dbc_databases = {}  # Stocke les bases DBC par ID de fichier
        
    @staticmethod
    def is_available():
        """Vérifie si cantools est disponible"""
        return CANTOOLS_AVAILABLE
    
    def load_dbc_file(self, dbc_file_path, dbc_id=None):
        """
        Charge un fichier DBC
        
        Args:
            dbc_file_path: Chemin vers le fichier DBC
            dbc_id: Identifiant optionnel pour stocker la base DBC
            
        Returns:
            True si le chargement a réussi, False sinon
        """
        if not CANTOOLS_AVAILABLE:
            logger.error("La bibliothèque cantools n'est pas installée. Impossible de charger le fichier DBC.")
            return False
        
        try:
            db = cantools.database.load_file(dbc_file_path)
            
            # Stocker la base DBC avec l'ID fourni ou le chemin du fichier
            key = dbc_id if dbc_id is not None else dbc_file_path
            self.dbc_databases[key] = db
            
            logger.info(f"Fichier DBC chargé avec succès: {dbc_file_path}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors du chargement du fichier DBC {dbc_file_path}: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def get_dbc_database(self, dbc_id):
        """
        Récupère une base DBC par son ID
        
        Args:
            dbc_id: Identifiant de la base DBC
            
        Returns:
            La base DBC correspondante ou None si non trouvée
        """
        return self.dbc_databases.get(dbc_id)
    
    def decode_frame(self, dbc_id, frame_id, frame_data):
        """
        Décode une trame CAN en utilisant une base DBC
        
        Args:
            dbc_id: Identifiant de la base DBC à utiliser
            frame_id: Identifiant de la trame CAN (entier)
            frame_data: Données de la trame (bytes ou liste d'octets)
            
        Returns:
            Un dictionnaire avec le message décodé ou None en cas d'erreur
        """
        if not CANTOOLS_AVAILABLE:
            return None
        
        db = self.get_dbc_database(dbc_id)
        if not db:
            logger.error(f"Base DBC {dbc_id} non trouvée")
            return None
        
        try:
            # Convertir frame_id en entier si c'est une chaîne hexadécimale
            if isinstance(frame_id, str) and frame_id.startswith('0x'):
                frame_id = int(frame_id, 16)
            
            # Convertir frame_data en bytes si nécessaire
            if not isinstance(frame_data, bytes):
                if isinstance(frame_data, list):
                    frame_data = bytes(frame_data)
                elif isinstance(frame_data, str):
                    # Si c'est une chaîne d'octets en hexadécimal séparés par des espaces
                    if ' ' in frame_data:
                        frame_data = bytes([int(x, 16) for x in frame_data.split()])
                    # Si c'est une chaîne hex sans espaces
                    else:
                        frame_data = bytes.fromhex(frame_data.replace('0x', ''))
            
            # Chercher le message dans la base DBC
            try:
                message = db.get_message_by_frame_id(frame_id)
            except KeyError:
                # Message non trouvé dans la base DBC
                logger.debug(f"Message avec ID {frame_id} non trouvé dans la base DBC {dbc_id}")
                return None
            
            # Décoder la trame
            decoded = message.decode(frame_data)
            
            # Ajouter des informations supplémentaires
            result = {
                'message_name': message.name,
                'signals': decoded
            }
            
            return result
        except Exception as e:
            logger.error(f"Erreur lors du décodage de la trame CAN: {str(e)}")
            logger.error(traceback.format_exc())
            return None
    
    def get_all_message_ids(self, dbc_id):
        """
        Récupère tous les IDs de message définis dans une base DBC
        
        Args:
            dbc_id: Identifiant de la base DBC
            
        Returns:
            Une liste de tuples (frame_id, nom_du_message) ou None en cas d'erreur
        """
        db = self.get_dbc_database(dbc_id)
        if not db:
            return None
        
        try:
            return [(message.frame_id, message.name) for message in db.messages]
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des IDs de message: {str(e)}")
            return None
    
    def get_message_info(self, dbc_id, frame_id):
        """
        Récupère les informations sur un message spécifique dans une base DBC
        
        Args:
            dbc_id: Identifiant de la base DBC
            frame_id: Identifiant de la trame CAN
            
        Returns:
            Un dictionnaire avec les informations sur le message ou None en cas d'erreur
        """
        db = self.get_dbc_database(dbc_id)
        if not db:
            return None
        
        try:
            # Convertir frame_id en entier si c'est une chaîne hexadécimale
            if isinstance(frame_id, str) and frame_id.startswith('0x'):
                frame_id = int(frame_id, 16)
            
            message = db.get_message_by_frame_id(frame_id)
            
            # Extraire les informations sur les signaux
            signals = []
            for signal in message.signals:
                signals.append({
                    'name': signal.name,
                    'start': signal.start,
                    'length': signal.length,
                    'byte_order': signal.byte_order,
                    'scale': signal.scale,
                    'offset': signal.offset,
                    'minimum': signal.minimum,
                    'maximum': signal.maximum,
                    'unit': signal.unit,
                    'comment': signal.comment
                })
            
            return {
                'name': message.name,
                'frame_id': message.frame_id,
                'is_extended_frame': message.is_extended_frame,
                'length': message.length,
                'comment': message.comment,
                'signals': signals
            }
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des informations sur le message: {str(e)}")
            return None
