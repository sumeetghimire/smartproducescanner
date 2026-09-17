"""Quick sanity check: runs a handful of held-out images through the trained
model + ripeness heuristic directly (no server needed) to confirm the
pipeline works end-to-end before testing via the browser.
"""
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from backend.app.inference import classify, decode_image  # noqa: E402
from backend.app.ripeness import estimate_ripeness  # noqa: E402

DATA_DIR = REPO_ROOT / "data" / "raw"


def main():
    random.seed(0)
    for label_dir in sorted(DATA_DIR.iterdir()):
        if not label_dir.is_dir():
            continue
        images = list(label_dir.glob("*.jpg"))
        sample = random.sample(images, min(3, len(images)))
        for img_path in sample:
            raw = img_path.read_bytes()
            image_bgr = decode_image(raw)
            pred_label, confidence = classify(image_bgr)
            ripeness = estimate_ripeness(image_bgr, pred_label)
            correct = "OK " if pred_label == label_dir.name else "MISS"
            print(
                f"[{correct}] true={label_dir.name:8s} pred={pred_label:8s} "
                f"conf={confidence:.3f} ripeness={ripeness['stage']:8s} "
                f"file={img_path.name}"
            )


if __name__ == "__main__":
    main()
