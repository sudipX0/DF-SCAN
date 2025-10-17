import os
import glob
import torch
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from utils import extract_frames, detect_and_crop_face, process_frame, val_transform
from model import load_model
from PIL import Image
import torchvision.transforms as transforms

# ---------------- FASTAPI APP ----------------
app = FastAPI(title="DF-SCAN")

# ---------------- DEVICE & MODEL ----------------
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL = load_model(model_path="models/baseline_temporal_model.pth", device=DEVICE)

# ---------------- PATHS ----------------
FRAMES_DIR = "tmp/frames"
FACES_DIR = "tmp/faces"

os.makedirs(FRAMES_DIR, exist_ok=True)
os.makedirs(FACES_DIR, exist_ok=True)

# ---------------- PREDICTION HELPER ----------------
def predict_video(video_path: str, frames_per_video: int = 20):
    extract_frames(video_path, FRAMES_DIR, fps=5)

    # Detect & crop faces
    frame_paths = sorted(glob.glob(os.path.join(FRAMES_DIR, "*.jpg")))
    cropped_faces = []
    for frame in frame_paths:
        count = detect_and_crop_face(frame, FACES_DIR)
        if count > 0:
            # Take the first face only for simplicity
            cropped_faces.append(frame)

    if not cropped_faces:
        return {"label": "No face detected", "probability": 0.0}

    # Load frames as tensors
    frames_tensor = []
    for f in cropped_faces[:frames_per_video]:
        img = Image.open(f).convert("RGB")
        img = val_transform(img)
        frames_tensor.append(img)

    frames_tensor = torch.stack(frames_tensor).unsqueeze(0).to(DEVICE)  # shape: 1, T, C, H, W

    with torch.no_grad():
        logits = MODEL(frames_tensor)
        probs = torch.softmax(logits, dim=1)
        pred_class = torch.argmax(probs, dim=1).item()
        prob = probs[0, pred_class].item()
        label = "REAL" if pred_class == 0 else "FAKE"

    return {"label": label, "probability": round(prob, 4)}

# ---------------- API ENDPOINT ----------------
@app.post("/predict/")
async def predict(file: UploadFile = File(...)):
    video_path = os.path.join("tmp", file.filename)
    with open(video_path, "wb") as f:
        f.write(await file.read())

    result = predict_video(video_path)
    os.remove(video_path)
    return JSONResponse(result)
