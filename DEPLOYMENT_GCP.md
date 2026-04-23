# 🚀 Guide de Déploiement sur GCP - Drowsiness Detection

## 1️⃣ PRÉREQUIS - Installation de Google Cloud SDK

### Windows:

```powershell
# Télécharger l'installateur depuis:
# https://cloud.google.com/sdk/docs/install#windows

# Ou via Chocolatey:
choco install google-cloud-sdk

# Ou via Scoop:
scoop install gcloud

# Initialiser
gcloud init
```

## 2️⃣ CONFIGURATION INITIALE GCP

### Étape 1: Créer/Sélectionner un projet

```powershell
# Voir les projets existants
gcloud projects list

# Créer un nouveau projet (si nécessaire)
gcloud projects create drowsiness-detection-2024

# Définir le projet par défaut
gcloud config set project drowsiness-detection-2024
```

### Étape 2: Configurer la région (optionnel)

```powershell
# Définir la région par défaut (ex: europe-west1)
gcloud config set run/region europe-west1
gcloud config set app/region europe-west1
```

### Étape 3: Activer les APIs nécessaires

```powershell
# App Engine
gcloud services enable appengine.googleapis.com

# Cloud Build (pour compiler/déployer)
gcloud services enable cloudbuild.googleapis.com
```

## 3️⃣ VÉRIFIER LA STRUCTURE DU PROJET

Assurez-vous que la structure est complète:

```
DrowsinessDetection/
├── main.py                    ✓ (application Flask)
├── app.yaml                   ✓ (configuration GAE)
├── requirements.txt           ✓ (dépendances)
├── .gcloudignore             ✓ (créé automatiquement)
├── models/
│   └── best_model_mobilenetv2.h5
└── templates/
    └── index.html
```

## 4️⃣ PRÉ-DÉPLOIEMENT: Vérifier la taille

⚠️ **IMPORTANT**: App Engine a une limite:

- **Taille totale**: max 500 MB (source + dépendances)
- **Les gros modèles**: doivent être compressés ou stockés dans Cloud Storage

```powershell
# Vérifier la taille du modèle
ls -la models/

# Si le modèle > 100MB, compressez-le:
tar -czf models.tar.gz models/
```

## 5️⃣ DÉPLOIEMENT SUR APP ENGINE (2 options)

### ✅ OPTION A: Déploiement Direct (Recommandé pour débuter)

```powershell
# Se placer dans le dossier du projet
cd "c:\Users\dghai\ITBS\2eme annee\DrowsinessDetection"

# Déployer
gcloud app deploy

# Le système va:
# 1. Préparer l'environnement Python
# 2. Installer les dépendances (requirements.txt)
# 3. Uploader le code
# 4. Créer une instance App Engine
# 5. Démarrer l'application
```

### ✅ OPTION B: Déploiement avec Staging (Plus contrôle)

```powershell
# Créer une version en staging
gcloud app deploy --no-promote

# Tester l'URL générée

# Promouvoir en production
gcloud app deploy --no-promote
gcloud app versions list
gcloud app services set-traffic default --splits v1=100
```

## 6️⃣ VÉRIFIER LE DÉPLOIEMENT

```powershell
# Voir l'URL de l'app
gcloud app browse

# Voir les logs en temps réel
gcloud app logs read -f

# Voir les instances actives
gcloud app instances list

# Voir les versions déployées
gcloud app versions list
```

## 7️⃣ PROBLÈMES COURANTS & SOLUTIONS

### ❌ Erreur: "MODEL_PATH not found"

```powershell
# Solution: Vérifier que le modèle est bien dans le dossier
# Ou utiliser Cloud Storage pour les gros fichiers
```

### ❌ Erreur: "Out of Memory"

```powershell
# Augmenter la mémoire dans app.yaml:
# - Ajouter après env: standard:
# resources:
#   memory_gb: 4
#   cpu: 2
```

### ❌ Erreur: "Timeout"

```powershell
# Augmenter le timeout dans app.yaml (déjà fait: 120s)
```

### ❌ Modèle trop volumineux

```powershell
# Solution 1: Compresser le modèle
# Solution 2: Utiliser Cloud Storage

# Exemple avec Cloud Storage:
# 1. Uploader le modèle:
gsutil cp models/best_model_mobilenetv2.h5 gs://mon-bucket/models/

# 2. Modifier main.py pour télécharger au démarrage:
# from google.cloud import storage
# bucket = storage.Client().bucket('mon-bucket')
# blob = bucket.blob('models/best_model_mobilenetv2.h5')
# blob.download_to_filename('models/best_model_mobilenetv2.h5')
```

## 8️⃣ ALTERNATIVE: Google Cloud Run (Plus flexible)

Si App Engine pose problèmes, utilisez Cloud Run:

```powershell
# Avec Cloud Run, on peut gérer plus de mémoire et de CPU
# Mais il faut créer un Dockerfile simple

# Créer Dockerfile:
# FROM python:3.9
# WORKDIR /app
# COPY requirements.txt .
# RUN pip install -r requirements.txt
# COPY . .
# CMD exec gunicorn -b :$PORT main:app

# Déployer:
gcloud run deploy drowsiness-detection \
  --source . \
  --platform managed \
  --region europe-west1 \
  --memory 2Gi \
  --cpu 2 \
  --allow-unauthenticated
```

## 9️⃣ CONFIGURATION FINALE (app.yaml mis à jour)

```yaml
runtime: python39
env: standard
entrypoint: gunicorn -b :$PORT --timeout 120 main:app

env_variables:
  MODEL_PATH: "models/best_model_mobilenetv2.h5"
  IMG_SIZE: "224"
  THRESHOLD: "0.5"

handlers:
  - url: /static
    static_dir: static
  - url: /.*
    script: auto
    secure: always
    redirect_http_response_code: 301

automatic_scaling:
  min_instances: 1
  max_instances: 5

timeout: "120s"
```

## 🔟 COMMANDE DÉPLOIEMENT FINALE

```powershell
# Position dans le dossier
cd "c:\Users\dghai\ITBS\2eme annee\DrowsinessDetection"

# Déployer
gcloud app deploy

# Accéder à l'app
gcloud app browse
```

---

## 📞 Support & Ressources

- Docs GCP: https://cloud.google.com/appengine
- Flask + GAE: https://cloud.google.com/python/docs/reference/functions/latest
- Troubleshooting: https://cloud.google.com/appengine/docs/standard/managing-instances-uptime#minimum_instances

**Status**: ✅ Prêt à déployer !
