from flask import Flask, request, jsonify, render_template
import os
import logging
from collections import deque
from io import BytesIO
from PIL import Image
import base64
import time

app = Flask(__name__, template_folder='templates')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("✓ Flask started - lightweight imports OK")

# ─── CONFIG ───────────────────────────────────────────────────────────
IMG_SIZE = 224
THRESHOLD = float(os.environ.get('THRESHOLD', 0.4))
SMOOTH_WIN = 5
DROWSY_LIMIT = 2
MODEL_PATH = os.environ.get('MODEL_PATH', 'models/best_model_mobilenetv2.h5')

# ─── GLOBAL STATE ──────────────────────────────────────────────────────
history = deque(maxlen=SMOOTH_WIN)
drowsy_counter = 0

# Heavy imports will be loaded on first use
deps_cache = {
    'cv2': None,
    'np': None,
    'model': None,
    'face_cascade': None,
    'eye_cascade': None,
    'preprocess_input': None,
    'loaded': False,
    'error': None
}


def load_heavy_deps():
    """Load TensorFlow, OpenCV, etc. on first use (lazy loading)"""
    if deps_cache['loaded']:
        return

    if deps_cache['error']:
        raise Exception(deps_cache['error'])

    try:
        logger.info(
            "📦 Loading heavy dependencies (this may take 10-20 seconds)...")
        start = time.time()

        # Import heavy libs
        import cv2
        import numpy as np
        from tensorflow.keras.models import load_model
        from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

        deps_cache['cv2'] = cv2
        deps_cache['np'] = np
        deps_cache['preprocess_input'] = preprocess_input

        logger.info("✓ TensorFlow/OpenCV imports loaded")

        # Load model
        logger.info(f"Loading model from {MODEL_PATH}...")
        deps_cache['model'] = load_model(MODEL_PATH)
        logger.info("✓ Model loaded")

        # Load cascades
        deps_cache['face_cascade'] = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        deps_cache['eye_cascade'] = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_eye.xml')
        logger.info("✓ Cascades loaded")

        deps_cache['loaded'] = True
        elapsed = time.time() - start
        logger.info(f"✓✓✓ All dependencies ready in {elapsed:.1f}s ✓✓✓")

    except Exception as e:
        msg = f"❌ Error loading dependencies: {e}"
        logger.error(msg, exc_info=True)
        deps_cache['error'] = msg
        raise

# ─── ROUTES ────────────────────────────────────────────────────────────


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/_ah/warmup', methods=['GET'])
def warmup_internal():
    """App Engine internal warmup request"""
    logger.info("🔥 App Engine warmup request")
    try:
        load_heavy_deps()
        logger.info("✓ App Engine warmup complete")
    except Exception as e:
        logger.error(f"App Engine warmup failed: {e}", exc_info=True)
    return '', 200


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200


@app.route('/warmup', methods=['GET'])
def warmup():
    """Called by App Engine to warm up the instance - preloads dependencies"""
    try:
        logger.info("🔥 Warmup request - preloading dependencies...")
        load_heavy_deps()
        logger.info("✓ Warmup complete")
        return jsonify({'status': 'warmed up'}), 200
    except Exception as e:
        logger.error(f"Warmup failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/reset', methods=['POST'])
def reset():
    global history, drowsy_counter
    history.clear()
    drowsy_counter = 0
    return jsonify({'status': 'reset ok'})


@app.route('/predict-realtime', methods=['POST'])
def predict_realtime():
    global history, drowsy_counter

    try:
        # Load heavy dependencies on first use
        load_heavy_deps()

        if deps_cache['model'] is None:
            return jsonify({'error': 'Model not available'}), 500

        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'error': 'No image provided'}), 400

        # Get cached dependencies
        cv2 = deps_cache['cv2']
        np = deps_cache['np']
        model = deps_cache['model']
        face_cascade = deps_cache['face_cascade']
        eye_cascade = deps_cache['eye_cascade']
        preprocess_input = deps_cache['preprocess_input']

        # Decode image
        image_bytes = base64.b64decode(data['image'])
        image = Image.open(BytesIO(image_bytes))
        frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        frame = cv2.resize(frame, (640, 480))

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=6, minSize=(100, 100)
        )

        results = []

        for (x, y, w, h) in faces:
            face = frame[y:y+h, x:x+w]
            gray_face = gray[y:y+h, x:x+w]

            face_r = cv2.resize(face, (IMG_SIZE, IMG_SIZE))
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

                scale_x = w / IMG_SIZE
                scale_y = h / IMG_SIZE
                eye_boxes.append({
                    'x': int(x + ex * scale_x),
                    'y': int(y + ey * scale_y),
                    'w': int(ew * scale_x),
                    'h': int(eh * scale_y)
                })

            avg_pred = float(np.mean(eye_preds)) if eye_preds else 0.0
            history.append(avg_pred)
            stable_pred = float(np.mean(history))

            if stable_pred > THRESHOLD:
                drowsy_counter += 1
            else:
                drowsy_counter = 0

            state = 'DROWSY' if drowsy_counter > DROWSY_LIMIT else 'AWAKE'

            results.append({
                'state': state,
                'confidence': round(stable_pred, 4),
                'drowsy_counter': drowsy_counter,
                'face': {'x': int(x), 'y': int(y), 'w': int(w), 'h': int(h)},
                'eyes': eye_boxes
            })

        if len(faces) == 0:
            drowsy_counter = 0

        return jsonify({
            'predictions': results,
            'total_faces': len(faces)
        }), 200

    except Exception as e:
        logger.error(f"Error /predict-realtime: {e}", exc_info=True)
        return jsonify({'error': str(e), 'type': type(e).__name__}), 500


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
