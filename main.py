from flask import Flask, request, jsonify, render_template
import cv2
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
import os
from io import BytesIO
from PIL import Image
import base64
import logging
from collections import deque

app = Flask(__name__, template_folder='templates')

# ─── CONFIG (identique à realtime_detection.py) ───────────────────────────────
IMG_SIZE     = 224
THRESHOLD    = float(os.environ.get('THRESHOLD', 0.4))   # même valeur
SMOOTH_WIN   = 5
DROWSY_LIMIT = 2
MODEL_PATH   = os.environ.get('MODEL_PATH', 'models/best_model_mobilenetv2.h5')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── LOAD MODEL ───────────────────────────────────────────────────────────────
try:
    logger.info(f"Chargement du modèle depuis {MODEL_PATH}...")
    model = load_model(MODEL_PATH)
    logger.info("✓ Modèle chargé avec succès")
except Exception as e:
    logger.error(f"❌ Erreur chargement modèle: {e}")
    model = None

# ─── CASCADE CLASSIFIERS ──────────────────────────────────────────────────────
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade  = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

# ─── SESSION STATE (lissage par session) ──────────────────────────────────────
# On garde un historique par client (simplifié : global pour démo)
history        = deque(maxlen=SMOOTH_WIN)
drowsy_counter = 0

# ─── ROUTES ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/reset', methods=['POST'])
def reset():
    """Réinitialise l'état de lissage (appelé au démarrage de la caméra)"""
    global history, drowsy_counter
    history.clear()
    drowsy_counter = 0
    return jsonify({'status': 'reset ok'})


@app.route('/predict-realtime', methods=['POST'])
def predict_realtime():
    """
    Reçoit une frame base64, applique la même logique que realtime_detection.py :
    - Haar face + eye detection
    - MobileNetV2 sur chaque œil
    - Lissage sur SMOOTH_WIN frames
    - Compteur drowsy_counter
    """
    global history, drowsy_counter

    try:
        if model is None:
            return jsonify({'error': 'Modèle non disponible'}), 500

        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'error': 'No image provided'}), 400

        # ── Décoder l'image ──
        image_bytes = base64.b64decode(data['image'])
        image       = Image.open(BytesIO(image_bytes))
        frame       = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        frame       = cv2.resize(frame, (640, 480))

        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=6, minSize=(100, 100)
        )

        results = []

        for (x, y, w, h) in faces:
            face      = frame[y:y+h, x:x+w]
            gray_face = gray[y:y+h, x:x+w]

            face_r      = cv2.resize(face,      (IMG_SIZE, IMG_SIZE))
            gray_face_r = cv2.resize(gray_face, (IMG_SIZE, IMG_SIZE))

            eyes = eye_cascade.detectMultiScale(
                gray_face_r, scaleFactor=1.1, minNeighbors=8, minSize=(20, 20)
            )

            eye_preds = []
            eye_boxes = []

            for (ex, ey, ew, eh) in eyes[:2]:
                eye_roi = face_r[ey:ey+eh, ex:ex+ew]
                if eye_roi.size == 0:
                    continue

                roi = cv2.resize(eye_roi, (IMG_SIZE, IMG_SIZE))
                roi = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
                roi = np.expand_dims(roi.astype(np.float32), axis=0)
                roi = preprocess_input(roi)

                pred = model.predict(roi, verbose=0)[0][0]
                eye_preds.append(float(pred))

                # Coordonnées yeux ramenées à la frame originale
                scale_x = w / IMG_SIZE
                scale_y = h / IMG_SIZE
                eye_boxes.append({
                    'x': int(x + ex * scale_x),
                    'y': int(y + ey * scale_y),
                    'w': int(ew * scale_x),
                    'h': int(eh * scale_y)
                })

            # ── Lissage identique à realtime_detection.py ──
            avg_pred    = float(np.mean(eye_preds)) if eye_preds else 0.0
            history.append(avg_pred)
            stable_pred = float(np.mean(history))

            if stable_pred > THRESHOLD:
                drowsy_counter += 1
            else:
                drowsy_counter = 0

            state = 'DROWSY' if drowsy_counter > DROWSY_LIMIT else 'AWAKE'

            results.append({
                'state':      state,
                'confidence': round(stable_pred, 4),
                'drowsy_counter': drowsy_counter,
                'face': {'x': int(x), 'y': int(y), 'w': int(w), 'h': int(h)},
                'eyes': eye_boxes
            })

        # Si aucun visage → reset compteur (comme dans la boucle originale)
        if len(faces) == 0:
            drowsy_counter = 0

        return jsonify({
            'predictions': results,
            'total_faces': len(faces)
        }), 200

    except Exception as e:
        logger.error(f"Erreur /predict-realtime: {e}")
        return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)