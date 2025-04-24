# BAW Marketing Tools

Une application desktop développée en Python pour traiter et envoyer des fichiers audio à des services web via webhooks.

## Fonctionnalités

- Conversion de fichiers MP4 en MP3
- Compression de fichiers audio avec différentes qualités
- Découpage de fichiers audio en plusieurs parties
- Envoi des fichiers audio à des services web via webhooks
- Interface utilisateur moderne et intuitive

## Prérequis

- Python 3.6 ou supérieur
- ffmpeg (inclus dans le dossier `bin/` ou à installer séparément)

## Installation

1. Clonez ce dépôt :
```
git clone https://github.com/VOTRE-NOM-UTILISATEUR/baw-marketing-tools.git
cd baw-marketing-tools
```

2. Installez les dépendances :
```
pip install -r requirements.txt
```

3. Configurez vos webhooks :
   - Remplacez les URLs de webhook dans `gui/audio_chunks_view.py` et `src/mp4_converter.py` par vos propres URLs

## Utilisation

Lancez l'application avec :
```
python main.py
```

## Structure du projet

- `main.py` : Point d'entrée principal de l'application
- `gui/` : Modules de l'interface utilisateur
- `utils/` : Utilitaires pour le traitement audio et l'envoi de fichiers
- `src/` : Modules sources spécifiques
- `bin/` : Binaires externes (ffmpeg)
- `blueprints/` : Blueprints Make.com pour configurer les intégrations

## Configuration Make.com

Cette application envoie des fichiers audio à Make.com via des webhooks. Deux scénarios Make sont nécessaires :

1. **Scénario de réception des fichiers** : Reçoit les fichiers audio et les stocke dans Google Drive
2. **Scénario de comptage des parties** : Reçoit le nombre de parties et gère la logique de traitement

> **Note importante** : Les fichiers blueprint Make.com ne sont pas inclus dans ce dépôt pour des raisons de sécurité (ils contiennent des identifiants personnels et des clés API). Veuillez contacter l'auteur pour obtenir ces fichiers si nécessaire.

Pour configurer vos propres scénarios Make.com :

1. Créez un scénario dans Make.com qui commence par un webhook HTTP
2. Ajoutez les modules nécessaires pour traiter les fichiers audio (Google Drive, etc.)
3. Activez le scénario et copiez l'URL du webhook générée
4. Collez cette URL dans les fichiers suivants :
   - `gui/audio_chunks_view.py` : Remplacez `PARTS_COUNT_WEBHOOK_URL = "INSÉRER_URL_WEBHOOK_ICI"`
   - `src/mp4_converter.py` : Remplacez `WEBHOOK_URL = "INSÉRER_URL_WEBHOOK_ICI"`

## Création d'un exécutable

Pour créer un exécutable standalone :
```
pyinstaller --onefile --windowed --icon=logo_baw.png --add-data "bin;bin" --add-data "logo_baw.png;." main.py
```

## Crédits

Développé par Antoine GOUPIL
