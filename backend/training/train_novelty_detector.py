"""
Trains an unsupervised convolutional autoencoder on ONLY the apple/banana
images already collected for the classifier (data/raw/apple, data/raw/banana)
-- no extra images or datasets.

Purpose: the classifier is a closed-set 2-class softmax, so it always picks
"apple" or "banana" with high confidence even for images of neither (e.g. a
photo of a table) -- softmax confidence alone cannot detect that. Instead we
train a second, small model to learn what apple/banana photos look like, by
reconstructing them. A genuine apple/banana photo reconstructs with low
error. A photo unlike anything in the training set (different shapes,
colours, composition -- a table, a room, a person, ...) reconstructs with
high error, and gets flagged as "not recognised" before the classifier runs.

Usage:
    python backend/training/train_novelty_detector.py
"""
import json
from pathlib import Path

import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data" / "raw"
MODEL_DIR = REPO_ROOT / "backend" / "models"
MODEL_PATH = MODEL_DIR / "novelty_autoencoder.keras"
THRESHOLD_PATH = MODEL_DIR / "novelty_threshold.json"

IMAGE_SIZE = (128, 128)
BATCH_SIZE = 32
SEED = 42
EPOCHS = 30
# Percentile of held-out apple/banana reconstruction errors used as the
# rejection cutoff. 99 means ~1% of genuine apple/banana photos would be
# (incorrectly) flagged as unrecognised -- a reasonable trade-off against
# catching clearly-unrelated images.
THRESHOLD_PERCENTILE = 99.0


def _load_all_image_paths():
    paths = []
    for label_dir in sorted(DATA_DIR.iterdir()):
        if label_dir.is_dir():
            paths.extend(str(p) for p in label_dir.glob("*.jpg"))
    return paths


def _make_dataset(paths):
    def _load(path):
        raw = tf.io.read_file(path)
        img = tf.io.decode_jpeg(raw, channels=3)
        img = tf.image.resize(img, IMAGE_SIZE)
        img = img / 255.0
        return img, img  # autoencoder target == input

    ds = tf.data.Dataset.from_tensor_slices(paths)
    ds = ds.shuffle(len(paths), seed=SEED)
    ds = ds.map(_load, num_parallel_calls=tf.data.AUTOTUNE)
    ds = ds.batch(BATCH_SIZE)
    ds = ds.prefetch(tf.data.AUTOTUNE)
    return ds


def build_autoencoder() -> tf.keras.Model:
    inputs = layers.Input(shape=(*IMAGE_SIZE, 3))

    x = layers.Conv2D(16, 3, padding="same", activation="relu")(inputs)
    x = layers.MaxPooling2D()(x)  # 64x64
    x = layers.Conv2D(32, 3, padding="same", activation="relu")(x)
    x = layers.MaxPooling2D()(x)  # 32x32
    x = layers.Conv2D(64, 3, padding="same", activation="relu")(x)
    encoded = layers.MaxPooling2D()(x)  # 16x16x64 bottleneck

    x = layers.Conv2D(64, 3, padding="same", activation="relu")(encoded)
    x = layers.UpSampling2D()(x)  # 32x32
    x = layers.Conv2D(32, 3, padding="same", activation="relu")(x)
    x = layers.UpSampling2D()(x)  # 64x64
    x = layers.Conv2D(16, 3, padding="same", activation="relu")(x)
    x = layers.UpSampling2D()(x)  # 128x128
    outputs = layers.Conv2D(3, 3, padding="same", activation="sigmoid")(x)

    model = models.Model(inputs, outputs, name="novelty_autoencoder")
    model.compile(optimizer="adam", loss="mse")
    return model


def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    all_paths = _load_all_image_paths()
    print(f"Total apple/banana images: {len(all_paths)}")

    rng = np.random.default_rng(SEED)
    indices = rng.permutation(len(all_paths))
    split = int(len(all_paths) * 0.9)
    train_paths = [all_paths[i] for i in indices[:split]]
    calib_paths = [all_paths[i] for i in indices[split:]]
    print(f"Train: {len(train_paths)}  Calibration (held-out): {len(calib_paths)}")

    train_ds = _make_dataset(train_paths)
    calib_ds = _make_dataset(calib_paths)

    model = build_autoencoder()
    model.summary()

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="loss", patience=5, restore_best_weights=True
        ),
    ]
    model.fit(train_ds, epochs=EPOCHS, callbacks=callbacks)

    # Calibrate the rejection threshold on held-out apple/banana images
    # (never seen during training) so the threshold reflects genuine
    # generalisation error, not memorisation.
    errors = []
    for batch_x, _ in calib_ds:
        recon = model.predict(batch_x, verbose=0)
        mse = np.mean(np.square(batch_x.numpy() - recon), axis=(1, 2, 3))
        errors.extend(mse.tolist())

    threshold = float(np.percentile(errors, THRESHOLD_PERCENTILE))
    print(f"Held-out reconstruction error: mean={np.mean(errors):.6f}, "
          f"p50={np.percentile(errors, 50):.6f}, "
          f"p{THRESHOLD_PERCENTILE}={threshold:.6f}, max={np.max(errors):.6f}")

    model.save(MODEL_PATH)
    with open(THRESHOLD_PATH, "w") as f:
        json.dump({"threshold": threshold, "percentile": THRESHOLD_PERCENTILE}, f)

    print(f"Saved autoencoder to {MODEL_PATH}")
    print(f"Saved threshold to {THRESHOLD_PATH}")


if __name__ == "__main__":
    main()
