"""Novelty ("is this even an apple or banana photo?") detection.

The classifier is a closed-set 2-class softmax over {apple, banana}, so it
always picks one of the two with high confidence -- even for a photo of a
table. Softmax confidence alone cannot tell us the image is unrelated.

This module loads a small autoencoder trained only on the existing
apple/banana photos (see backend/training/train_novelty_detector.py) to
reconstruct them. An apple/banana photo reconstructs with low error; an
unrelated image reconstructs poorly. Images whose reconstruction error
exceeds a threshold (calibrated on held-out apple/banana photos) are
rejected before the classifier runs.
"""
import json
from functools import lru_cache

import cv2
import numpy as np
import tensorflow as tf

from .config import IMAGE_SIZE, NOVELTY_MODEL_PATH, NOVELTY_THRESHOLD_PATH


@lru_cache(maxsize=1)
def get_autoencoder() -> tf.keras.Model:
    return tf.keras.models.load_model(NOVELTY_MODEL_PATH)


@lru_cache(maxsize=1)
def get_threshold() -> float:
    with open(NOVELTY_THRESHOLD_PATH) as f:
        return json.load(f)["threshold"]


def reconstruction_error(image_bgr: np.ndarray) -> float:
    resized = cv2.resize(image_bgr, IMAGE_SIZE, interpolation=cv2.INTER_AREA)
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    batch = np.expand_dims(rgb, axis=0)

    model = get_autoencoder()
    reconstruction = model.predict(batch, verbose=0)[0]
    mse = float(np.mean(np.square(rgb - reconstruction)))
    return mse


def is_recognised(image_bgr: np.ndarray) -> tuple[bool, float]:
    error = reconstruction_error(image_bgr)
    return error <= get_threshold(), error
