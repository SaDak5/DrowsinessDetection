#!/bin/bash

# ============================================================================
# 🚀 SCRIPT DE DÉPLOIEMENT AUTOMATIQUE SUR GCP (Linux/Mac)
# Drowsiness Detection Project
# ============================================================================

PROJECT_ID="${1:-drowsiness-detection-2024}"
REGION="${2:-europe-west1}"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  🚀 DÉPLOIEMENT SUR GCP - DROWSINESS DETECTION            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📋 Configuration:"
echo "  • Projet: $PROJECT_ID"
echo "  • Région: $REGION"
echo ""

# ============================================================================
# 1. VÉRIFIER PRÉREQUIS
# ============================================================================

echo "1️⃣ Vérification des prérequis..."

# Vérifier gcloud
if ! command -v gcloud &> /dev/null; then
    echo "   ❌ Google Cloud SDK n'est pas installé"
    echo "   📥 Installez depuis: https://cloud.google.com/sdk/docs/install"
    exit 1
fi
echo "   ✓ Google Cloud SDK trouvé"

# Vérifier fichiers essentiels
for file in "main.py" "app.yaml" "requirements.txt"; do
    if [ -f "$file" ]; then
        echo "   ✓ $file trouvé"
    else
        echo "   ❌ $file manquant"
        exit 1
    fi
done

# Vérifier modèle
if [ -f "models/best_model_mobilenetv2.h5" ]; then
    model_size=$(du -m "models/best_model_mobilenetv2.h5" | cut -f1)
    echo "   ✓ Modèle trouvé ($model_size MB)"
    
    if [ $model_size -gt 200 ]; then
        echo "   ⚠️  Attention: modèle volumineux (>200MB)"
        echo "   💡 Conseil: utiliser Cloud Storage pour les gros fichiers"
    fi
else
    echo "   ❌ Modèle manquant"
    exit 1
fi

echo ""

# ============================================================================
# 2. CONFIGURATION GCP
# ============================================================================

echo "2️⃣ Configuration GCP..."

echo "   • Sélection du projet..."
gcloud config set project $PROJECT_ID
echo "   ✓ Projet défini: $PROJECT_ID"

echo "   • Configuration de la région..."
gcloud config set app/region $REGION
echo "   ✓ Région: $REGION"

echo "   • Activation des APIs..."
gcloud services enable appengine.googleapis.com
gcloud services enable cloudbuild.googleapis.com
echo "   ✓ APIs activées"

echo ""

# ============================================================================
# 3. DÉPLOYER
# ============================================================================

echo "3️⃣ Déploiement en cours..."
echo "   ⏳ Cela peut prendre 5-10 minutes..."
echo ""

gcloud app deploy --quiet

if [ $? -eq 0 ]; then
    echo ""
    echo "   ✅ Déploiement réussi!"
    echo ""
    
    # Obtenir l'URL
    app_url=$(gcloud app browse --no-launch --project $PROJECT_ID 2>/dev/null)
    echo "   🌐 URL: $app_url"
    echo ""
else
    echo "   ❌ Erreur lors du déploiement"
    exit 1
fi

# ============================================================================
# INFORMATION FINALE
# ============================================================================

echo "💡 Commandes utiles:"
echo "   • Voir les logs: gcloud app logs read -f"
echo "   • Accéder à l'app: gcloud app browse"
echo "   • Arrêter l'app: gcloud app versions stop <version-id>"
echo ""
echo "✅ Script terminé!"
