import os
import random
import shutil
from tqdm import tqdm

def create_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def split_dataset_by_video(faces_root, output_root,
                           train_ratio=0.7, val_ratio=0.15, test_ratio=0.15, seed=42):
    random.seed(seed)
    
    classes = ["real", "fake"]
    splits = ["train", "val", "test"]
    
    # CREATE SPLIT DIRECTORIES
    for split in splits:
        for cls in classes:
            create_dir(os.path.join(output_root, split, cls))
    
    for cls in classes:
        class_dir = os.path.join(faces_root, cls)
        videos = [d for d in os.listdir(class_dir)
                  if os.path.isdir(os.path.join(class_dir, d))]
        
        print(f"\nFOUND {len(videos)} {cls.upper()} VIDEOS.")
        random.shuffle(videos)

        train_end = int(train_ratio * len(videos))
        val_end = int((train_ratio + val_ratio) * len(videos))
        
        split_videos = {
            "train": videos[:train_end],
            "val": videos[train_end:val_end],
            "test": videos[val_end:]
        }
        
        for split, vid_list in split_videos.items():
            for vid in tqdm(vid_list, desc=f"COPYING {cls} → {split}", leave=False):
                src_dir = os.path.join(class_dir, vid)
                dst_dir = os.path.join(output_root, split, cls, vid)
                shutil.copytree(src_dir, dst_dir)
    
    print("\nDATASET ORGANIZED SUCCESSFULLY.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Organize dataset by video folders (train/val/test)")
    parser.add_argument("--faces_root", type=str, default="data/intermediate_100/faces",
                        help="Folder with cropped faces grouped by video")
    parser.add_argument("--output_root", type=str, default="data/processed_100",
                        help="Where to store organized datasets")
    parser.add_argument("--train_ratio", type=float, default=0.7)
    parser.add_argument("--val_ratio", type=float, default=0.15)
    parser.add_argument("--test_ratio", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    
    split_dataset_by_video(args.faces_root, args.output_root,
                           args.train_ratio, args.val_ratio, args.test_ratio, args.seed)
