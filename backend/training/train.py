"""
Trains the apple/banana CNN classifier described in the project's technical
approach: convolution + pooling blocks -> fully connected layers -> softmax
output over {apple, banana}.

Usage:
    python backend/training/train.py
"""
import json
from pathlib import Path

import tensorflow as tf
from tensorflow.keras import layers, models

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data" / "raw"
MODEL_DIR = REPO_ROOT / "backend" / "models"
MODEL_PATH = MODEL_DIR / "fruit_classifier.keras"
LABELS_PATH = MODEL_DIR / "labels.json"

IMAGE_SIZE = (128, 128)
BATCH_SIZE = 32
SEED = 42
EPOCHS = 20


def build_datasets():
    train_ds = tf.keras.utils.image_dataset_from_directory(
        DATA_DIR,
        validation_split=0.2,
        subset="training",
        seed=SEED,
        image_size=IMAGE_SIZE,
        batch_size=BATCH_SIZE,
        label_mode="categorical",
    )
    val_ds = tf.keras.utils.image_dataset_from_directory(
        DATA_DIR,
        validation_split=0.2,
        subset="validation",
        seed=SEED,
        image_size=IMAGE_SIZE,
        batch_size=BATCH_SIZE,
        label_mode="categorical",
    )
    class_names = train_ds.class_names

    # Split the validation set in half -> validation (for training) + held-out test set
    val_batches = tf.data.experimental.cardinality(val_ds)
    test_ds = val_ds.take(val_batches // 2)
    val_ds = val_ds.skip(val_batches // 2)

    autotune = tf.data.AUTOTUNE
    train_ds = train_ds.prefetch(autotune)
    val_ds = val_ds.prefetch(autotune)
    test_ds = test_ds.prefetch(autotune)
    return train_ds, val_ds, test_ds, class_names


def build_model(num_classes: int) -> tf.keras.Model:
    data_augmentation = models.Sequential([
        layers.RandomFlip("horizontal"),
        layers.RandomRotation(0.06),
        layers.RandomZoom(0.06),
    ], name="augmentation")

    model = models.Sequential([
        layers.Input(shape=(*IMAGE_SIZE, 3)),
        layers.Rescaling(1.0 / 255),
        data_augmentation,

        layers.Conv2D(16, 3, padding="same", activation="relu"),
        layers.MaxPooling2D(),

        layers.Conv2D(32, 3, padding="same", activation="relu"),
        layers.MaxPooling2D(),

        layers.Conv2D(64, 3, padding="same", activation="relu"),
        layers.MaxPooling2D(),

        layers.Flatten(),
        layers.Dense(64, activation="relu"),
        layers.Dropout(0.3),
        layers.Dense(num_classes, activation="softmax"),
    ], name="fruit_classifier")

    model.compile(
        optimizer="adam",
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    train_ds, val_ds, test_ds, class_names = build_datasets()
    print("Classes:", class_names)

    model = build_model(num_classes=len(class_names))
    model.summary()

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_accuracy", patience=6, restore_best_weights=True
        ),
    ]

    model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS,
        callbacks=callbacks,
    )

    test_loss, test_acc = model.evaluate(test_ds)
    print(f"Held-out test accuracy: {test_acc:.4f} (loss: {test_loss:.4f})")

    model.save(MODEL_PATH)
    with open(LABELS_PATH, "w") as f:
        json.dump(class_names, f)

    print(f"Saved model to {MODEL_PATH}")
    print(f"Saved labels to {LABELS_PATH}")


if __name__ == "__main__":
    main()
