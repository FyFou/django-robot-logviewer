from django.core.management.base import BaseCommand
from robot_logs.models import RobotLog, CurveMeasurement, Laser2DScan, ImageData, MDFFile
from django.utils import timezone
from django.core.files.base import ContentFile
import random
import os
import numpy as np
import tempfile
from datetime import timedelta
import io
import matplotlib.pyplot as plt
from PIL import Image

class Command(BaseCommand):
    help = 'Génère des logs de test et optionnellement des fichiers MDF'

    def add_arguments(self, parser):
        parser.add_argument('count', type=int, help='Nombre de logs à générer')
        parser.add_argument('--mdf', action='store_true', help='Générer également des fichiers MDF de test')
        parser.add_argument('--mdf-count', type=int, default=2, help='Nombre de fichiers MDF à générer')

    def handle(self, *args, **options):
        count = options['count']
        generate_mdf = options.get('mdf', False)
        mdf_count = options.get('mdf_count', 2)
        
        robot_ids = ['R2D2', 'C3PO', 'BB8', 'K2SO', 'RobotX']
        log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        log_types = ['TEXT', 'CURVE', 'LASER2D', 'IMAGE']
        sources = ['sensors', 'motion', 'vision', 'navigation', 'communication']
        
        messages = [
            "Initialisation du système",
            "Lecture des capteurs terminée",
            "Niveau de batterie faible",
            "Obstacle détecté à {0} mètres",
            "Erreur de communication avec la station de base",
            "Échec de la connexion au serveur",
            "Température moteur élevée: {0}°C",
            "Mise à jour des coordonnées GPS",
            "Réception de nouvelle commande: {0}",
            "Exécution de la tâche #{0}",
            "Erreur critique: perte de données",
            "Redémarrage du système nécessaire",
            "Maintenance programmée"
        ]
        
        logs = []
        now = timezone.now()
        
        # Distribution du type de log
        type_weights = {'TEXT': 0.7, 'CURVE': 0.1, 'LASER2D': 0.1, 'IMAGE': 0.1}
        
        self.stdout.write(self.style.SUCCESS(f'Génération de {count} logs...'))
        
        for i in range(count):
            level = random.choice(log_levels)
            robot_id = random.choice(robot_ids)
            source = random.choice(sources)
            
            # Déterminer le type de log basé sur les poids
            log_type = random.choices(
                population=list(type_weights.keys()), 
                weights=list(type_weights.values()), 
                k=1
            )[0]
            
            message_template = random.choice(messages)
            if '{0}' in message_template:
                if 'mètres' in message_template:
                    param = random.randint(1, 10)
                elif '°C' in message_template:
                    param = random.randint(60, 90)
                elif 'commande' in message_template:
                    param = random.choice(['avancer', 'reculer', 'tourner', 'arrêter'])
                elif 'tâche' in message_template:
                    param = random.randint(1000, 9999)
                else:
                    param = random.randint(1, 100)
                message = message_template.format(param)
            else:
                message = message_template
            
            # Générer une date aléatoire dans les 30 derniers jours
            random_days = random.randint(0, 30)
            random_hours = random.randint(0, 23)
            random_minutes = random.randint(0, 59)
            random_seconds = random.randint(0, 59)
            timestamp = now - timedelta(
                days=random_days,
                hours=random_hours,
                minutes=random_minutes,
                seconds=random_seconds
            )
            
            log = RobotLog(
                timestamp=timestamp,
                robot_id=robot_id,
                level=level,
                message=message,
                source=source,
                log_type=log_type
            )
            
            # Si c'est un type spécial, ajouter des métadonnées
            if log_type != 'TEXT':
                metadata = {
                    'generated': True,
                    'generator': 'test_data_generator',
                    'timestamp': timestamp.isoformat(),
                }
                
                if log_type == 'CURVE':
                    metadata['signal_type'] = random.choice(['sine', 'square', 'triangle'])
                    metadata['frequency'] = random.uniform(0.1, 10.0)
                    metadata['amplitude'] = random.uniform(1.0, 5.0)
                    metadata['samples_count'] = random.randint(100, 1000)
                    metadata['unit'] = random.choice(['V', 'A', '°C', 'm/s', 'rad/s'])
                
                elif log_type == 'LASER2D':
                    metadata['angle_min'] = -3.14
                    metadata['angle_max'] = 3.14
                    metadata['angle_increment'] = 0.01745
                    metadata['range_min'] = 0.1
                    metadata['range_max'] = 10.0
                    metadata['points_count'] = random.randint(100, 360)
                
                elif log_type == 'IMAGE':
                    metadata['width'] = random.choice([320, 640, 800])
                    metadata['height'] = random.choice([240, 480, 600])
                    metadata['format'] = 'JPEG'
                    metadata['camera'] = f'CAM_{random.randint(1, 5)}'
                
                # Stocker les métadonnées
                log.set_metadata_from_dict(metadata)
            
            logs.append(log)
            
            if i % 100 == 0 and i > 0:
                self.stdout.write(f"  {i} logs générés...")
        
        # Sauvegarder les logs
        RobotLog.objects.bulk_create(logs)
        self.stdout.write(self.style.SUCCESS(f'{count} logs générés avec succès'))
        
        # Si demandé, générer des fichiers MDF
        if generate_mdf:
            self.generate_mdf_files(mdf_count)
    
    def generate_curve_data(self, log, curve_type='sine', points=500):
        """Génère des données de courbe pour un log"""
        # Créer un objet log de type courbe
        curve_measurements = []
        
        # Paramètres de base
        amplitude = random.uniform(1.0, 10.0)
        frequency = random.uniform(0.1, 2.0)
        
        # Créer une série temporelle
        base_time = log.timestamp
        
        for i in range(points):
            # Temps relatif en secondes (de 0 à 60 secondes)
            t = i / points * 60
            timestamp = base_time + timedelta(seconds=t)
            
            # Valeur selon le type de courbe
            if curve_type == 'sine':
                value = amplitude * np.sin(2 * np.pi * frequency * t)
            elif curve_type == 'square':
                value = amplitude * np.sign(np.sin(2 * np.pi * frequency * t))
            elif curve_type == 'triangle':
                value = 2 * amplitude * np.abs(2 * ((frequency * t) % 1 - 0.5)) - amplitude
            else:
                # Par défaut, une sinusoïde
                value = amplitude * np.sin(2 * np.pi * frequency * t)
            
            # Créer la mesure
            measurement = CurveMeasurement(
                log=log,
                timestamp=timestamp,
                sensor_name=f"Sensor_{log.robot_id}",
                value=float(value)
            )
            curve_measurements.append(measurement)
        
        # Générer un aperçu du graphique
        try:
            # Extraire les données pour le graphique
            times = [m.timestamp for m in curve_measurements]
            values = [m.value for m in curve_measurements]
            
            # Convertir les timestamps en nombres pour matplotlib
            import matplotlib.dates as mdates
            times_num = mdates.date2num(times)
            
            # Créer le graphique
            plt.figure(figsize=(8, 4))
            plt.plot(times_num, values)
            plt.title(f"Courbe: {log.message}")
            plt.xlabel("Temps")
            plt.ylabel("Valeur")
            plt.grid(True)
            
            # Définir le format de date sur l'axe x
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            
            # Sauvegarder l'image dans un buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            plt.close()
            
            # Attacher l'image au log
            log.data_file.save(
                f"curve_preview_{log.id}.png",
                ContentFile(buf.getvalue()),
                save=True
            )
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Erreur lors de la génération du graphique: {e}"))
        
        return curve_measurements
    
    def generate_laser_data(self, log, points=360):
        """Génère des données laser 2D pour un log"""
        # Paramètres du laser
        angle_min = -3.14159  # -180 degrés en radians
        angle_max = 3.14159   # 180 degrés en radians
        angle_increment = (angle_max - angle_min) / points
        
        # Créer un scan avec une forme circulaire de base et quelques obstacles
        range_data = []
        base_distance = 5.0  # distance de base en mètres
        
        # Générer les distances
        for i in range(points):
            angle = angle_min + i * angle_increment
            
            # Distance de base
            distance = base_distance
            
            # Ajouter des obstacles simulés
            # Un "mur" sur environ 30 degrés
            if -0.5 < angle < 0.5:
                distance = 2.0
            
            # Un obstacle ponctuel
            if 1.5 < angle < 2.0:
                distance = 1.0 + random.uniform(-0.1, 0.1)
            
            # Un autre obstacle
            if -2.0 < angle < -1.5:
                distance = 3.0 + random.uniform(-0.2, 0.2)
            
            # Ajouter un peu de bruit aléatoire
            distance += random.uniform(-0.1, 0.1)
            
            # S'assurer que la distance reste positive
            distance = max(0.1, distance)
            
            range_data.append(distance)
        
        # Créer l'objet de scan laser
        laser_scan = Laser2DScan(
            log=log,
            timestamp=log.timestamp,
            angle_min=angle_min,
            angle_max=angle_max,
            angle_increment=angle_increment
        )
        
        # Stocker les données de plage
        laser_scan.set_range_data_from_list(range_data)
        
        # Générer un aperçu visuel
        try:
            plt.figure(figsize=(6, 6))
            
            # Convertir les coordonnées polaires en coordonnées cartésiennes
            angles = np.linspace(angle_min, angle_max, len(range_data))
            xs = [r * np.cos(a) for r, a in zip(range_data, angles)]
            ys = [r * np.sin(a) for r, a in zip(range_data, angles)]
            
            # Tracer les points
            plt.scatter(xs, ys, s=2, c='blue')
            
            # Ajouter un point central pour le scanner
            plt.scatter(0, 0, s=50, c='red', marker='*')
            
            # Ajouter une grille et des axes
            plt.grid(True)
            plt.axhline(y=0, color='k', linestyle='-', alpha=0.3)
            plt.axvline(x=0, color='k', linestyle='-', alpha=0.3)
            
            # Définir les limites d'axes égales
            max_range = max(range_data) + 1
            plt.xlim(-max_range, max_range)
            plt.ylim(-max_range, max_range)
            
            plt.title(f"Scan Laser: {log.message}")
            plt.xlabel("X (mètres)")
            plt.ylabel("Y (mètres)")
            
            # Sauvegarder l'image dans un buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            plt.close()
            
            # Attacher l'image au log
            log.data_file.save(
                f"laser_preview_{log.id}.png",
                ContentFile(buf.getvalue()),
                save=True
            )
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Erreur lors de la génération de la visualisation laser: {e}"))
        
        return laser_scan
    
    def generate_image_data(self, log):
        """Génère une image simple pour un log"""
        # Obtenir les métadonnées
        metadata = log.get_metadata_as_dict()
        width = metadata.get('width', 320)
        height = metadata.get('height', 240)
        
        # Créer une image simple
        try:
            # Générer une image synthétique
            image_type = random.choice(['gradient', 'checker', 'circle'])
            
            if image_type == 'gradient':
                # Créer un dégradé
                array = np.zeros((height, width, 3), dtype=np.uint8)
                for i in range(height):
                    for j in range(width):
                        r = int(255 * i / height)
                        g = int(255 * j / width)
                        b = int(255 * (i + j) / (height + width))
                        array[i, j] = [r, g, b]
                
                img = Image.fromarray(array)
                
            elif image_type == 'checker':
                # Créer un damier
                check_size = random.randint(10, 50)
                array = np.zeros((height, width, 3), dtype=np.uint8)
                for i in range(height):
                    for j in range(width):
                        if (i // check_size + j // check_size) % 2 == 0:
                            array[i, j] = [255, 255, 255]
                        else:
                            array[i, j] = [0, 0, 0]
                
                img = Image.fromarray(array)
                
            else:  # circle
                # Créer un cercle
                array = np.zeros((height, width, 3), dtype=np.uint8)
                center_x, center_y = width // 2, height // 2
                radius = min(width, height) // 3
                
                for i in range(height):
                    for j in range(width):
                        dist = np.sqrt((i - center_y)**2 + (j - center_x)**2)
                        if dist < radius:
                            array[i, j] = [255, 0, 0]  # Cercle rouge
                        else:
                            array[i, j] = [255, 255, 255]  # Fond blanc
                
                img = Image.fromarray(array)
            
            # Sauvegarder l'image dans un buffer
            buf = io.BytesIO()
            img.save(buf, format='JPEG')
            buf.seek(0)
            
            # Créer l'objet ImageData
            image_data = ImageData(
                log=log,
                timestamp=log.timestamp,
                width=width,
                height=height,
                format='JPEG',
                description=f"Image générée: {image_type}"
            )
            
            # Sauvegarder l'image
            image_data.image_file.save(
                f"image_{log.id}.jpg",
                ContentFile(buf.getvalue()),
                save=False
            )
            
            # Utiliser également cette image comme aperçu pour le log
            log.data_file.save(
                f"image_preview_{log.id}.jpg",
                ContentFile(buf.getvalue()),
                save=True
            )
            
            return image_data
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Erreur lors de la génération de l'image: {e}"))
            return None
    
    def generate_mdf_files(self, count=2):
        """Génère des fichiers MDF de test"""
        self.stdout.write(self.style.SUCCESS(f'Génération de {count} fichiers MDF...'))
        
        try:
            # Essayer d'importer asammdf
            from asammdf import MDF
            import numpy as np
        except ImportError:
            self.stdout.write(self.style.ERROR("La bibliothèque asammdf n'est pas installée. Impossible de générer des fichiers MDF."))
            self.stdout.write(self.style.ERROR("Installez-la avec: pip install asammdf"))
            return
        
        for i in range(count):
            try:
                # Créer un fichier MDF
                mdf = MDF()
                
                # Ajouter quelques signaux de test
                # 1. Signal sinusoïdal
                timestamps = np.linspace(0, 10, 1000)
                sinus = np.sin(timestamps * 2 * np.pi * 0.5) * 5  # 0.5 Hz, amplitude 5
                
                try:
                    mdf.append(timestamps, sinus, 'sinus')
                except Exception as e:
                    # Essayer une méthode alternative
                    self.stdout.write(self.style.WARNING(f"Erreur lors de l'ajout du signal sinus, essai d'une méthode alternative: {e}"))
                    from asammdf.blocks.mdf_v4 import Signal
                    signal = Signal(samples=sinus, timestamps=timestamps, name='sinus')
                    mdf.append([signal])
                
                # 2. Signal carré (si le premier a fonctionné)
                try:
                    square = np.sign(np.sin(timestamps * 2 * np.pi * 0.3)) * 3  # 0.3 Hz, amplitude 3
                    mdf.append(timestamps, square, 'carre')
                except:
                    pass
                
                # 3. Événements textuels (si possible)
                try:
                    event_timestamps = np.linspace(0, 10, 5)
                    events = np.array(["Démarrage", "Événement 1", "Événement 2", "Alerte", "Fin"], dtype='U20')
                    mdf.append(event_timestamps, events, 'evenements')
                except:
                    pass
                
                # Sauvegarder dans un fichier temporaire
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mdf')
                temp_file.close()
                
                mdf.save(temp_file.name, overwrite=True)
                
                # Créer un objet MDFFile dans la base de données
                with open(temp_file.name, 'rb') as f:
                    mdf_file = MDFFile(
                        name=f"Test MDF File {i+1}",
                        mdf_version=f"MDF {mdf.version}" if hasattr(mdf, 'version') else "MDF 4.x"
                    )
                    mdf_file.file.save(
                        f"test_mdf_{i+1}.mdf",
                        ContentFile(f.read()),
                        save=True
                    )
                
                # Nettoyer le fichier temporaire
                os.unlink(temp_file.name)
                
                self.stdout.write(self.style.SUCCESS(f"  Fichier MDF {i+1} créé avec succès"))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Erreur lors de la génération du fichier MDF {i+1}: {e}"))
        
        self.stdout.write(self.style.SUCCESS(f'{count} fichiers MDF générés'))

    def create_rich_logs(self, logs):
        """Crée des données enrichies pour certains types de logs"""
        self.stdout.write(self.style.SUCCESS('Création de données enrichies pour les logs spéciaux...'))
        
        # Parcourir les logs et enrichir ceux qui ne sont pas de type TEXT
        for log in logs:
            if log.log_type == 'CURVE':
                # Générer des données de courbe
                metadata = log.get_metadata_as_dict()
                curve_type = metadata.get('signal_type', 'sine')
                points = metadata.get('samples_count', 500)
                
                # Créer et sauvegarder les mesures de courbe
                curve_measurements = self.generate_curve_data(log, curve_type, points)
                CurveMeasurement.objects.bulk_create(curve_measurements)
                
                self.stdout.write(f"  Créé {len(curve_measurements)} points de mesure pour le log {log.id}")
                
            elif log.log_type == 'LASER2D':
                # Générer des données laser
                laser_scan = self.generate_laser_data(log)
                laser_scan.save()
                
                self.stdout.write(f"  Créé un scan laser pour le log {log.id}")
                
            elif log.log_type == 'IMAGE':
                # Générer une image
                image_data = self.generate_image_data(log)
                if image_data:
                    image_data.save()
                    self.stdout.write(f"  Créé une image pour le log {log.id}")
