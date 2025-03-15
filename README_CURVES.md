# Visualisation Avancée des Courbes

Cette fonctionnalité améliore la visualisation des courbes dans le projet LogViewer en ajoutant des capacités de zoom interactif et la possibilité de comparer plusieurs courbes sur un même graphique avec des axes Y différents.

## Fonctionnalités Principales

### 1. Zoom Interactif

- **Zoom à la molette** : utilisez la molette de la souris pour zoomer sur une partie spécifique de la courbe
- **Panoramique** : cliquez et faites glisser pour vous déplacer dans la courbe
- **Double-clic** : réinitialise la vue à sa taille d'origine
- **Outils supplémentaires** : options pour dessiner des lignes, effacer des formes, etc.

### 2. Comparaison de Plusieurs Courbes

- **Interface dédiée** : page spéciale pour comparer plusieurs courbes simultanément
- **Sélection flexible** : ajoutez autant de courbes que nécessaire à la comparaison
- **Axes Y multiples** : assignez chaque courbe à un axe Y différent (jusqu'à 4 axes)
- **Codage couleur** : chaque axe a sa propre couleur pour faciliter la lecture
- **Ajout/Suppression dynamique** : modifiez les courbes affichées sans recharger la page

## Utilisation

### Visualisation d'une Courbe Individuelle

1. Accédez à un log de type "Courbe"
2. Cliquez sur "Voir la courbe"
3. Utilisez les outils de zoom interactif pour explorer les données en détail
4. Cliquez sur "Comparer avec d'autres courbes" pour ajouter cette courbe à la vue de comparaison

### Comparaison de Plusieurs Courbes

1. Cliquez sur "Comparaison de courbes" dans la barre de navigation
2. Sélectionnez une courbe dans la liste déroulante
3. Choisissez l'axe Y sur lequel vous souhaitez l'afficher (Y1, Y2, Y3 ou Y4)
4. Cliquez sur "Ajouter"
5. Répétez pour ajouter d'autres courbes
6. Utilisez les outils de zoom pour explorer les données combinées
7. Retirez une courbe en cliquant sur le bouton "Retirer" correspondant

## Avantages

Cette fonctionnalité est particulièrement utile pour :

- **Analyse détaillée** : examinez de près des portions spécifiques d'une courbe
- **Corrélation de données** : comparez des courbes provenant de différents capteurs sur la même échelle de temps
- **Analyse de données à échelles multiples** : visualisez des courbes avec des unités et des plages de valeurs très différentes
- **Détection de tendances** : identifiez des corrélations entre différentes mesures

## Notes Techniques

- L'implémentation utilise Plotly.js, une bibliothèque JavaScript puissante pour la visualisation de données
- Les données sont transmises au format JSON du serveur vers le client
- Le zoom et la sélection d'axes sont gérés côté client pour une expérience fluide
- Les échelles des axes Y s'adaptent automatiquement aux données affichées
