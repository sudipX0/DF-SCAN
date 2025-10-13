import os
import subprocess
from multiprocessing import Pool, cpu_count
from tqdm import tqdm


def extract_frames(video_path: str, output_dir: str, fps: int = 5):
    """
    Extract frames from a single video using FFmpeg.
    Saves frames in output_dir/frame_0001.jpg, frame_0002.jpg, ...
    """
    os.makedirs(output_dir, exist_ok=True)

    command = [
        "ffmpeg",
        "-i", video_path,              
        "-qscale:v", "2",              
        "-vf", f"fps={fps}",           
        os.path.join(output_dir, "frame_%04d.jpg"),
        "-hide_banner",
        "-loglevel", "error"           
    ]

    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def detect_label_from_path(video_path: str) -> str:
    """
    Determine whether a video is 'real' or 'fake' based on folder name.
    """
    fake_keywords = [
        "deepfake", "faceswap", "face2face",
        "faceshifter", "neuraltexture", "detection"
    ]
    folder = video_path.lower()
    for keyword in fake_keywords:
        if keyword in folder:
            return "fake"
    return "real"


def process_video(args):
    """Helper function for multiprocessing pool."""
    video_path, frames_root, fps = args
    label = detect_label_from_path(video_path)
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    output_dir = os.path.join(frames_root, label, video_name)
    extract_frames(video_path, output_dir, fps)
    return video_path


def extract_frames_from_videos(input_dir: str, output_dir: str, fps: int = 5, num_workers: int = None):
    """
    Walk through input_dir and extract frames from all videos in parallel.
    """
    video_paths = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith((".mp4", ".avi", ".mov", ".mkv")):
                video_paths.append(os.path.join(root, file))

    print(f"📂 Found {len(video_paths)} videos in {input_dir}")
    os.makedirs(output_dir, exist_ok=True)

    num_workers = num_workers or max(1, cpu_count() - 2)
    print(f"⚙️ Using {num_workers} CPU cores for parallel extraction\n")

    with Pool(num_workers) as pool:
        list(
            tqdm(
                pool.imap_unordered(
                    process_video,
                    [(vp, output_dir, fps) for vp in video_paths]
                ),
                total=len(video_paths),
                desc="🎞️ Extracting frames"
            )
        )

    print("\n✅ Frame extraction completed!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract frames from FaceForensics++ videos")
    parser.add_argument(
        "--input_dir",
        type=str,
        default="data/raw/ff-c23/FaceForensics++_C23",
        help="Path to FaceForensics++ dataset root"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="data/intermediate/frames",
        help="Where to store extracted frames"
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=5,
        help="Frames per second to extract from each video"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of CPU cores to use (default: all but 2)"
    )

    args = parser.parse_args()

    args.input_dir = os.path.expanduser(args.input_dir)
    args.output_dir = os.path.expanduser(args.output_dir)

    extract_frames_from_videos(args.input_dir, args.output_dir, args.fps, args.workers)
