"""
Version diagnostic simplifiée pour identifier les problèmes
"""
from flask import Flask, jsonify, render_template, request
import os
import logging
from pathlib import Path

app = Flask(__name__, template_folder='templates')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variables globales
deps = {
    'model': None,
    'cv2': None,
    'np': None,
    'loaded': False,
    'errors': []
}

MODEL_PATH = 'models/best_model_mobilenetv2.h5'


def check_model_exists():
    """Vérifie si le modèle existe"""
    import os
    cwd = os.getcwd()
    model_path = os.path.join(cwd, MODEL_PATH)
    exists = os.path.exists(model_path)
    size_mb = os.path.getsize(model_path) / (1024**2) if exists else 0
    return {
        'cwd': cwd,
        'expected_path': model_path,
        'exists': exists,
        'size_mb': round(size_mb, 2) if exists else 0
    }


def load_dependencies():
    """Charge les dépendances"""
    if deps['loaded']:
        return

    logger.info("🔄 Tentative de chargement des dépendances...")

    try:
        import cv2
        deps['cv2'] = cv2
        logger.info("✓ OpenCV chargé")
    except Exception as e:
        msg = f"❌ Erreur OpenCV: {e}"
        logger.error(msg)
        deps['errors'].append(msg)
        return

    try:
        import numpy as np
        deps['np'] = np
        logger.info("✓ NumPy chargé")
    except Exception as e:
        msg = f"❌ Erreur NumPy: {e}"
        logger.error(msg)
        deps['errors'].append(msg)
        return

    try:
        from tensorflow.keras.models import load_model
        logger.info("✓ TensorFlow importé")

        # Vérifier le modèle
        check = check_model_exists()
        logger.info(f"État du modèle: {check}")

        if not check['exists']:
            msg = f"❌ Modèle NOT FOUND à {check['expected_path']}"
            logger.error(msg)
            deps['errors'].append(msg)
            return

        # Charger le modèle
        logger.info(f"Chargement du modèle ({check['size_mb']} MB)...")
        deps['model'] = load_model(MODEL_PATH)
        logger.info("✓ Modèle chargé avec succès")

    except Exception as e:
        msg = f"❌ Erreur TensorFlow/Modèle: {e}"
        logger.error(msg, exc_info=True)
        deps['errors'].append(msg)
        return

    deps['loaded'] = True
    logger.info("✓✓✓ TOUTES LES DÉPENDANCES CHARGÉES ✓✓✓")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200


@app.route('/diagnostic')
def diagnostic():
    """Endpoint de diagnostic"""
    load_dependencies()
    return jsonify({
        'model_check': check_model_exists(),
        'dependencies_loaded': deps['loaded'],
        'errors': deps['errors'],
        'model_type': str(type(deps['model']).__name__) if deps['model'] else None
    })


@app.route('/predict-realtime', methods=['POST'])
def predict_realtime():
    """Version simple pour tester"""
    try:
        load_dependencies()

        if not deps['loaded']:
            return jsonify({
                'error': 'Dependencies not loaded',
                'errors': deps['errors']
            }), 500

        if deps['model'] is None:
            return jsonify({
                'error': 'Model is None',
                'errors': deps['errors']
            }), 500

        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'error': 'No image provided'}), 400

        # Test simple
        return jsonify({
            'status': 'ok',
            'model_loaded': True,
            'image_received': len(data['image']) > 0,
            'message': 'Model test successful'
        })

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return jsonify({
            'error': str(e),
            'type': type(e).__name__,
            'errors': deps['errors']
        }), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
