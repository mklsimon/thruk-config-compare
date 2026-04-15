# Python DevContainer

Ce projet fournit un environnement de développement prêt à l'emploi pour des applications Python dans un conteneur Docker, optimisé pour VS Code.

## Fonctionnalités principales
- **Environnement Python isolé** avec venv local (`.venv`)
- **Installation automatique** des dépendances listées dans `requirements.txt`
- **Scripts utilitaires** pour gérer l'environnement Python :
  - `env-init` : installe ou réinstalle les dépendances
  - `env-clean` : nettoie l'environnement
  - `env-check` : affiche l'état de l'environnement
  - `env-help` : affiche l'aide
- **Extensions VS Code** recommandées pour Python

## Démarrage rapide
1. **Ouvrir le dossier dans VS Code**
2. Installer l'extension "Remote - Containers" si besoin
3. Cliquer sur "Reopen in Container"
4. L'environnement Python sera automatiquement prêt (voir message ✅)
5. Pour installer les dépendances ou réinitialiser l'environnement :
   ```bash
   env-init
   ```

## Structure du projet
- `main.py` : point d'entrée de votre app/script
- `requirements.txt` : dépendances Python
- `.devcontainer/` : configuration du conteneur et scripts

## Scripts disponibles
Voir la commande `env-help` ou le fichier `.devcontainer/env-commands.help` pour la liste complète et l'aide sur les scripts.

## Personnalisation
- Ajoutez vos dépendances dans `requirements.txt`
- Modifiez `main.py` pour votre application
- Adaptez la configuration Docker/DevContainer si besoin

---

*Basé sur un template DevContainer Python, prêt pour le développement moderne !*
