from django.core.management.base import BaseCommand
from robot_logs.models import RobotLog
from django.utils import timezone
import random
from datetime import timedelta

class Command(BaseCommand):
    help = 'Génère des logs de test'

    def add_arguments(self, parser):
        parser.add_argument('count', type=int, help='Nombre de logs à générer')

    def handle(self, *args, **options):
        count = options['count']
        robot_ids = ['R2D2', 'C3PO', 'BB8', 'K2SO', 'RobotX']
        log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
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
        
        for i in range(count):
            level = random.choice(log_levels)
            robot_id = random.choice(robot_ids)
            source = random.choice(sources)
            
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
                source=source
            )
            logs.append(log)
            
        RobotLog.objects.bulk_create(logs)
        self.stdout.write(self.style.SUCCESS(f'{count} logs générés avec succès'))
