import os
import subprocess
from multiprocessing import Pool, cpu_count
from tqdm import tqdm


def extract_frames(video_path: str, output_dir: str, num_frames: int = 10):
    """
    Extract `num_frames` evenly spaced frames from a video using FFmpeg.
    Each frame is saved as frame_0001.jpg, frame_0002.jpg, ...
    """
    os.makedirs(output_dir, exist_ok=True)

    # Get video duration
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "format=duration", "-of",
             "default=noprint_wrappers=1:nokey=1", video_path],
            capture_output=True, text=True, check=True
        )
        duration = float(result.stdout.strip())
    except Exception:
        # fallback if duration cannot be determined
        duration = None

    if duration is None or num_frames <= 0:
        # fallback: extract every frame
        command = [
            "ffmpeg",
            "-i", video_path,
            "-qscale:v", "2",
            os.path.join(output_dir, "frame_%04d.jpg"),
            "-hide_banner",
            "-loglevel", "error"
        ]
        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return

    # Calculate evenly spaced timestamps
    interval = duration / num_frames
    # Create a list of timestamp filters for FFmpeg
    # Example: select='eq(n,0)+eq(n,10)+eq(n,20)...'
    # We'll use the 'select' filter with 'between(t,start,end)'
    select_exprs = [f"between(t,{i*interval},{(i+1)*interval})" for i in range(num_frames)]
    select_filter = "+".join(select_exprs)

    command = [
        "ffmpeg",
        "-i", video_path,
        "-qscale:v", "2",
        "-vf", f"select='{select_filter}',setpts=N/FRAME_RATE/TB",
        os.path.join(output_dir, "frame_%04d.jpg"),
        "-hide_banner",
        "-loglevel", "error"
    ]

    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def detect_label_from_path(video_path: str) -> str:
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
    video_path, frames_root, num_frames = args
    label = detect_label_from_path(video_path)
    method_name = os.path.basename(os.path.dirname(video_path))
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    unique_video_id = f"{method_name}_{video_name}"
    output_dir = os.path.join(frames_root, label, unique_video_id)
    extract_frames(video_path, output_dir, num_frames)
    return video_path


def extract_frames_from_videos(input_dir: str, output_dir: str, num_frames: int = 10, num_workers: int = None):
    video_paths = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith((".mp4", ".avi", ".mov", ".mkv")):
                video_paths.append(os.path.join(root, file))

    print(f"FOUND {len(video_paths)} VIDEOS IN {input_dir}")
    os.makedirs(output_dir, exist_ok=True)

    num_workers = num_workers or max(1, cpu_count() - 2)
    print(f"USING {num_workers} CPU CORES FOR PARALLEL EXTRACTION\n")

    with Pool(num_workers) as pool:
        list(
            tqdm(
                pool.imap_unordered(
                    process_video,
                    [(vp, output_dir, num_frames) for vp in video_paths]
                ),
                total=len(video_paths),
                desc="EXTRACTING FRAMES"
            )
        )

    print("\nFRAME EXTRACTION COMPLETED.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract fixed number of evenly spaced frames from FaceForensics++ videos.")
    parser.add_argument("--input_dir", type=str, default="data/raw/ff-c23/FaceForensics++_C23",
                        help="Path to FaceForensics++ dataset root")
    parser.add_argument("--output_dir", type=str, default="data/intermediate/frames",
                        help="Where to store extracted frames")
    parser.add_argument("--num_frames", type=int, default=10,
                        help="Number of evenly spaced frames to extract per video")
    parser.add_argument("--workers", type=int, default=None,
                        help="Number of CPU cores to use (default: all but 2)")
    args = parser.parse_args()

    args.input_dir = os.path.expanduser(args.input_dir)
    args.output_dir = os.path.expanduser(args.output_dir)

    extract_frames_from_videos(args.input_dir, args.output_dir, args.num_frames, args.workers)


# python scripts/extract_frames_v2.py \
#   --input_dir ~/DF-SCAN/data/experiment_100/ff-c23/FaceForensics++_C23 \
#   --output_dir ~/DF-SCAN/data/intermediate_100/frames \
#   --num_frames 10 \
#   --workers 6
