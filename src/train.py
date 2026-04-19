import os
import numpy as np
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout, BatchNormalization
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from data_preprocessing import get_data_generators
from sklearn.utils.class_weight import compute_class_weight

# ── Paramètres ────────────────────────────────────────────────────────────────
IMG_SIZE        = 224   # taille native MobileNetV2
BATCH_SIZE      = 32
EPOCHS_INITIAL  = 20
EPOCHS_FINETUNE = 10
LR_INITIAL      = 1e-4
LR_FINETUNE     = 1e-5

models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
os.makedirs(models_dir, exist_ok=True)

# ── Données ───────────────────────────────────────────────────────────────────
print("Chargement des données...")
train_gen, val_gen = get_data_generators(img_size=IMG_SIZE, batch_size=BATCH_SIZE)

# ── Poids des classes ─────────────────────────────────────────────────────────
print("\nCalcul des poids des classes...")
class_weights = compute_class_weight(
    'balanced',
    classes=np.unique(train_gen.classes),
    y=train_gen.classes
)
class_weights_dict = dict(enumerate(class_weights))
print(f"Poids des classes : {class_weights_dict}")

# ── Architecture MobileNetV2 ──────────────────────────────────────────────────
print("\nCréation du modèle MobileNetV2...")
base_model = MobileNetV2(
    weights='imagenet',
    include_top=False,
    input_shape=(IMG_SIZE, IMG_SIZE, 3)
)
base_model.trainable = False  # geler toutes les couches au début

# ── Tête de classification ────────────────────────────────────────────────────
x = GlobalAveragePooling2D()(base_model.output)
x = BatchNormalization()(x)
x = Dropout(0.5)(x)
x = Dense(128, activation='relu')(x)
x = BatchNormalization()(x)
x = Dropout(0.3)(x)
output = Dense(1, activation='sigmoid')(x)

model = Model(inputs=base_model.input, outputs=output)
model.compile(
    optimizer=Adam(learning_rate=LR_INITIAL),
    loss='binary_crossentropy',
    metrics=['accuracy']
)
model.summary()

# ── Callbacks ─────────────────────────────────────────────────────────────────
best_path = os.path.join(models_dir, 'best_model_mobilenetv2.h5')

callbacks = [
    EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True),
    ModelCheckpoint(best_path, monitor='val_accuracy', save_best_only=True, verbose=1),
    ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3, min_lr=1e-7, verbose=1),
]

# ── Phase 1 : couches de base gelées ─────────────────────────────────────────
print("\n=== PHASE 1 : Entraînement initial (couches gelées) ===")
history1 = model.fit(
    train_gen,
    validation_data=val_gen,
    epochs=EPOCHS_INITIAL,
    class_weight=class_weights_dict,
    callbacks=callbacks,
    verbose=1
)
print(f"Phase 1 — meilleure val_accuracy : {max(history1.history['val_accuracy']):.4f}")

# ── Phase 2 : fine-tuning ─────────────────────────────────────────────────────
print("\n=== PHASE 2 : Fine-tuning (30 dernières couches) ===")
base_model.trainable = True

# MobileNetV2 a 154 couches — on gèle tout sauf les 30 dernières
for layer in base_model.layers[:-30]:
    layer.trainable = False

# Garder les BatchNormalization gelées pour stabilité
for layer in base_model.layers:
    if isinstance(layer, BatchNormalization):
        layer.trainable = False

model.compile(
    optimizer=Adam(learning_rate=LR_FINETUNE),
    loss='binary_crossentropy',
    metrics=['accuracy']
)

print(f"Couches entraînables : {sum(1 for l in model.layers if l.trainable)}")

history2 = model.fit(
    train_gen,
    validation_data=val_gen,
    epochs=EPOCHS_FINETUNE,
    class_weight=class_weights_dict,
    callbacks=callbacks,
    verbose=1
)
print(f"Phase 2 — meilleure val_accuracy : {max(history2.history['val_accuracy']):.4f}")

# ── Sauvegarde ────────────────────────────────────────────────────────────────
final_path = os.path.join(models_dir, 'fatigue_detection_mobilenetv2_final.h5')
model.save(final_path)
print(f"\n✓ Modèle final        : {final_path}")
print(f"✓ Meilleur checkpoint : {best_path}")
print("\n=== ENTRAÎNEMENT TERMINÉ ===")