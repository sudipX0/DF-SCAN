import os
import cv2
from PIL import Image
from tqdm import tqdm
from multiprocessing import Pool, cpu_count
import face_recognition


def detect_and_crop_face(frame_path, faces_root, margin=20, image_size=224):
    """
    Detect faces in a frame using face_recognition and save cropped face(s).
    """
    try:
        img = cv2.imread(frame_path)
        if img is None:
            return 0

        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        boxes = face_recognition.face_locations(rgb_img, model='hog')  # fast on CPU

        if not boxes:
            return 0

        # Determine label (real/fake)
        label = "fake" if "fake" in frame_path.lower() else "real"

        # Include method name to avoid collisions
        method_name = os.path.basename(os.path.dirname(os.path.dirname(frame_path)))
        video_name = os.path.basename(os.path.dirname(frame_path))
        unique_video_id = f"{method_name}_{video_name}"
        output_dir = os.path.join(faces_root, label, unique_video_id)
        os.makedirs(output_dir, exist_ok=True)

        count = 0
        for (top, right, bottom, left) in boxes:
            # Add margin
            top = max(0, top - margin)
            left = max(0, left - margin)
            bottom = min(img.shape[0], bottom + margin)
            right = min(img.shape[1], right + margin)

            face_crop = img[top:bottom, left:right]
            if face_crop.size == 0:
                continue

            face_crop = cv2.resize(face_crop, (image_size, image_size))
            base_name = os.path.splitext(os.path.basename(frame_path))[0]
            cv2.imwrite(os.path.join(output_dir, f"{base_name}_face_{count}.jpg"), face_crop)
            count += 1

        return count

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

    parser = argparse.ArgumentParser(description="Detect and crop faces from frames (face_recognition)")
    parser.add_argument("--frames_root", type=str, default="data/intermediate/frames",
                        help="Folder with extracted frames")
    parser.add_argument("--faces_root", type=str, default="data/intermediate/faces",
                        help="Where to save cropped faces")
    parser.add_argument("--workers", type=int, default=None,
                        help="Number of CPU cores for multiprocessing")
    args = parser.parse_args()

    detect_faces_from_frames(args.frames_root, args.faces_root, args.workers)


# python scripts/detect_faces_v2.py \
#     --frames_root ~/DF-SCAN/data/intermediate_100/frames \
#     --faces_root ~/DF-SCAN/data/intermediate_100/faces \
#     --workers 6
