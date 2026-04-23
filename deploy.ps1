# ============================================================================
# SCRIPT DE DEPLOIEMENT AUTOMATIQUE SUR GCP
# Drowsiness Detection Project
# ============================================================================

param(
    [string]$ProjectID = "drowsiness-detection-2024",
    [string]$Region = "europe-west1",
    [switch]$SkipSetup = $false,
    [switch]$ShowLogs = $false
)

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   DEPLOIEMENT SUR GCP - DROWSINESS DETECTION" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  - Projet: $ProjectID"
Write-Host "  - Region: $Region"
Write-Host ""

# ============================================================================
# 1. VÉRIFIER PRÉREQUIS
# ============================================================================

function Check-Prerequisites {
    Write-Host "1. Verification des prerequis..." -ForegroundColor Cyan
    
    # Verifier gcloud
    $gcloud = Get-Command gcloud -ErrorAction SilentlyContinue
    if (-not $gcloud) {
        Write-Host "   ERREUR: Google Cloud SDK n'est pas installe" -ForegroundColor Red
        Write-Host "   Installez depuis: https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "   OK - Google Cloud SDK trouve" -ForegroundColor Green
    
    # Verifier fichiers essentiels
    $essentialFiles = @("main.py", "app.yaml", "requirements.txt")
    foreach ($file in $essentialFiles) {
        if (Test-Path $file) {
            Write-Host "   OK - $file trouve" -ForegroundColor Green
        } else {
            Write-Host "   ERREUR - $file manquant" -ForegroundColor Red
            exit 1
        }
    }
    
    # Verifier modele
    if (Test-Path "models/best_model_mobilenetv2.h5") {
        $modelSize = (Get-Item "models/best_model_mobilenetv2.h5").Length / 1MB
        Write-Host "   OK - Modele trouve ($([math]::Round($modelSize, 2)) MB)" -ForegroundColor Green
        
        if ($modelSize -gt 200) {
            Write-Host "   ATTENTION: modele volumineux (>200MB)" -ForegroundColor Yellow
            Write-Host "   Conseil: utiliser Cloud Storage pour les gros fichiers" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   ERREUR - Modele manquant" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
}

# ============================================================================
# 2. CONFIGURATION GCP
# ============================================================================

function Setup-GCP {
    Write-Host "2️⃣ Configuration GCP..." -ForegroundColor Cyan
    
    # Définir le projet
    Write-Host "   • Sélection du projet..." -ForegroundColor Gray
    gcloud config set project $ProjectID 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ Projet défini: $ProjectID" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Impossible de sélectionner le projet. Continuons..." -ForegroundColor Yellow
    }
    
    # Définir la région
    Write-Host "   • Configuration de la région..." -ForegroundColor Gray
    gcloud config set app/region $Region 2>&1 | Out-Null
    Write-Host "   ✓ Région: $Region" -ForegroundColor Green
    
    # Activer les APIs
    Write-Host "   • Activation des APIs..." -ForegroundColor Gray
    gcloud services enable appengine.googleapis.com 2>&1 | Out-Null
    gcloud services enable cloudbuild.googleapis.com 2>&1 | Out-Null
    Write-Host "   ✓ APIs activées" -ForegroundColor Green
    
    Write-Host ""
}

# ============================================================================
# 3. DÉPLOYER
# ============================================================================

function Deploy-App {
    Write-Host "3️⃣ Déploiement en cours..." -ForegroundColor Cyan
    Write-Host "   ⏳ Cela peut prendre 5-10 minutes..." -ForegroundColor Gray
    Write-Host ""
    
    # Lancer le déploiement
    gcloud app deploy --quiet
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "   ✅ Déploiement réussi!" -ForegroundColor Green
        Write-Host ""
        
        # Obtenir l'URL
        $appUrl = gcloud app browse --no-launch --project $ProjectID 2>$null
        Write-Host "   🌐 URL: $appUrl" -ForegroundColor Green
        Write-Host ""
    } else {
        Write-Host "   ❌ Erreur lors du déploiement" -ForegroundColor Red
        exit 1
    }
}

# ============================================================================
# 4. AFFICHER LES LOGS
# ============================================================================

function Show-Logs {
    Write-Host "4️⃣ Affichage des logs..." -ForegroundColor Cyan
    Write-Host "   (Appuyez sur Ctrl+C pour arrêter)" -ForegroundColor Gray
    Write-Host ""
    
    gcloud app logs read -f --limit 50
}

# ============================================================================
# EXECUTION
# ============================================================================

try {
    Check-Prerequisites
    
    if (-not $SkipSetup) {
        Setup-GCP
    }
    
    Deploy-App
    
    if ($ShowLogs) {
        Show-Logs
    } else {
        Write-Host "Info - Pour afficher les logs: gcloud app logs read --limit 50" -ForegroundColor Cyan
        Write-Host "Info - Pour acceder a l'app: gcloud app browse" -ForegroundColor Cyan
    }
    
    Write-Host ""
    Write-Host "OK - Script termine!" -ForegroundColor Green
    
} catch {
    Write-Host ""
    Write-Host "ERREUR: $_" -ForegroundColor Red
    exit 1
}
