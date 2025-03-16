#!/usr/bin/env python
"""
Script pour corriger les assignations de channel groups dans les logs existants.
À exécuter avec:
python manage.py shell < scripts/fix_channel_group_assignments.py
"""

import os
import sys
import django

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logViewer.settings')
django.setup()

from django.db.models import Q
from robot_logs.models import LogGroup, RobotLog, MDFFile

def fix_channel_group_assignments():
    """
    Corrige les assignations de logs aux channel groups.
    Cette fonction réassigne les logs qui ont un channel_group_index
    mais qui sont associés au mauvais groupe.
    """
    print("Correction des assignations de channel groups...")
    
    # Compte des logs ayant un channel_group_index
    logs_with_cg = RobotLog.objects.exclude(channel_group_index=None)
    print(f"Logs avec un channel_group_index: {logs_with_cg.count()}")
    
    # Compte pour chaque valeur de channel_group_index
    cg_counts = {}
    for log in logs_with_cg:
        if log.channel_group_index in cg_counts:
            cg_counts[log.channel_group_index] += 1
        else:
            cg_counts[log.channel_group_index] = 1
    
    print("Distribution des channel_group_index:")
    for cg_idx, count in sorted(cg_counts.items()):
        print(f"  Channel group {cg_idx}: {count} logs")
    
    # Pour chaque fichier MDF
    fixed_count = 0
    for mdf_file in MDFFile.objects.filter(log_group__isnull=False):
        print(f"\nTraitement du fichier MDF: {mdf_file.name}")
        
        # Groupe principal pour ce fichier MDF
        main_group = mdf_file.log_group
        print(f"  Groupe principal: {main_group.name} (ID: {main_group.id})")
        
        # Récupérer tous les channel groups pour ce fichier
        channel_groups = LogGroup.objects.filter(
            parent_group=main_group,
            is_channel_group=True
        )
        print(f"  Nombre de channel groups trouvés: {channel_groups.count()}")
        
        # Créer un mapping des index vers les channel groups
        channel_group_map = {cg.channel_group_index: cg for cg in channel_groups}
        
        # Source pattern pour les logs de ce fichier
        source_pattern = f"MDF Import: {mdf_file.name}"
        
        # Logs à corriger : ceux qui ont un channel_group_index mais pas le bon groupe
        logs_to_fix = []
        
        for cg_idx, channel_group in channel_group_map.items():
            # Logs qui ont cet index mais pas ce groupe
            misplaced_logs = RobotLog.objects.filter(
                source=source_pattern,
                channel_group_index=cg_idx
            ).exclude(group=channel_group)
            
            # Ajouter à la liste à corriger
            for log in misplaced_logs:
                logs_to_fix.append((log, channel_group))
        
        print(f"  Logs à réassigner: {len(logs_to_fix)}")
        
        # Corriger les logs
        for log, correct_group in logs_to_fix:
            old_group = log.group
            log.group = correct_group
            log.save()
            
            print(f"  Log {log.id} réassigné: {old_group} -> {correct_group}")
            fixed_count += 1
    
    print(f"\nTotal des logs réassignés: {fixed_count}")
    
    # Vérification finale
    misplaced_logs_count = 0
    for mdf_file in MDFFile.objects.filter(log_group__isnull=False):
        main_group = mdf_file.log_group
        channel_groups = LogGroup.objects.filter(
            parent_group=main_group,
            is_channel_group=True
        )
        channel_group_map = {cg.channel_group_index: cg for cg in channel_groups}
        
        # Source pattern pour les logs de ce fichier
        source_pattern = f"MDF Import: {mdf_file.name}"
        
        for cg_idx, channel_group in channel_group_map.items():
            # Logs qui ont cet index mais pas ce groupe
            misplaced = RobotLog.objects.filter(
                source=source_pattern,
                channel_group_index=cg_idx
            ).exclude(group=channel_group).count()
            misplaced_logs_count += misplaced
    
    if misplaced_logs_count > 0:
        print(f"ATTENTION: Il reste {misplaced_logs_count} logs mal assignés.")
    else:
        print("Tous les logs sont correctement assignés !")

# Exécution du script
if __name__ == "__main__":
    fix_channel_group_assignments()
