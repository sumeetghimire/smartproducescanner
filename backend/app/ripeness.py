"""Heuristic ripeness estimation via HSV colour analysis.

IMPORTANT LIMITATION: no labelled ripeness dataset (unripe/ripe/overripe)
was available to train a CNN for this sub-task (it would require a
separate dataset with ripeness ground truth, which was not obtainable
without Kaggle credentials during scoping). Instead this module uses a
simple, documented colour heuristic:

  - a "background" mask removes near-white/plain background pixels
    (the source dataset images are studio photos on white backgrounds)
  - the remaining foreground pixels are checked for:
      * dark_ratio  -> proportion of very low-brightness pixels
                       (bruising / brown spotting) -> overripe signal
      * green_ratio -> proportion of green-hued pixels -> unripe signal
      * yellow_ratio -> proportion of yellow-hued pixels -> ripe signal

This is intentionally simple and should be presented as a prototype
heuristic, not a validated ripeness classifier. See project extensions
in the scoping document for training a dedicated ripeness model.
"""
import cv2
import numpy as np

RIPENESS_STAGES = ("unripe", "ripe", "overripe")


def _foreground_ratios(image_bgr: np.ndarray) -> dict:
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]

    background_mask = (s < 30) & (v > 200)
    foreground_mask = ~background_mask
    total_fg = int(foreground_mask.sum())

    if total_fg < 50:  # essentially no fruit detected against background
        return {"total_fg": 0, "dark_ratio": 0.0, "green_ratio": 0.0, "yellow_ratio": 0.0}

    dark_mask = foreground_mask & (v < 70)
    green_mask = foreground_mask & (h >= 35) & (h <= 85) & (s > 40)
    yellow_mask = foreground_mask & (h >= 20) & (h < 35) & (s > 40)

    return {
        "total_fg": total_fg,
        "dark_ratio": float(dark_mask.sum()) / total_fg,
        "green_ratio": float(green_mask.sum()) / total_fg,
        "yellow_ratio": float(yellow_mask.sum()) / total_fg,
    }


def estimate_ripeness(image_bgr: np.ndarray, label: str) -> dict:
    ratios = _foreground_ratios(image_bgr)

    if ratios["total_fg"] == 0:
        return {"stage": "unknown", "method": "heuristic-colour-analysis", "ratios": ratios}

    dark_ratio = ratios["dark_ratio"]
    green_ratio = ratios["green_ratio"]
    yellow_ratio = ratios["yellow_ratio"]

    if label == "banana":
        if dark_ratio > 0.15:
            stage = "overripe"
        elif green_ratio > 0.25 and green_ratio > yellow_ratio:
            stage = "unripe"
        else:
            stage = "ripe"
    elif label == "apple":
        if dark_ratio > 0.12:
            stage = "overripe"
        elif green_ratio > 0.55:
            stage = "unripe"
        else:
            stage = "ripe"
    else:
        stage = "unknown"

    return {"stage": stage, "method": "heuristic-colour-analysis", "ratios": ratios}
