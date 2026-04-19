# predict.py
import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
import os

# ── Paramètres ────────────────────────────────────────────────────────────────
IMG_SIZE   = 224
THRESHOLD  = 0.5       # seuil de décision (0.35 pour plus de sensibilité)
VIDEO_PATH = r"D:\drowsiness-detection\src\test_video.mp4"  # ← change ici
models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
MODEL_PATH = os.path.join(models_dir, 'best_model_mobilenetv2.h5')

# ── Charger le modèle ─────────────────────────────────────────────────────────
print("Chargement du modèle...")
model = load_model(MODEL_PATH)
print("✓ Modèle chargé\n")

# ── Charger le détecteur de visage ───────────────────────────────────────────
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

# ── Ouvrir la vidéo ───────────────────────────────────────────────────────────
cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    print(f"❌ Impossible d'ouvrir la vidéo : {VIDEO_PATH}")
    exit(1)

# Infos vidéo
fps        = cap.get(cv2.CAP_PROP_FPS)
width      = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height     = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
print(f"Vidéo      : {VIDEO_PATH}")
print(f"Résolution : {width}x{height}")
print(f"FPS        : {fps:.1f}")
print(f"Frames     : {total_frames}")
print(f"\nAppuie sur 'q' pour quitter\n")

# ── Sauvegarder la vidéo annotée ─────────────────────────────────────────────
output_dir  = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'outputs')
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, 'predict_output.mp4')
fourcc      = cv2.VideoWriter_fourcc(*'mp4v')
out         = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

# ── Compteurs pour statistiques ───────────────────────────────────────────────
frame_count   = 0
drowsy_count  = 0
awake_count   = 0
no_face_count = 0

# ── Traitement frame par frame ────────────────────────────────────────────────
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1
    display = frame.copy()

    # Convertir en niveaux de gris pour la détection de visage
    gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(80, 80)
    )

    if len(faces) == 0:
        # Aucun visage détecté — prédire sur la frame entière
        no_face_count += 1
        face_img = cv2.resize(frame, (IMG_SIZE, IMG_SIZE))
        face_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
        face_arr = np.expand_dims(face_img, axis=0).astype(np.float32)
        face_arr = preprocess_input(face_arr)

        pred  = model.predict(face_arr, verbose=0)[0][0]
        label = "DROWSY" if pred > THRESHOLD else "AWAKE"
        color = (0, 0, 255) if label == "DROWSY" else (0, 255, 0)
        conf  = pred if label == "DROWSY" else 1 - pred

        if label == "DROWSY":
            drowsy_count += 1
        else:
            awake_count += 1

        # Overlay texte sur la frame
        cv2.putText(display, f"{label} ({conf*100:.1f}%)",
                    (20, 50), cv2.FONT_HERSHEY_SIMPLEX,
                    1.2, color, 3)

    else:
        # Visage(s) détecté(s)
        for (x, y, w, h) in faces:
            # Extraire et préparer le visage
            face_roi = frame[y:y+h, x:x+w]
            face_img = cv2.resize(face_roi, (IMG_SIZE, IMG_SIZE))
            face_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
            face_arr = np.expand_dims(face_img, axis=0).astype(np.float32)
            face_arr = preprocess_input(face_arr)

            # Prédiction
            pred  = model.predict(face_arr, verbose=0)[0][0]
            label = "DROWSY" if pred > THRESHOLD else "AWAKE"
            color = (0, 0, 255) if label == "DROWSY" else (0, 255, 0)
            conf  = pred if label == "DROWSY" else 1 - pred

            if label == "DROWSY":
                drowsy_count += 1
            else:
                awake_count += 1

            # Rectangle autour du visage
            cv2.rectangle(display, (x, y), (x+w, y+h), color, 2)

            # Label au-dessus du visage
            label_text = f"{label} ({conf*100:.1f}%)"
            label_y    = y - 10 if y - 10 > 10 else y + 20
            cv2.putText(display, label_text,
                        (x, label_y), cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, color, 2)

    # ── Barre d'info en bas ───────────────────────────────────────────────────
    bar_h  = 40
    bar_y  = height - bar_h
    overlay = display.copy()
    cv2.rectangle(overlay, (0, bar_y), (width, height), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, display, 0.4, 0, display)

    progress = f"Frame {frame_count}/{total_frames}"
    stats    = f"AWAKE: {awake_count}  DROWSY: {drowsy_count}"
    cv2.putText(display, progress,
                (10, bar_y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1)
    cv2.putText(display, stats,
                (width//2 - 100, bar_y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1)

    # ── Alerte DROWSY plein écran ─────────────────────────────────────────────
    if label == "DROWSY":
        alert_overlay = display.copy()
        cv2.rectangle(alert_overlay, (0, 0), (width, 80), (0, 0, 200), -1)
        cv2.addWeighted(alert_overlay, 0.4, display, 0.6, 0, display)
        cv2.putText(display, "⚠ DROWSINESS DETECTED ⚠",
                    (width//2 - 220, 55),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

    # Écrire dans la vidéo de sortie
    out.write(display)

    # Afficher
    cv2.imshow("Drowsiness Detection", display)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("\nArrêt manuel.")
        break

# ── Libération des ressources ─────────────────────────────────────────────────
cap.release()
out.release()
cv2.destroyAllWindows()

# ── Résumé final ──────────────────────────────────────────────────────────────
total = awake_count + drowsy_count
print("\n" + "="*50)
print("RÉSUMÉ DE L'ANALYSE")
print("="*50)
print(f"Frames analysées : {frame_count}")
print(f"AWAKE            : {awake_count} ({awake_count/total*100:.1f}%)")
print(f"DROWSY           : {drowsy_count} ({drowsy_count/total*100:.1f}%)")
print(f"Sans visage      : {no_face_count}")
print(f"\n✓ Vidéo annotée sauvegardée : {output_path}")