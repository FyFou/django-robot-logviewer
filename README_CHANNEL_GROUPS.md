# Support des Channel Groups dans LogViewer

Cette fonctionnalité permet de mieux organiser les données importées depuis les fichiers MDF en utilisant la structure de channel groups présente dans ces fichiers.

## Qu'est-ce qu'un Channel Group?

Dans les fichiers MDF (Measurement Data Format), les données sont organisées en "channel groups" qui regroupent des canaux de mesure liés. Par exemple :
- Un channel group peut contenir toutes les données d'un bus CAN spécifique
- Un autre peut contenir les données d'un ensemble de capteurs
- Un troisième peut regrouper les logs textuels d'un sous-système particulier

Cette organisation en channel groups reflète souvent la structure des systèmes qui ont généré les données.

## Comment cela fonctionne dans LogViewer

Lorsque vous importez un fichier MDF avec l'option "Utiliser les channel groups" activée (activée par défaut) :

1. Le système crée un groupe principal pour l'importation
2. Pour chaque channel group dans le fichier MDF, un sous-groupe est créé
3. Les logs générés à partir des canaux sont assignés au sous-groupe correspondant à leur channel group d'origine
4. Une hiérarchie claire est maintenue entre le groupe principal et les sous-groupes

## Avantages

- **Organisation logique** : Les logs sont organisés selon la structure originale du fichier MDF
- **Navigation simplifiée** : Vous pouvez explorer les données par sous-système ou module
- **Analyse facilitée** : Les données corrélées restent regroupées
- **Filtrage amélioré** : Vous pouvez filtrer les logs par channel group en plus des autres critères

## Interface utilisateur

### Lors de l'importation

- Une option "Utiliser les channel groups" est disponible lors de l'importation d'un fichier MDF
- Pendant la prévisualisation, vous verrez les channel groups détectés dans le fichier
- Une fois l'importation terminée, vous serez redirigé vers le groupe principal qui montre les sous-groupes

### Dans la vue de groupe

- Les groupes principaux affichent une section "Channel Groups" listant tous les sous-groupes
- Chaque log indique son channel group d'origine
- Les vues détaillées des logs montrent également le channel group associé

### Dans la liste des logs

- Vous pouvez maintenant filtrer les logs par channel group
- Les exports CSV incluent l'information de channel group

## Notes techniques

- Les sous-groupes (channel groups) sont des objets LogGroup réguliers mais avec l'attribut `is_channel_group=True`
- Ils ont une relation `parent_group` vers le groupe principal
- L'attribut `channel_group_index` stocke l'index original du channel group dans le fichier MDF
- Les logs ont également un champ `channel_group_index` qui conserve cette information, même s'ils sont déplacés entre groupes

## Migration des données existantes

L'ajout de cette fonctionnalité nécessite une migration de base de données. Si vous avez des données existantes :

1. Exécutez la migration : `python manage.py migrate`
2. Les champs nécessaires seront ajoutés à vos modèles
3. Aucune action supplémentaire n'est requise pour les données existantes

## Désactivation de la fonctionnalité

Si vous préférez ne pas utiliser les channel groups pour certaines importations, vous pouvez simplement décocher l'option "Utiliser les channel groups" lors de l'importation d'un fichier MDF. Tous les logs seront alors assignés directement au groupe principal.
