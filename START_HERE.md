# ✅ PROJET PRÊT À DÉPLOYER SUR GCP

## 📋 Fichiers Créés/Modifiés

```
✅ app.yaml                    - Configuration GAE optimisée
✅ .gcloudignore              - Exclut dataset/ et cache
✅ deploy.ps1                 - Script automatisé (Windows)
✅ deploy.sh                  - Script automatisé (Linux/Mac)
✅ DEPLOYMENT_GCP.md          - Guide complet (10 sections)
✅ README_DEPLOYMENT.md       - Quick start & checklist
```

---

## 🚀 DÉPLOIEMENT EN 2 COMMANDES

### Étape 1: Configuration initiale (une seule fois)

```powershell
gcloud init
# Suivez les instructions pour:
# 1. Vous connecter avec votre compte Google
# 2. Créer ou sélectionner un projet GCP
```

### Étape 2: Déployer l'application

```powershell
cd "c:\Users\dghai\ITBS\2eme annee\DrowsinessDetection"
.\deploy.ps1
```

**C'est tout!** ☝️

---

## 📊 Coût estimé

| Service          | Coût                                            |
| ---------------- | ----------------------------------------------- |
| App Engine       | **Gratuit** (12 instances-heures/jour incluses) |
| Stockage modèles | ~$0.020/GB/mois                                 |
| Bande passante   | Gratuit (1 GB/jour inclus)                      |
| **Total**        | **Pratiquement gratuit** ✓                      |

---

## 🎯 Ce que vous obtenez

- ✅ URL publique: `https://votre-projet.appspot.com`
- ✅ Modèle ML actif et rapide
- ✅ API REST fonctionnelle
- ✅ Interface web (templates/index.html)
- ✅ Scaling automatique
- ✅ Monitoring & logs en temps réel
- ✅ SSL/HTTPS automatique

---

## ⚡ Quick Commands

```powershell
# Voir l'app en ligne
gcloud app browse

# Logs en direct (temps réel)
gcloud app logs read -f

# Arrêter l'app
gcloud app versions stop VERSION_ID

# Voir toutes les versions
gcloud app versions list
```

---

## 🆘 Aide

**Lisez d'abord**: `DEPLOYMENT_GCP.md` (guide complet avec troubleshooting)

**Questions?**

- GCP Console: https://console.cloud.google.com
- Documentation: https://cloud.google.com/appengine
- Stack Overflow: Tagguez `google-app-engine`

---

## 📝 Notes importantes

1. **Taille du modèle**: Vérifiée et optimisée
2. **Timeout**: Augmenté à 120 secondes (pour les calculs ML)
3. **Dataset**: Exclu du déploiement (via .gcloudignore)
4. **Port**: Automatiquement géré par GCP
5. **Environnement**: Python 3.9 (spécifié dans app.yaml)

---

## 🎬 Prochaines étapes

1. [ ] Installer Google Cloud SDK (si pas fait)
2. [ ] Lancer `gcloud init`
3. [ ] Lancer `.\deploy.ps1`
4. [ ] Attendre 5-10 minutes
5. [ ] Accéder à `gcloud app browse`
6. [ ] Tester l'application!

---

**Bonne déploiement! 🚀**

Pour plus de détails, consultez les fichiers markdown créés.
