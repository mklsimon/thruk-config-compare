# Thruk Audit Cockpit

Ce projet est une application Streamlit permettant de comparer et d’auditer la configuration de plusieurs instances Thruk (Naemon/Nagios) via leur API. L’outil facilite l’identification des différences entre environnements (OnPrem, GCP, etc.) sur les objets supervisés (hosts, services, timeperiods).

## Fonctionnalités principales
- Sélection de deux instances Thruk à comparer (source/cible)
- Récupération automatique des données via l’API Thruk
- Affichage des différences : objets absents, en trop, ou en désynchronisation d’état
- Tableaux interactifs pour explorer les écarts
- Cockpit global de synthèse des anomalies
- Vidage du cache Streamlit en un clic

## Structure du projet
```
main.py                  # Application principale Streamlit
requirements.txt         # Dépendances Python
config/
  thruk_config.json      # Configuration des instances Thruk (URL, API key, user)
  thruk_query.json       # Colonnes à récupérer pour chaque endpoint
```

## Installation
1. Clonez le dépôt et placez-vous dans le dossier du projet.
2. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

## Utilisation
Lancez l’application Streamlit :
```bash
streamlit run main.py
```

## Configuration
- **config/thruk_config.json** : renseignez les accès API pour chaque instance Thruk à comparer.
- **config/thruk_query.json** : personnalisez les colonnes récupérées pour chaque endpoint (hosts, services, etc.).

## Exemples d’utilisation
- Audit de migration entre deux environnements de supervision
- Contrôle de conformité entre production et recette
- Détection rapide des objets manquants, en trop ou désynchronisés

## Dépendances

- streamlit
- pandas
- requests

## Développement dans un DevContainer

Un environnement de développement conteneurisé (VS Code DevContainer) est fourni pour garantir la reproductibilité et la simplicité de mise en place.

### Démarrage rapide
1. Ouvrez le dossier du projet dans VS Code.
2. Installez l’extension "Remote - Containers" si besoin.
3. Cliquez sur "Reopen in Container".
4. L’environnement Python sera automatiquement prêt à l’emploi (voir message ✅ dans le terminal).
5. Utilisez la commande suivante pour installer ou réinstaller les dépendances :
  ```bash
  env-init
  ```

Pour plus de détails sur la personnalisation, les scripts utilitaires et la structure du DevContainer, consultez le fichier [.devcontainer/README.md](.devcontainer/README.md).

## Analyse réseau avec tcplife

Vous pouvez déposer dans le dossier `./dump_tcplife` les fichiers de traces réseau générés par l’outil tcplife (format CSV/log). L’application permet alors de recouper les adresses IP observées avec les objets de supervision Thruk pour enrichir l’audit.

### Exemple de génération automatique (cron + script)

Ajoutez la ligne suivante à votre crontab pour lancer la capture chaque heure :

```cron
# Dump network traces
dump network traces
0 * * * * /bin/bash /root/rotate_tcplife.sh
```

Exemple de script `/root/rotate_tcplife.sh` :

```bash
#!/bin/bash

# 1. Tuer l'ancienne instance de tcplife proprement
pkill -f "tcplife -s"

# 2. Définir le dossier et le nom du fichier (00.log, 01.log, ..., 23.log)
OUTPUT_DIR="/u01/tcplife"
mkdir -p $OUTPUT_DIR
FILENAME="${OUTPUT_DIR}/$(date +'%H').log"

# 3. Supprimer l'ancien fichier de la veille pour repartir sur du propre
rm -f "$FILENAME"

# 4. Lancer la nouvelle instance
# -L : Colonne Date/Heure
# -P : Colonne Protocole (TCP)
# -T : Colonne Timestamp
# -s : Colonne CSV-like (si supporté) ou séparateurs simples
nohup /usr/share/bcc/tools/tcplife -s > "$FILENAME" 2>&1 &
```

Copiez ensuite les fichiers générés dans le dossier `./dump_tcplife` du projet pour les exploiter dans l’interface.
