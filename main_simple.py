from flask import Flask, render_template, request, jsonify
import logging

app = Flask(__name__, template_folder='templates')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Flask app initializing...")


@app.route('/')
def index():
    logger.info("Index route called")
    return render_template('index.html')


@app.route('/health')
def health():
    logger.info("Health check")
    return jsonify({'status': 'OK'}), 200


@app.route('/reset', methods=['POST'])
def reset():
    logger.info("Reset called")
    return jsonify({'status': 'reset ok'}), 200


logger.info("Flask app initialized successfully!")

if __name__ == '__main__':
    app.run(debug=False, port=8080)
