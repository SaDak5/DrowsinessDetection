import cv2
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from collections import deque
import winsound
import threading
import time

# ───────────────────── CONFIG ─────────────────────
IMG_SIZE = 224

# ⚡ OPTIMISATION VITESSE
THRESHOLD = 0.4
SMOOTH_WINDOW = 5   # ↓ réduit (avant 10)
DROWSY_LIMIT = 2    # ↓ réduit (avant 5)

# ───────────────────── MODEL ──────────────────────
model = load_model("models/best_model_mobilenetv2.h5")

# ───────────────────── HAAR ───────────────────────
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

eye_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_eye.xml"
)

# ───────────────────── CAMERA ──────────────────────
cap = cv2.VideoCapture(0)

# ⚡ OPTIMISATION FPS
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

# ───────────────────── MEMORY ──────────────────────
history = deque(maxlen=SMOOTH_WINDOW)
drowsy_counter = 0

# ───────────────────── SOUND CONTROL ──────────────
sound_active = False

def beep_loop():
    while sound_active:
        winsound.Beep(1200, 300)
        time.sleep(0.05)

def start_beep():
    global sound_active
    if not sound_active:
        sound_active = True
        threading.Thread(target=beep_loop, daemon=True).start()

def stop_beep():
    global sound_active
    sound_active = False

# ───────────────────── PREPROCESS ──────────────────
def preprocess(roi):
    if roi is None or roi.size == 0:
        return None
    roi = cv2.resize(roi, (IMG_SIZE, IMG_SIZE))
    roi = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
    roi = np.expand_dims(roi.astype(np.float32), axis=0)
    return preprocess_input(roi)

# ───────────────────── LOOP ─────────────────────────
frame_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # ⚡ SKIP FRAME POUR GAGNER EN VITESSE
    frame_count += 1
    if frame_count % 2 == 0:
        continue

    frame = cv2.resize(frame, (640, 480))
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=6,
        minSize=(100, 100)
    )

    for (x, y, w, h) in faces:
        face = frame[y:y+h, x:x+w]
        gray_face = gray[y:y+h, x:x+w]

        face = cv2.resize(face, (224, 224))
        gray_face = cv2.resize(gray_face, (224, 224))

        eyes = eye_cascade.detectMultiScale(
            gray_face,
            scaleFactor=1.1,
            minNeighbors=8,
            minSize=(20, 20)
        )

        predictions = []

        for (ex, ey, ew, eh) in eyes[:2]:
            eye_roi = face[ey:ey+eh, ex:ex+ew]

            processed = preprocess(eye_roi)
            if processed is None:
                continue

            pred = model.predict(processed, verbose=0)[0][0]
            predictions.append(pred)

        avg_pred = np.mean(predictions) if len(predictions) > 0 else 0.0

        history.append(avg_pred)
        stable_pred = np.mean(history)

        # ───────── DECISION RAPIDE ─────────
        if stable_pred > THRESHOLD:
            drowsy_counter += 1
        else:
            drowsy_counter = 0

        current_state = "DROWSY" if drowsy_counter > DROWSY_LIMIT else "AWAKE"

        # ───────── BEEP CONTINU ─────────
        if current_state == "DROWSY":
            start_beep()
        else:
            stop_beep()

        # ───────── DISPLAY ─────────
        color = (0, 0, 255) if current_state == "DROWSY" else (0, 255, 0)

        cv2.putText(frame,
                    f"{current_state} ({stable_pred:.2f})",
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    color,
                    2)

        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)

    cv2.imshow("Drowsiness Detection - FAST", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# ───────────────────── CLEAN ──────────────────────
stop_beep()
cap.release()
cv2.destroyAllWindows()