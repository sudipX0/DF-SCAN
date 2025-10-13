import os
from PIL import Image
from tqdm import tqdm
from multiprocessing import Pool, cpu_count

def detect_and_crop_face(frame_path, faces_root, margin=20, image_size=224):
    """
    Detect faces in a frame and save cropped face(s).
    """
    try:
        from facenet_pytorch import MTCNN
        mtcnn = MTCNN(keep_all=True)

        img = Image.open(frame_path).convert("RGB")
        boxes, _ = mtcnn.detect(img)

        if boxes is None:
            return 0 # CONDITION WHERE NO FACE IS DETECTED

        # DETERMINE LABEL (FAKE OR REAL) FROM PATH
        label = "fake" if "fake" in frame_path.lower() else "real"
        video_name = os.path.basename(os.path.dirname(frame_path))
        output_dir = os.path.join(faces_root, label, video_name)
        os.makedirs(output_dir, exist_ok=True)

        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = [int(b) for b in box]
            x1 = max(0, x1 - margin)
            y1 = max(0, y1 - margin)
            x2 = min(img.width, x2 + margin)
            y2 = min(img.height, y2 + margin)

            face_crop = img.crop((x1, y1, x2, y2)).resize((image_size, image_size))
            base_name = os.path.splitext(os.path.basename(frame_path))[0]
            face_crop.save(os.path.join(output_dir, f"{base_name}_face_{i}.jpg"))

        return len(boxes)

    except Exception as e:
        print(f"ERROR PROCESSING {frame_path}: {e}")
        return 0

def process_frame(args):
    frame_path, faces_root = args
    return detect_and_crop_face(frame_path, faces_root)

def detect_faces_from_frames(frames_root="data/intermediate/frames",
                             faces_root="data/intermediate/faces",
                             num_workers=None):
    frame_paths = []
    for root, _, files in os.walk(frames_root):
        for file in files:
            if file.lower().endswith(".jpg"):
                frame_paths.append(os.path.join(root, file))

    print(f"FOUND {len(frame_paths)} FRAMES FOR FACE DETECTION.")
    os.makedirs(faces_root, exist_ok=True)

    num_workers = num_workers or max(1, cpu_count() - 2)
    print(f"USING {num_workers} CPU CORES FOR FACE DETECTION.\n")

    # MULTIPROCESSING POOL
    with Pool(num_workers) as pool:
        list(
            tqdm(
                pool.imap_unordered(
                    process_frame,
                    [(fp, faces_root) for fp in frame_paths]
                ),
                total=len(frame_paths),
                desc="DETECTING FACES"
            )
        )

    print("\nFACE DETECTION & CROPPING COMPLETED.")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Detect and crop faces from frames")
    parser.add_argument("--frames_root", type=str, default="data/intermediate/frames",
                        help="Folder with extracted frames")
    parser.add_argument("--faces_root", type=str, default="data/intermediate/faces",
                        help="Where to save cropped faces")
    parser.add_argument("--workers", type=int, default=None,
                        help="Number of CPU cores for multiprocessing")
    args = parser.parse_args()

    detect_faces_from_frames(args.frames_root, args.faces_root, args.workers)
