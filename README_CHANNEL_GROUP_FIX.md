# Correctif pour l'assignation des logs aux channel groups

Ce correctif résout un problème où les logs n'étaient pas correctement assignés aux channel groups lors de l'importation de fichiers MDF.

## Problème

Lors de l'importation d'un fichier MDF avec l'option "Utiliser les channel groups" activée, les logs n'étaient pas correctement assignés aux sous-groupes représentant les channel groups, bien que :

1. Les sous-groupes (LogGroup avec is_channel_group=True) étaient correctement créés
2. Les logs avaient le bon attribut channel_group_index
3. Le code dans mdf_parser.py tentait de les assigner au bon groupe

Le problème provenait des fonctions `_process_xxx` dans `mdf_processors.py` qui assignaient directement les logs au groupe principal (`self._log_group`), surchargeant l'assignation ultérieure dans `process_channel`.

## Solution

La solution consiste en deux parties :

1. **Correction du code source** : 
   - Suppression des assignations de groupe codées en dur dans `mdf_processors.py`
   - Laissons `process_channel` dans `mdf_parser.py` gérer l'assignation aux bons groupes

2. **Script de correction pour les données existantes** :
   - Un script de migration `scripts/fix_channel_group_assignments.py` est fourni
   - Il réassigne les logs existants aux bons channel groups en fonction de leur channel_group_index

## Comment appliquer le correctif

1. Mettez à jour le code avec la branche `fix/channel-group-assignment-fix` :
   ```bash
   git checkout fix/channel-group-assignment-fix
   git pull
   ```

2. Pour corriger les données existantes, exécutez :
   ```bash
   python manage.py shell < scripts/fix_channel_group_assignments.py
   ```

3. Vérifiez que les logs apparaissent maintenant correctement dans leurs channel groups respectifs.

## Détail technique du correctif

Le correctif modifie la façon dont les logs sont créés et assignés :

**Avant** :
```python
# Dans mdf_processors.py
log = RobotLog(
    # ...autres attributs...
    group=self._log_group  # Assignation directe au groupe principal
)
```

**Après** :
```python
# Dans mdf_processors.py
log = RobotLog(
    # ...autres attributs...
    # Pas d'assignation de groupe ici
)

# Dans mdf_parser.py, la bonne assignation est faite :
log.group = log_group  # log_group est soit le groupe principal, soit le channel group
log.channel_group_index = group_index
```

Cette modification permet au code de `process_channel` dans `mdf_parser.py` de déterminer correctement le groupe approprié (principal ou channel group) et d'y assigner le log.

## Conséquences sur les performances

Ce correctif n'a pas d'impact significatif sur les performances. Il corrige simplement l'ordre des opérations sans ajouter de traitement supplémentaire.

## Cas d'utilisation future

Après ce correctif, les utilisateurs pourront bénéficier pleinement de la fonctionnalité de channel groups :

- Les logs seront correctement organisés par channel group
- La navigation hiérarchique entre le groupe principal et les sous-groupes fonctionnera comme prévu
- Les filtres par channel group seront plus précis

Si vous rencontrez d'autres problèmes avec la fonctionnalité de channel groups, veuillez créer un ticket dans le système de suivi des problèmes.
