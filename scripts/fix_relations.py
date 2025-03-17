# fix_relations.py
import os
import django
import sys

# Ajouter le répertoire parent au chemin Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Vérifiez le nom de votre module de settings - il pourrait être différent
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logViewer.settings')
try:
    django.setup()
except ModuleNotFoundError:
    # Essayez une alternative si le premier nom ne fonctionne pas
    os.environ['DJANGO_SETTINGS_MODULE'] = 'robot_logs.settings'
    django.setup()

from robot_logs.models import LogGroup, RobotLog, MDFFile

def fix_relations():
    # Pour tous les logs qui ont un channel_group_index
    logs_with_index = RobotLog.objects.exclude(channel_group_index=None)
    print(f"Trouvé {logs_with_index.count()} logs avec un channel_group_index")
    
    # Pour chaque log, trouver le bon channel group
    fixed = 0
    for log in logs_with_index:
        # Trouver le channel group correspondant
        channel_groups = LogGroup.objects.filter(
            is_channel_group=True,
            channel_group_index=log.channel_group_index
        )
        
        if channel_groups.exists():
            # Prendre le premier channel group correspondant
            channel_group = channel_groups.first()
            # Si le log n'est pas déjà associé à ce groupe
            if log.group != channel_group:
                log.group = channel_group
                log.save()
                fixed += 1
    
    print(f"Corrigé {fixed} relations de logs")

if __name__ == "__main__":
    fix_relations()