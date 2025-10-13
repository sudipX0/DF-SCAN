"""
preprocessing.py — Orchestrates the full preprocessing pipeline
Steps:
1. Extract frames from videos
2. Detect and crop faces
3. Organize dataset into train/val/test splits
"""

import os
import subprocess
import argparse

def run_script(script_path, args_dict):
    """Run a Python script with arguments."""
    cmd = ["python", script_path]
    for k, v in args_dict.items():
        cmd.append(f"--{k}")
        if v is not None:
            cmd.append(str(v))
    print("\nRUNNING:", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print(f"COMPLETED {os.path.basename(script_path)}\n")


def main():
    parser = argparse.ArgumentParser(description="DF-SCAN PREPROCESSING PIPELINE")
    
    parser.add_argument("--raw_root", type=str, default="data/raw/ff-c23/FaceForensics++_C23", help="RAW DATA ROOT DIRECTORY")
    parser.add_argument("--frames_root", type=str, default="data/intermediate/frames", help="WHERE TO SAVE EXTRACTED FRAMES")
    parser.add_argument("--faces_root", type=str, default="data/intermediate/faces", help="WHERE TO SAVE CROPPED FACES")
    parser.add_argument("--output_root", type=str, default="data/processed", help="WHERE TO SAVE ORGANIZED DATASET")
    parser.add_argument("--workers", type=int, default=6, help="NUMBER OF CPU CORES FOR MULTIPROCESSING")
    parser.add_argument("--skip_frames", action="store_true", help="SKIP FRAME EXTRACTION")
    parser.add_argument("--skip_faces", action="store_true", help="SKIP FACE DETECTION")
    parser.add_argument("--skip_split", action="store_true", help="SKIP DATASET ORGANIZATION")

    args = parser.parse_args()

    # PIPELINE 1: FRAME EXTRACTION
    if not args.skip_frames:
        run_script("scripts/extract_frames.py", {
            "input_root": args.raw_root,
            "output_root": args.frames_root
        })
    else:
        print("SKIPPING FRAME EXTRACTION.")

    # PIPELINE 2: FACE DETECTION
    if not args.skip_faces:
        run_script("scripts/detect_faces.py", {
            "frames_root": args.frames_root,
            "faces_root": args.faces_root,
            "workers": args.workers
        })
    else:
        print("SKIPPING FACE DETECTION.")

    # PIPELINE 3: DATASET ORGANIZATION
    if not args.skip_split:
        run_script("scripts/organize_dataset.py", {
            "faces_root": args.faces_root,
            "output_root": args.output_root
        })
    else:
        print("SKIPPING DATASET ORGANIZATION.")

    print("\nPREPROCESSING PIPELINE COMPLETED SUCCESSFULLY.")


if __name__ == "__main__":
    main()

# python scripts/preprocessing.py \
#   --raw_root ~/DF-SCAN/data/raw/ff-c23/FaceForensics++_C23 \
#   --frames_root ~/DF-SCAN/data/intermediate/frames \
#   --faces_root ~/DF-SCAN/data/intermediate/faces \
#   --output_root ~/DF-SCAN/data/processed \
#   --workers 6
