import os
import cv2
import torch
import torchvision.transforms as transforms
from PIL import Image
from tqdm import tqdm
import subprocess
from multiprocessing import Pool, cpu_count
import face_recognition

# ---------------- TRANSFORMS ----------------
train_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(),
    transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

val_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])


# ---------------- FRAME EXTRACTION ----------------
def extract_frames(video_path: str, output_dir: str, fps: int = 5):
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


# ---------------- FACE DETECTION ----------------
def detect_and_crop_face(frame_path, faces_root, margin=20, image_size=224):
    try:
        img = cv2.imread(frame_path)
        if img is None:
            return 0

        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        boxes = face_recognition.face_locations(rgb_img, model='hog')

        if not boxes:
            return 0

        label = "fake" if "fake" in frame_path.lower() else "real"
        method_name = os.path.basename(os.path.dirname(os.path.dirname(frame_path)))
        video_name = os.path.basename(os.path.dirname(frame_path))
        unique_video_id = f"{method_name}_{video_name}"
        output_dir = os.path.join(faces_root, label, unique_video_id)
        os.makedirs(output_dir, exist_ok=True)

        count = 0
        for (top, right, bottom, left) in boxes:
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
