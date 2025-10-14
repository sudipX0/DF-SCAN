import os
import cv2
import argparse
from tqdm import tqdm

def reconstruct_video_from_frames(frames_dir, output_path, fps=25):
    frame_files = sorted([
        f for f in os.listdir(frames_dir)
        if f.endswith(('.jpg', '.png'))
    ])
    
    if not frame_files:
        print(f"[WARN] No frames found in {frames_dir}, skipping.")
        return

    first_frame_path = os.path.join(frames_dir, frame_files[0])
    frame = cv2.imread(first_frame_path)
    height, width, _ = frame.shape

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    for frame_file in frame_files:
        frame_path = os.path.join(frames_dir, frame_file)
        frame = cv2.imread(frame_path)
        if frame is not None:
            video_writer.write(frame)

    video_writer.release()


def main(faces_root, output_root, fps=25):
    os.makedirs(output_root, exist_ok=True)

    for method in os.listdir(faces_root):
        method_path = os.path.join(faces_root, method)
        if not os.path.isdir(method_path):
            continue

        for video_dir in tqdm(os.listdir(method_path), desc=f"Reconstructing {method}"):
            video_path = os.path.join(method_path, video_dir)
            if not os.path.isdir(video_path):
                continue

            output_subdir = os.path.join(output_root, method)
            os.makedirs(output_subdir, exist_ok=True)
            output_path = os.path.join(output_subdir, f"{video_dir}.mp4")

            reconstruct_video_from_frames(video_path, output_path, fps=fps)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reconstruct videos from face frames")
    parser.add_argument("--faces_root", type=str, required=True, help="Path to cropped face frames directory")
    parser.add_argument("--output_root", type=str, required=True, help="Path to save reconstructed videos")
    parser.add_argument("--fps", type=int, default=25, help="Frame rate for reconstructed video")

    args = parser.parse_args()
    main(args.faces_root, args.output_root, args.fps)
