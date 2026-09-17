from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = REPO_ROOT / "backend" / "models" / "fruit_classifier.keras"
LABELS_PATH = REPO_ROOT / "backend" / "models" / "labels.json"
FRONTEND_DIR = REPO_ROOT / "frontend"

IMAGE_SIZE = (128, 128)

# Predictions below this softmax probability are rejected as "unrecognised"
# per the scoping document's confidence-threshold requirement (section 4.2).
CONFIDENCE_THRESHOLD = 0.70
