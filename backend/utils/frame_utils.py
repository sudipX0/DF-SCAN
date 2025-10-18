import os
import cv2

def extract_frames(video_path, output_dir, step=5, max_preview=8):
    """
    Extract frames from a video at every `step` frames.
    Yields the saved frame path for live preview.
    """
    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    idx = 0
    saved = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if idx % step == 0:
            path = os.path.join(output_dir, f"frame_{saved:05d}.jpg")
            cv2.imwrite(path, frame)
            saved += 1
            yield path  # <-- yield for streaming
        idx += 1

    cap.release()
