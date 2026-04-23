# 🚀 Déploiement GCP - Drowsiness Detection

## ⚡ TL;DR - Déploiement en 3 étapes

### 1. Installer Google Cloud SDK

```powershell
# Windows - Via Chocolatey
choco install google-cloud-sdk

# Ou télécharger: https://cloud.google.com/sdk/docs/install
```

### 2. Initialiser GCP

```powershell
gcloud init
# Sélectionnez votre compte Google
# Créez/sélectionnez un projet
```

### 3. Déployer

```powershell
# Windows (PowerShell)
cd "c:\Users\dghai\ITBS\2eme annee\DrowsinessDetection"
.\deploy.ps1

# Linux/Mac
cd ~/path/to/DrowsinessDetection
bash deploy.sh
```

---

## ✅ Check-list pré-déploiement

- [ ] **Google Cloud SDK installé** - `gcloud --version`
- [ ] **Compte Google configuré** - `gcloud auth list`
- [ ] **Projet GCP créé** - `gcloud projects list`
- [ ] **Fichier `app.yaml` présent** ✓
- [ ] **Modèle `best_model_mobilenetv2.h5` présent** ✓
- [ ] **Fichier `.gcloudignore` présent** ✓
- [ ] **requirements.txt à jour** ✓

---

## 📁 Fichiers de configuration créés

| Fichier             | Rôle                                     |
| ------------------- | ---------------------------------------- |
| `app.yaml`          | Configuration App Engine (UPDATED)       |
| `.gcloudignore`     | Exclut dataset/ et dossiers volumineux ✓ |
| `deploy.ps1`        | Script PowerShell automatisé ✓           |
| `deploy.sh`         | Script Bash pour Linux/Mac ✓             |
| `DEPLOYMENT_GCP.md` | Guide complet détaillé ✓                 |

---

## 🎯 Résultat attendu

Après déploiement:

- ✅ Application accessible via URL `https://drowsiness-detection-2024.appspot.com`
- ✅ Modèle ML chargé et actif
- ✅ API Flask fonctionnelle
- ✅ Templates HTML servis

---

## 🐛 Dépannage rapide

### L'app ne démarre pas?

```powershell
# Voir les erreurs
gcloud app logs read -f
```

### Modèle trop volumineux?

```powershell
# Compresser le modèle
Compress-Archive -Path models\*.h5 -DestinationPath models.zip
```

### Besoin de plus de mémoire?

Ajouter dans `app.yaml`:

```yaml
resources:
  memory_gb: 2
  cpu: 1
```

---

## 📖 Documentation

- **Guide complet**: Voir `DEPLOYMENT_GCP.md`
- **GCP App Engine**: https://cloud.google.com/appengine
- **Déploiement Flask**: https://cloud.google.com/python/docs/

---

## 🎬 Commandes post-déploiement

```powershell
# Voir l'application
gcloud app browse

# Afficher les logs en direct
gcloud app logs read -f

# Lister les versions
gcloud app versions list

# Arrêter une version
gcloud app versions stop VERSION_ID

# Supprimer l'application
gcloud app delete
```

---

## 🚨 Options alternatives si App Engine pose problème

### Option A: Google Cloud Run (Recommandé)

```powershell
gcloud run deploy drowsiness-detection \
  --source . \
  --platform managed \
  --region europe-west1 \
  --memory 2Gi \
  --cpu 2 \
  --allow-unauthenticated
```

### Option B: Compute Engine (VM)

- Plus de contrôle
- Moins cher à long terme
- Demande plus de configuration

---

## 💡 Tips & Astuces

1. **Variables d'environnement**: Modifiables dans `app.yaml`
2. **Scaling**: Contrôlé par `automatic_scaling` dans `app.yaml`
3. **Coûts**: App Engine gratuit jusqu'à certains quotas
4. **Monitoring**: Utilisez GCP Console pour les logs et métriques

---

**Status**: ✅ **Prêt à déployer !**

Lancez maintenant: `.\deploy.ps1` (Windows) ou `bash deploy.sh` (Linux/Mac)
