import asyncio
import os
import uuid
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import base64
import torch
from model import VideoResNetLSTM
from utils.frame_utils import extract_frames
from utils.face_utils import detect_and_crop_faces
from utils.inference import predict_from_faces

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

device = "cuda" if torch.cuda.is_available() else "cpu"
model = VideoResNetLSTM(pretrained=False).to(device)
model.load_state_dict(torch.load("models/baseline500_temporal_model.pth", map_location=device))
model.eval()

progress_messages = {}

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    session_id = str(uuid.uuid4())
    session_dir = os.path.join("temp", session_id)
    os.makedirs(session_dir, exist_ok=True)
    video_path = os.path.join(session_dir, file.filename)
    with open(video_path, "wb") as f:
        f.write(await file.read())

    progress_messages[session_id] = {
        "status": "Upload complete",
        "frames": [],
        "faces": [],
        "crops": [],
        "prediction": None,
        "done": False,
        "video_path": video_path,
        "dirs": {
            "frames": os.path.join(session_dir, "frames"),
            "vis": os.path.join(session_dir, "vis"),
            "crops": os.path.join(session_dir, "crops")
        }
    }
    return {"session_id": session_id}

@app.post("/scan/{session_id}")
async def scan_video(session_id: str):
    asyncio.create_task(process_video(session_id))
    return {"message": "Scan started"}

async def process_video(session_id):
    session = progress_messages[session_id]

    # --- Extract frames ---
    session["status"] = "Extracting frames..."
    for frame_path in extract_frames(session["video_path"], session["dirs"]["frames"]):
        if len(session["frames"]) < 8:
            session["frames"].append(frame_path)
        await asyncio.sleep(0.05)

    session["status"] = "Frame extraction completed. Detecting faces..."

    # --- Detect faces ---
    for vis_path, crop_paths in detect_and_crop_faces(session["dirs"]["frames"],
                                                     session["dirs"]["vis"],
                                                     session["dirs"]["crops"]):
        if len(session["faces"]) < 8:
            session["faces"].append(vis_path)
        for cp in crop_paths:
            if len(session["crops"]) < 8:
                session["crops"].append(cp)
        await asyncio.sleep(0.05)

    session["status"] = "Face detection completed. Cropping faces done. Predicting..."

    # --- Prediction ---
    result = predict_from_faces(model, session["dirs"]["crops"], device)
    session["prediction"] = result
    session["status"] = "Prediction completed"
    session["done"] = True

@app.get("/stream/{session_id}")
async def stream(session_id: str):
    async def event_generator():
        last = None
        while True:
            session = progress_messages.get(session_id)
            if not session:
                break

            if session != last:
                last = session.copy()
                yield f"data: {await encode_session(session)}\n\n"

            if session.get("done"):
                break
            await asyncio.sleep(0.2)
    return StreamingResponse(event_generator(), media_type="text/event-stream")

async def encode_session(session):
    def to_b64(path):
        if os.path.exists(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
        return None

    return JSONResponse(content={
        "type": "status",
        "status": session.get("status"),
        "frames": [to_b64(p) for p in session.get("frames", [])],
        "faces": [to_b64(p) for p in session.get("faces", [])],
        "crops": [to_b64(p) for p in session.get("crops", [])],
        "prediction": session.get("prediction"),
        "done": session.get("done")
    }).body.decode()
