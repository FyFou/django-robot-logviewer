"""
Module pour parser et décoder les messages CAN à l'aide de fichiers DBC.
"""
import logging
import binascii
import struct
import re
import io

logger = logging.getLogger(__name__)

class DBCParser:
    """Classe pour parser les fichiers DBC et décoder les messages CAN"""
    
    def __init__(self, dbc_file_path):
        """
        Initialise le parser DBC
        
        Args:
            dbc_file_path: Chemin vers le fichier DBC
        """
        self.dbc_file_path = dbc_file_path
        self.messages = {}  # {can_id: MessageInfo}
        self.load_dbc()
        
    def load_dbc(self):
        """Charge et parse le fichier DBC"""
        # Vérification de la disponibilité de cantools
        try:
            import cantools
            self.use_cantools = True
            self.db = cantools.database.load_file(self.dbc_file_path)
            logger.info(f"Fichier DBC chargé avec cantools: {len(self.db.messages)} messages")
            return True
        except ImportError:
            logger.warning("La bibliothèque cantools n'est pas disponible. Utilisation du parser DBC de base.")
            self.use_cantools = False
            
        try:
            # Parser de base si cantools n'est pas disponible
            with open(self.dbc_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Parser les définitions de messages
            message_patterns = r'BO_ (\d+) ([^:]+): (\d+) ([^\n]+)'
            for match in re.finditer(message_patterns, content):
                can_id, name, dlc, sender = match.groups()
                can_id = int(can_id)
                dlc = int(dlc)
                name = name.strip()
                sender = sender.strip()
                
                self.messages[can_id] = {
                    'name': name,
                    'length': dlc,
                    'sender': sender,
                    'signals': {}
                }
            
            # Parser les définitions de signaux (simplifié)
            signal_pattern = r'SG_ ([^ ]+) : (\d+)\|(\d+)@(\d+)([+-]) \(([^,]+),([^)]+)\) \[([^|]*)\|([^]]*)\] "([^"]*)"'
            current_message_id = None
            
            for line in content.split('\n'):
                if line.startswith('BO_'):
                    # Nouvelle définition de message, extraire l'ID
                    try:
                        current_message_id = int(line.split(' ')[1])
                    except:
                        current_message_id = None
                        
                elif line.strip().startswith('SG_') and current_message_id and current_message_id in self.messages:
                    # Définition de signal
                    try:
                        matches = re.search(signal_pattern, line)
                        if matches:
                            name, start_bit, length, byte_order, sign, factor, offset, min_val, max_val, unit = matches.groups()
                            
                            self.messages[current_message_id]['signals'][name] = {
                                'start_bit': int(start_bit),
                                'length': int(length),
                                'byte_order': int(byte_order),
                                'sign': sign,
                                'factor': float(factor),
                                'offset': float(offset),
                                'min': float(min_val) if min_val else None,
                                'max': float(max_val) if max_val else None,
                                'unit': unit
                            }
                    except Exception as e:
                        logger.error(f"Erreur lors du parsing du signal: {line} - {e}")
            
            logger.info(f"Fichier DBC chargé avec le parser de base: {len(self.messages)} messages")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement du fichier DBC: {e}")
            return False
    
    def get_message_by_id(self, can_id):
        """
        Récupère les informations d'un message par son ID CAN
        
        Args:
            can_id: ID du message CAN (entier ou hexadécimal)
            
        Returns:
            Dictionnaire d'informations sur le message ou None si non trouvé
        """
        # Convertir l'ID en entier si c'est une chaîne hexadécimale
        if isinstance(can_id, str):
            if can_id.startswith('0x'):
                can_id = int(can_id, 16)
            else:
                try:
                    can_id = int(can_id)
                except ValueError:
                    return None
        
        if self.use_cantools:
            try:
                return self.db.get_message_by_frame_id(can_id)
            except:
                return None
        else:
            return self.messages.get(can_id)
    
    def decode_message(self, can_id, data):
        """
        Décode un message CAN
        
        Args:
            can_id: ID du message CAN (entier ou hexadécimal)
            data: Données binaires du message (bytes ou str hex)
            
        Returns:
            Tuple (message_name, signaux_décodés) ou (None, None) si échec
        """
        # Convertir l'ID en entier si c'est une chaîne hexadécimale
        if isinstance(can_id, str):
            if can_id.startswith('0x'):
                can_id = int(can_id, 16)
            else:
                try:
                    can_id = int(can_id)
                except ValueError:
                    return None, {}
        
        # Convertir les données en bytes si c'est une chaîne hexadécimale
        if isinstance(data, str):
            try:
                data = binascii.unhexlify(data.replace(' ', ''))
            except:
                logger.error(f"Impossible de convertir les données hexadécimales: {data}")
                return None, {}
        
        if self.use_cantools:
            try:
                message = self.db.get_message_by_frame_id(can_id)
                decoded = message.decode(data)
                return message.name, decoded
            except Exception as e:
                logger.error(f"Erreur lors du décodage du message CAN {can_id}: {e}")
                return None, {}
        else:
            # Décodage basique sans cantools (limité)
            message_info = self.messages.get(can_id)
            if not message_info:
                return None, {}
            
            try:
                # Conversion des données en entier 64 bits pour faciliter l'extraction des bits
                data_int = int.from_bytes(data, byteorder='little')
                
                decoded = {}
                for signal_name, signal_info in message_info['signals'].items():
                    # Extraction des bits (très simplifié et incomplet)
                    start_bit = signal_info['start_bit']
                    length = signal_info['length']
                    
                    # Extraction simple de bits consécutifs
                    mask = (1 << length) - 1
                    raw_value = (data_int >> start_bit) & mask
                    
                    # Application du facteur et offset
                    value = raw_value * signal_info['factor'] + signal_info['offset']
                    
                    # Ajout au dictionnaire de signaux décodés
                    decoded[signal_name] = {
                        'value': value,
                        'unit': signal_info['unit']
                    }
                
                return message_info['name'], decoded
            except Exception as e:
                logger.error(f"Erreur lors du décodage basique du message CAN {can_id}: {e}")
                return None, {}

def extract_can_messages_from_mdf(mdf_file, can_channel_name):
    """
    Extrait les messages CAN d'un canal dans un fichier MDF.
    
    Args:
        mdf_file: Instance de MDF (asammdf)
        can_channel_name: Nom du canal contenant les données CAN
        
    Returns:
        Liste de tuples (timestamp, can_id, data)
    """
    try:
        # Vérifier si le canal existe
        if can_channel_name not in mdf_file.channels_db:
            logger.error(f"Canal CAN {can_channel_name} non trouvé dans le fichier MDF")
            return []
        
        # Extraire le signal
        channel_group, channel_index = mdf_file.channels_db[can_channel_name][0]
        signal = mdf_file.get(can_channel_name, group=channel_group, index=channel_index)
        
        # Préparer la liste de messages
        messages = []
        
        # Parser le canal selon le format
        for i, (timestamp, data) in enumerate(zip(signal.timestamps, signal.samples)):
            try:
                # Format spécifique au canal, adapter selon les besoins
                # Exemple : canal contenant des strings de format "ID:DATA"
                if isinstance(data, (bytes, bytearray)):
                    # Décodage basique d'un message CAN binaire
                    # Format: [ID (4 bytes)][DLC (1 byte)][DATA (8 bytes)]
                    if len(data) >= 13:
                        can_id = int.from_bytes(data[0:4], byteorder='little')
                        dlc = data[4]
                        can_data = data[5:5+dlc]
                        messages.append((timestamp, can_id, can_data))
                elif isinstance(data, str):
                    # Format texte "ID:DATA" (adapter selon format réel)
                    if ':' in data:
                        id_str, data_str = data.split(':', 1)
                        can_id = int(id_str.strip(), 16)
                        can_data = binascii.unhexlify(data_str.strip().replace(' ', ''))
                        messages.append((timestamp, can_id, can_data))
            except Exception as e:
                logger.error(f"Erreur lors du parsing du message CAN à l'index {i}: {e}")
        
        return messages
    
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction des messages CAN du canal {can_channel_name}: {e}")
        return []
