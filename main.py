#!/usr/bin/env python3
"""
Drowsiness Detection Flask API - Ultra-minimalist startup
Only Flask initialized at startup. ML loads on first real request.
"""
import base64
from flask import Flask, request, jsonify, render_template
from collections import deque
import logging
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask ONLY
app = Flask(__name__, template_folder='templates')
logger.info("Flask initialized")

IMG_SIZE = 224
THRESHOLD = float(os.environ.get('THRESHOLD', 0.4))
SMOOTH_WIN = 5
DROWSY_LIMIT = 2
MODEL_PATH = os.environ.get('MODEL_PATH', 'models/best_model_mobilenetv2.h5')

history = deque(maxlen=SMOOTH_WIN)
drowsy_counter = 0

# Lazy-loaded ML libraries and model
_model = None
_face_cascade = None
_eye_cascade = None
_np = None
_cv2 = None
_Image = None
_BytesIO = None
_preprocess_input = None
_load_error = None


def _ensure_model_loaded():
    """Lazy load model on first request"""
    global _model, _face_cascade, _eye_cascade, _np, _cv2, _Image, _BytesIO, _preprocess_input, _load_error

    if _model is not None:
        return True  # Already loaded

    if _load_error:
        return False  # Failed before

    try:
        logger.info("Loading ML libraries and model...")

        import numpy as np_temp
        import cv2 as cv2_temp
        from PIL import Image as Image_temp
        from io import BytesIO as BytesIO_temp

        _np = np_temp
        _cv2 = cv2_temp
        _Image = Image_temp
        _BytesIO = BytesIO_temp

        import tensorflow as tf
        from tensorflow.keras.models import load_model as tf_load_model
        from tensorflow.keras.applications.mobilenet_v2 import preprocess_input as pp_input

        tf.get_logger().setLevel('ERROR')
        _preprocess_input = pp_input

        logger.info("Loading model from " + MODEL_PATH)
        _model = tf_load_model(MODEL_PATH)

        logger.info("Loading Haar cascades...")
        _face_cascade = _cv2.CascadeClassifier(
            _cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        _eye_cascade = _cv2.CascadeClassifier(
            _cv2.data.haarcascades + 'haarcascade_eye.xml')

        logger.info("Model fully loaded!")
        return True

    except Exception as e:
        logger.error(f"Failed to load model: {e}", exc_info=True)
        _load_error = str(e)
        return False


@app.route('/')
def index():
    """Serve the HTML UI"""
    return render_template('index.html')


@app.route('/_ah/warmup', methods=['GET'])
def warmup():
    """App Engine warmup endpoint"""
    return '', 200


@app.route('/health', methods=['GET'])
def health():
    """Health check - responds immediately"""
    return jsonify({'status': 'ok', 'model_ready': _model is not None}), 200


@app.route('/reset', methods=['POST'])
def reset():
    """Reset prediction state"""
    global history, drowsy_counter
    history.clear()
    drowsy_counter = 0
    return jsonify({'status': 'ok'})


@app.route('/predict-realtime', methods=['POST'])
def predict_realtime():
    """Process a frame and return predictions"""
    global history, drowsy_counter

    # Lazy load on first request
    if not _ensure_model_loaded():
        if _load_error:
            return jsonify({'error': f'Model failed to load: {_load_error}'}), 500
        return jsonify({'error': 'Model is loading... please retry', 'status': 'loading'}), 503

    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'error': 'No image provided'}), 400

        # Decode base64 image
        img_bytes = base64.b64decode(data['image'])
        img = _Image.open(_BytesIO(img_bytes))
        frame = _cv2.cvtColor(_np.array(img), _cv2.COLOR_RGB2BGR)
        frame = _cv2.resize(frame, (640, 480))

        # Detect faces
        gray = _cv2.cvtColor(frame, _cv2.COLOR_BGR2GRAY)
        faces = _face_cascade.detectMultiScale(
            gray, 1.1, 6, minSize=(100, 100))

        results = []
        for (x, y, w, h) in faces:
            face_r = _cv2.resize(frame[y:y+h, x:x+w], (IMG_SIZE, IMG_SIZE))
            gray_face_r = _cv2.resize(gray[y:y+h, x:x+w], (IMG_SIZE, IMG_SIZE))

            # Detect eyes in face
            eyes = _eye_cascade.detectMultiScale(
                gray_face_r, 1.1, 8, minSize=(20, 20))

            eye_preds = []
            eye_boxes = []

            # Process each eye
            for (ex, ey, ew, eh) in eyes[:2]:
                eye_roi = face_r[ey:ey+eh, ex:ex+ew]
                if eye_roi.size == 0:
                    continue

                # Prepare for model
                roi = _cv2.resize(eye_roi, (IMG_SIZE, IMG_SIZE))
                roi = _cv2.cvtColor(roi, _cv2.COLOR_BGR2RGB)
                roi = _np.expand_dims(roi.astype(_np.float32), axis=0)
                roi = _preprocess_input(roi)

                # Get prediction
                pred = _model.predict(roi, verbose=0)[0][0]
                eye_preds.append(float(pred))

                # Eye box coordinates
                sx, sy = w / IMG_SIZE, h / IMG_SIZE
                eye_boxes.append({
                    'x': int(x + ex * sx),
                    'y': int(y + ey * sy),
                    'w': int(ew * sx),
                    'h': int(eh * sy)
                })

            # Average predictions across eyes
            avg_pred = float(_np.mean(eye_preds)) if eye_preds else 0.0
            history.append(avg_pred)
            stable_pred = float(_np.mean(history))

            # Update drowsy counter
            if stable_pred > THRESHOLD:
                drowsy_counter += 1
            else:
                drowsy_counter = 0

            # Determine state
            state = 'DROWSY' if drowsy_counter > DROWSY_LIMIT else 'AWAKE'
            results.append({
                'state': state,
                'confidence': round(stable_pred, 4),
                'drowsy_counter': drowsy_counter,
                'face': {'x': int(x), 'y': int(y), 'w': int(w), 'h': int(h)},
                'eyes': eye_boxes
            })

        # Reset counter if no faces
        if len(faces) == 0:
            drowsy_counter = 0

        return jsonify({'predictions': results, 'total_faces': len(faces)}), 200

    except Exception as e:
        logger.error(f"Error in predict_realtime: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8080)
