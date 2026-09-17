"""
Flattens the sourced Fruit-Images-Dataset (Muresan & Oltean, 2018) variety
folders (e.g. "Apple Braeburn", "Banana Lady Finger") into two flat class
folders: data/raw/apple and data/raw/banana. Combines the dataset's own
Training + Test splits since we create our own train/val/test split later.

Source: https://github.com/horea94/Fruit-Images-Dataset
"""
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "data_src" / "Fruit-Images-Dataset"
DEST_ROOT = REPO_ROOT / "data" / "raw"

CLASS_FOLDERS = {
    "apple": [
        "Apple Braeburn",
        "Apple Golden 1",
        "Apple Granny Smith",
        "Apple Red Delicious",
    ],
    "banana": [
        "Banana",
        "Banana Lady Finger",
        "Banana Red",
    ],
}

SPLITS = ["Training", "Test"]


def main() -> None:
    for label, variety_folders in CLASS_FOLDERS.items():
        dest_dir = DEST_ROOT / label
        dest_dir.mkdir(parents=True, exist_ok=True)
        count = 0
        for split in SPLITS:
            for variety in variety_folders:
                src_dir = SRC_ROOT / split / variety
                if not src_dir.is_dir():
                    print(f"WARNING: missing {src_dir}")
                    continue
                for img_path in src_dir.glob("*.jpg"):
                    variety_slug = variety.lower().replace(" ", "_")
                    dest_name = f"{variety_slug}_{split.lower()}_{img_path.name}"
                    shutil.copyfile(img_path, dest_dir / dest_name)
                    count += 1
        print(f"{label}: {count} images -> {dest_dir}")


if __name__ == "__main__":
    main()
