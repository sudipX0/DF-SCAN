import os
import random
import shutil
from tqdm import tqdm

def create_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def split_dataset(faces_root, output_root, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15, seed=42):
    random.seed(seed)
    
    classes = ["real", "fake"]
    splits = ["train", "val", "test"]
    for split in splits:
        for cls in classes:
            create_dir(os.path.join(output_root, split, cls))
    
    for cls in classes:
        class_dir = os.path.join(faces_root, cls)
        all_images = []

        # COLLECTING ALL FACE IMAGES
        for root, _, files in os.walk(class_dir):
            for file in files:
                if file.lower().endswith((".jpg", ".png")):
                    all_images.append(os.path.join(root, file))
        
        print(f"\nFOUND {len(all_images)} {cls} FACE IMAGES.")
        random.shuffle(all_images)

        train_end = int(train_ratio * len(all_images))
        val_end = int((train_ratio + val_ratio) * len(all_images))

        train_files = all_images[:train_end]
        val_files = all_images[train_end:val_end]
        test_files = all_images[val_end:]

        for split, file_list in zip(splits, [train_files, val_files, test_files]):
            for src_path in tqdm(file_list, desc=f"COPYING {cls} → {split}", leave=False):
                filename = os.path.basename(src_path)
                dst_path = os.path.join(output_root, split, cls, filename)
                shutil.copy2(src_path, dst_path)

    print("\nDATASET ORGANIZED SUCCESSFULLY.")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ORGANIZE DATASET INTO TRAIN/VAL/TEST SPLITS")
    parser.add_argument("--faces_root", type=str, default="data/intermediate/faces", help="FOLDER WITH CROPPED FACES")
    parser.add_argument("--output_root", type=str, default="data/processed", help="WHERE TO STORE ORGANIZED DATASETS")
    parser.add_argument("--train_ratio", type=float, default=0.7)
    parser.add_argument("--val_ratio", type=float, default=0.15)
    parser.add_argument("--test_ratio", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    split_dataset(args.faces_root, args.output_root, args.train_ratio, args.val_ratio, args.test_ratio, args.seed)
