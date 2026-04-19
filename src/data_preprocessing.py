import os
from tensorflow.keras.preprocessing.image import ImageDataGenerator

IMG_SIZE   = 224   # taille native MobileNetV2
BATCH_SIZE = 32

DATASET_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dataset')


def get_data_generators(img_size=IMG_SIZE, batch_size=BATCH_SIZE, dataset_dir=DATASET_DIR):

    train_dir = os.path.join(dataset_dir, 'train')
    val_dir   = os.path.join(dataset_dir, 'val')

    # MobileNetV2 attend des pixels dans [-1, 1]
    from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

    train_datagen = ImageDataGenerator(
        preprocessing_function=preprocess_input,
        rotation_range=10,
        zoom_range=0.1,
        horizontal_flip=True,
        brightness_range=[0.8, 1.2],
        shear_range=0.1,
    )

    val_datagen = ImageDataGenerator(
        preprocessing_function=preprocess_input
    )

    train_gen = train_datagen.flow_from_directory(
        train_dir,
        target_size=(img_size, img_size),
        batch_size=batch_size,
        class_mode='binary',
        classes=['awake', 'drowsy'],  # 0=awake, 1=drowsy
        shuffle=True,
        seed=42
    )

    val_gen = val_datagen.flow_from_directory(
        val_dir,
        target_size=(img_size, img_size),
        batch_size=batch_size,
        class_mode='binary',
        classes=['awake', 'drowsy'],
        shuffle=False
    )

    print(f"Classes : {train_gen.class_indices}")
    print(f"Train   : {train_gen.samples} images")
    print(f"Val     : {val_gen.samples} images")

    return train_gen, val_gen


if __name__ == "__main__":
    train_gen, val_gen = get_data_generators()