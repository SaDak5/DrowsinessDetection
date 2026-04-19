import os
import numpy as np
import matplotlib.pyplot as plt
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.models import load_model
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay,
    roc_auc_score,
    roc_curve
)

# ── Paramètres ────────────────────────────────────────────────────────────────
IMG_SIZE    = 224
BATCH_SIZE  = 32

DATASET_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dataset')
models_dir  = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
outputs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'outputs')
os.makedirs(outputs_dir, exist_ok=True)

# ── Générateur test ───────────────────────────────────────────────────────────
test_dir     = os.path.join(DATASET_DIR, 'test')
test_datagen = ImageDataGenerator(preprocessing_function=preprocess_input)

test_gen = test_datagen.flow_from_directory(
    test_dir,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='binary',
    classes=['awake', 'drowsy'],  # 0=awake, 1=drowsy
    shuffle=False
)

print(f"Classes : {test_gen.class_indices}")
print(f"Test    : {test_gen.samples} images\n")

# ── Charger le modèle ─────────────────────────────────────────────────────────
model_path = os.path.join(models_dir, 'best_model_mobilenetv2.h5')
print(f"Chargement du modèle : {model_path}")
model = load_model(model_path)

# ── Évaluation ────────────────────────────────────────────────────────────────
print("\nÉvaluation sur le test set...")
loss, accuracy = model.evaluate(test_gen, verbose=1)

# ── Prédictions ───────────────────────────────────────────────────────────────
print("\nGénération des prédictions...")
test_gen.reset()
y_pred_probs = model.predict(test_gen, verbose=1).flatten()
y_pred       = (y_pred_probs > 0.5).astype(int)
y_true       = test_gen.classes
class_names  = list(test_gen.class_indices.keys())  # ['awake', 'drowsy']

# ── Métriques ─────────────────────────────────────────────────────────────────
print("\n=== Métriques d'évaluation ===")
print(f"Test Loss : {loss:.4f}")
print(f"Accuracy  : {accuracy:.4f}")

report = classification_report(y_true, y_pred, target_names=class_names)
print("\n=== Rapport de classification ===")
print(report)

cm = confusion_matrix(y_true, y_pred)
print("=== Matrice de confusion ===")
print(cm)

try:
    auc = roc_auc_score(y_true, y_pred_probs)
    print(f"\nAUC-ROC : {auc:.4f}")
except Exception:
    auc = None

# ── Sauvegarde résultats texte ────────────────────────────────────────────────
results_path = os.path.join(outputs_dir, 'evaluation_results.txt')
with open(results_path, 'w', encoding='utf-8') as f:
    f.write("=== Métriques d'évaluation (Test Set — MobileNetV2) ===\n\n")
    f.write(f"Modèle    : {model_path}\n")
    f.write(f"Test Loss : {loss:.4f}\n")
    f.write(f"Accuracy  : {accuracy:.4f}\n")
    if auc:
        f.write(f"AUC-ROC   : {auc:.4f}\n")
    f.write("\n=== Rapport de classification ===\n")
    f.write(report)
    f.write("\n=== Matrice de confusion ===\n")
    f.write(str(cm))
print(f"\nRésultats sauvegardés : {results_path}")

# ── Matrice de confusion (image) ──────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(6, 5))
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=class_names)
disp.plot(ax=ax, colorbar=False, cmap='Blues')
ax.set_title("Matrice de confusion — MobileNetV2")
plt.tight_layout()
cm_path = os.path.join(outputs_dir, 'confusion_matrix_mobilenetv2.png')
plt.savefig(cm_path)
plt.close()
print(f"Matrice de confusion sauvegardée : {cm_path}")

# ── Courbe ROC ────────────────────────────────────────────────────────────────
if auc:
    fpr, tpr, _ = roc_curve(y_true, y_pred_probs)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(fpr, tpr, label=f"AUC = {auc:.4f}", color='steelblue', lw=2)
    ax.plot([0, 1], [0, 1], 'k--', lw=1)
    ax.set_xlabel("Taux de faux positifs")
    ax.set_ylabel("Taux de vrais positifs")
    ax.set_title("Courbe ROC — MobileNetV2")
    ax.legend(loc='lower right')
    plt.tight_layout()
    roc_path = os.path.join(outputs_dir, 'roc_curve_mobilenetv2.png')
    plt.savefig(roc_path)
    plt.close()
    print(f"Courbe ROC sauvegardée : {roc_path}")

print("\n=== ÉVALUATION TERMINÉE ===")