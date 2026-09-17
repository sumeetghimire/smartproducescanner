import json
from functools import lru_cache

import cv2
import numpy as np
import tensorflow as tf

from .config import IMAGE_SIZE, LABELS_PATH, MODEL_PATH


@lru_cache(maxsize=1)
def get_model() -> tf.keras.Model:
    return tf.keras.models.load_model(MODEL_PATH)


@lru_cache(maxsize=1)
def get_labels() -> list[str]:
    with open(LABELS_PATH) as f:
        return json.load(f)


def decode_image(raw_bytes: bytes) -> np.ndarray:
    """Decodes uploaded bytes into a BGR OpenCV image."""
    arr = np.frombuffer(raw_bytes, dtype=np.uint8)
    image_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if image_bgr is None:
        raise ValueError("Could not decode image. Please upload a valid JPG/PNG file.")
    return image_bgr


def classify(image_bgr: np.ndarray) -> tuple[str, float]:
    """Preprocesses the image and returns (predicted_label, confidence)."""
    resized = cv2.resize(image_bgr, IMAGE_SIZE, interpolation=cv2.INTER_AREA)
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    batch = np.expand_dims(rgb.astype(np.float32), axis=0)

    model = get_model()
    labels = get_labels()

    probabilities = model.predict(batch, verbose=0)[0]
    top_idx = int(np.argmax(probabilities))
    return labels[top_idx], float(probabilities[top_idx])
