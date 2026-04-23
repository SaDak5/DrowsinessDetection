param(
    [string]$ProjectID = "trim-cistern-493821-t6",
    [string]$Region = "europe-west1"
)

Write-Host "======================================================================"
Write-Host "   DEPLOIEMENT SUR GCP - DROWSINESS DETECTION"
Write-Host "======================================================================"
Write-Host ""
Write-Host "Configuration:"
Write-Host "  - Projet: $ProjectID"
Write-Host "  - Region: $Region"
Write-Host ""

# 1. VERIFICATION DES PREREQUIS
Write-Host "1. Verification des prerequis..." -ForegroundColor Cyan

$gcloud = Get-Command gcloud -ErrorAction SilentlyContinue
if (-not $gcloud) {
    Write-Host "   ERREUR: Google Cloud SDK n'est pas installe" -ForegroundColor Red
    exit 1
}
Write-Host "   OK - Google Cloud SDK trouve" -ForegroundColor Green

# Verifier fichiers essentiels
foreach ($file in @("main.py", "app.yaml", "requirements.txt")) {
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
} else {
    Write-Host "   ERREUR - Modele manquant" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 2. CONFIGURATION GCP
Write-Host "2. Configuration GCP..." -ForegroundColor Cyan

Write-Host "   - Selection du projet..." -ForegroundColor Gray
gcloud config set project $ProjectID 2>&1 | Out-Null
Write-Host "   OK - Projet defini: $ProjectID" -ForegroundColor Green

Write-Host "   - Configuration de la region..." -ForegroundColor Gray
gcloud config set app/region $Region 2>&1 | Out-Null
Write-Host "   OK - Region: $Region" -ForegroundColor Green

Write-Host "   - Activation des APIs..." -ForegroundColor Gray
gcloud services enable appengine.googleapis.com 2>&1 | Out-Null
gcloud services enable cloudbuild.googleapis.com 2>&1 | Out-Null
Write-Host "   OK - APIs activees" -ForegroundColor Green

Write-Host ""

# 3. DEPLOIEMENT
Write-Host "3. Deploiement en cours..." -ForegroundColor Cyan
Write-Host "   Cela peut prendre 5-10 minutes..." -ForegroundColor Gray
Write-Host ""

gcloud app deploy --quiet

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "   OK - Deploiement reussi!" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "   ERREUR - Probleme lors du deploiement" -ForegroundColor Red
    exit 1
}

Write-Host "Info - Pour afficher les logs: gcloud app logs read --limit 50" -ForegroundColor Cyan
Write-Host "Info - Pour acceder a l'app: gcloud app browse" -ForegroundColor Cyan
Write-Host ""
Write-Host "OK - Script termine!" -ForegroundColor Green
