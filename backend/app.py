import asyncio
import os
import uuid
import time
import json
import traceback
from pathlib import Path
from typing import Any, Dict
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import base64
import cv2
import torch
import shutil
from model import VideoResNetLSTM
from utils.frame_utils import extract_frames
from utils.face_utils import detect_and_crop_faces
from utils.inference import predict_from_faces, predict_image

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

device = "cuda" if torch.cuda.is_available() else "cpu"
model = VideoResNetLSTM(pretrained=False).to(device)
model.load_state_dict(torch.load("models/baseline500_temporal_model.pth", map_location=device))
model.eval()

progress_messages: Dict[str, Dict[str, Any]] = {}
# Serve frontend at /ui
FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/ui", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="ui")

@app.get("/health")
async def health():
    return {"ok": True}

# --- Reliability/UX additions ---
SESSIONS_ROOT = Path(__file__).resolve().parent / "temp"
META_FILENAME = "session.json"
HEARTBEAT_SECONDS = 10

# Basic per-step soft timeouts (seconds)
STEP_TIMEOUTS = {
    "frames": 120,
    "faces": 180,
    "inference": 90,
}

def _session_dir(sid: str) -> Path:
    return SESSIONS_ROOT / sid

def _meta_path(sid: str) -> Path:
    return _session_dir(sid) / META_FILENAME

def _load_meta(sid: str) -> Dict[str, Any]:
    p = _meta_path(sid)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}

def _save_meta(sid: str, data: Dict[str, Any]) -> None:
    d = _session_dir(sid)
    d.mkdir(parents=True, exist_ok=True)
    p = _meta_path(sid)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(p)

def _update_meta(sid: str, **updates) -> Dict[str, Any]:
    m = _load_meta(sid)
    m.update(updates)
    # Always store the session_id field for convenience
    m.setdefault("session_id", sid)
    _save_meta(sid, m)
    return m

def _set_stage(sid: str, stage: str, status: str) -> None:
    now = time.time()
    m = _load_meta(sid)
    stages = m.get("stages", {})
    s = stages.get(stage, {})
    if status == "running":
        s["started_at"] = now
    if status in ("done", "error", "canceled"):
        s["ended_at"] = now
    s["status"] = status
    stages[stage] = s
    m["stages"] = stages
    m["stage"] = stage
    if status in ("error", "canceled"):
        m["status"] = status
        m["ended_at"] = now
    _save_meta(sid, m)

def _ensure_app_state():
    if not hasattr(app.state, "canceled"):
        app.state.canceled = set()
    if not hasattr(app.state, "tasks"):
        app.state.tasks = {}

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
        "stage": "uploaded",
        "frames": [],
        "faces": [],
        "crops": [],
        "frames_count": 0,
        "faces_count": 0,
        "crops_count": 0,
        "prediction": None,
        "done": False,
        "video_path": video_path,
        "dirs": {
            "frames": os.path.join(session_dir, "frames"),
            "vis": os.path.join(session_dir, "vis"),
            "crops": os.path.join(session_dir, "crops")
        }
    }
    # persist minimal metadata
    _update_meta(
        session_id,
        status="uploaded",
        stage="uploaded",
        started_at=time.time(),
        stages={}
    )
    return {"session_id": session_id}

@app.post("/scan/{session_id}")
async def scan_video(session_id: str):
    _ensure_app_state()
    task = asyncio.create_task(process_video(session_id))
    app.state.tasks[session_id] = task
    return {"message": "Scan started"}

async def process_video(session_id):
    """Main orchestration with cooperative cancel checks, soft timeouts, and metadata updates."""
    session = progress_messages.get(session_id)
    if not session:
        return

    try:
        # Stage: frames
        _update_meta(session_id, status="running", stage="frames")
        _set_stage(session_id, "frames", "running")
        session["status"] = "Extracting frames..."
        session["stage"] = "frames"
        start_t = time.time()
        for frame_path in extract_frames(session["video_path"], session["dirs"]["frames"]):
            _ensure_app_state()
            if session_id in app.state.canceled:
                session["status"] = "Canceled"
                _set_stage(session_id, "frames", "canceled")
                _update_meta(session_id, status="canceled", ended_at=time.time())
                session["done"] = True
                return
            session["frames_count"] = session.get("frames_count", 0) + 1
            session.setdefault("frames", []).append(frame_path)
            await asyncio.sleep(0.01)
            if time.time() - start_t > STEP_TIMEOUTS["frames"]:
                raise HTTPException(status_code=504, detail="Frame extraction timeout")

        # Stage: faces
        session["status"] = "Frame extraction completed. Detecting faces..."
        _set_stage(session_id, "frames", "done")
        _set_stage(session_id, "faces", "running")
        _update_meta(session_id, stage="faces")
        session["stage"] = "faces"

        start_t = time.time()
        for vis_path, crop_paths, boxes in detect_and_crop_faces(
            session["dirs"]["frames"], session["dirs"]["vis"], session["dirs"]["crops"]
        ):
            _ensure_app_state()
            if session_id in app.state.canceled:
                session["status"] = "Canceled"
                _set_stage(session_id, "faces", "canceled")
                _update_meta(session_id, status="canceled", ended_at=time.time())
                session["done"] = True
                return
            # Per-face predictions and overlay on vis image
            try:
                preds = []
                for cp in crop_paths:
                    try:
                        preds.append(predict_image(model, cp, device))
                    except Exception:
                        preds.append({"prediction": "REAL", "confidence": 0.0})
                if os.path.exists(vis_path):
                    vis_img = cv2.imread(vis_path)
                    if vis_img is not None:
                        # Persist latest boxes/preds and frame size for UI overlay
                        try:
                            h, w = vis_img.shape[:2]
                            session["frame_size"] = [h, w]
                        except Exception:
                            pass
                        session["last_boxes"] = [(int(t), int(r), int(b), int(l)) for (t, r, b, l) in boxes]
                        session["last_preds"] = [{
                            "label": str(p.get("prediction", "")).upper(),
                            "confidence": float(p.get("confidence", 0.0) or 0.0),
                        } for p in preds]

                        for (top, right, bottom, left), pred in zip(boxes, preds):
                            label = str(pred.get("prediction", "")).upper()
                            conf_val = float(pred.get("confidence", 0.0) or 0.0)
                            conf_pct = int(round(conf_val * 100))
                            color = (0, 0, 255) if label == "FAKE" else (0, 200, 0)
                            # draw box and confidence value only
                            cv2.rectangle(vis_img, (left, top), (right, bottom), color, 2)
                            text = f"Conf {conf_val:.2f}"
                            (tw, th), bl = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                            tx, ty = left, max(0, top - th - 6)
                            cv2.rectangle(vis_img, (tx - 2, ty - th - 4), (tx + tw + 2, ty + 2), color, -1)
                            cv2.putText(vis_img, text, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
                        cv2.imwrite(vis_path, vis_img)
            except Exception:
                pass

            session["faces_count"] = session.get("faces_count", 0) + len(crop_paths)
            session["crops_count"] = session.get("crops_count", 0) + len(crop_paths)
            session.setdefault("faces", []).append(vis_path)
            for cp in crop_paths:
                session.setdefault("crops", []).append(cp)
            await asyncio.sleep(0.01)
            if time.time() - start_t > STEP_TIMEOUTS["faces"]:
                raise HTTPException(status_code=504, detail="Face detection timeout")

        # Stage: inference
        session["status"] = "Face detection completed. Cropping faces done. Predicting..."
        _set_stage(session_id, "faces", "done")
        _set_stage(session_id, "inference", "running")
        _update_meta(session_id, stage="inference")
        session["stage"] = "inference"

        async def _run_inf():
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, lambda: predict_from_faces(model, session["dirs"]["crops"], device))
        try:
            result = await asyncio.wait_for(_run_inf(), timeout=STEP_TIMEOUTS["inference"])
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="Inference timeout")

        # Do not annotate face previews after final result to avoid confusion on last frame

        session["prediction"] = result
        session["status"] = "Prediction completed"
        session["done"] = True
        _set_stage(session_id, "inference", "done")
        _update_meta(session_id, status="done", ended_at=time.time(), result=result)
    except HTTPException as he:
        session["status"] = f"Error: {he.detail}"
        session["done"] = True
        _set_stage(session_id, _load_meta(session_id).get("stage", "unknown"), "error")
        _update_meta(session_id, status="error", error=he.detail, ended_at=time.time())
    except Exception as e:
        session["status"] = "Internal error"
        session["done"] = True
        _set_stage(session_id, _load_meta(session_id).get("stage", "unknown"), "error")
        _update_meta(session_id, status="error", error=str(e), traceback=traceback.format_exc(), ended_at=time.time())

@app.get("/stream/{session_id}")
async def stream(session_id: str, request: Request):
    async def event_generator():
        last_sig = None
        last_heartbeat = 0.0
        loop = asyncio.get_event_loop()
        while True:
            # client disconnect check
            try:
                if await request.is_disconnected():
                    break
            except Exception:
                pass

            session = progress_messages.get(session_id)
            if not session:
                break

            # signature based on a few fields to avoid shallow-copy pitfalls
            sig = (
                session.get("status"),
                len(session.get("frames", [])),
                len(session.get("faces", [])),
                len(session.get("crops", [])),
                bool(session.get("prediction")),
                bool(session.get("done")),
            )
            if sig != last_sig:
                last_sig = sig
                payload = await encode_session(session)
                yield f"data: {payload}\n\n"

            # Heartbeat keep-alive
            now = loop.time()
            if now - last_heartbeat > HEARTBEAT_SECONDS:
                last_heartbeat = now
                yield "event: keep-alive\n\n"

            if session.get("done"):
                break
            await asyncio.sleep(0.25)
    return StreamingResponse(event_generator(), media_type="text/event-stream")

async def encode_session(session):
    def to_b64(path):
        if os.path.exists(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
        return None

    # Limit to last N media items to control payload size
    max_items = 8
    return JSONResponse(content={
        "type": "status",
        "status": session.get("status"),
        "stage": session.get("stage"),
        "frames": [to_b64(p) for p in session.get("frames", [])][-max_items:],
        "faces": [to_b64(p) for p in session.get("faces", [])][-max_items:],
        "crops": [to_b64(p) for p in session.get("crops", [])][-max_items:],
        "frames_count": session.get("frames_count", 0),
        "faces_count": session.get("faces_count", 0),
        "crops_count": session.get("crops_count", 0),
        "boxes": session.get("last_boxes"),
        "box_preds": session.get("last_preds"),
        "frame_size": session.get("frame_size"),
        "prediction": session.get("prediction"),
        "done": session.get("done")
    }).body.decode()


@app.get("/status/{session_id}")
async def get_status(session_id: str):
    m = _load_meta(session_id)
    if not m:
        session = progress_messages.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        # derive a minimal status
        m = {
            "session_id": session_id,
            "status": "done" if session.get("done") else "running",
            "stage": _load_meta(session_id).get("stage", "unknown"),
            "stages": _load_meta(session_id).get("stages", {}),
        }
    return JSONResponse(m)


@app.post("/cancel/{session_id}")
async def cancel_scan(session_id: str):
    _ensure_app_state()
    app.state.canceled.add(session_id)
    t = getattr(app.state, "tasks", {}).get(session_id)
    if t and not t.done():
        t.cancel()
    # update in-memory session if exists
    s = progress_messages.get(session_id)
    if s:
        s["status"] = "Canceled"
        s["done"] = True
    _set_stage(session_id, _load_meta(session_id).get("stage", "unknown"), "canceled")
    _update_meta(session_id, status="canceled", ended_at=time.time())
    return {"ok": True, "session_id": session_id}


@app.post("/clear/{session_id}")
async def clear_session(session_id: str):
    """Delete temp files, metadata, and in-memory state for a session."""
    _ensure_app_state()
    # Cancel any running task
    t = getattr(app.state, "tasks", {}).get(session_id)
    if t and not t.done():
        try:
            t.cancel()
        except Exception:
            pass
        try:
            await asyncio.sleep(0)
        except Exception:
            pass
    try:
        # Remove temp directory and meta
        d = _session_dir(session_id)
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)
    except Exception:
        pass
    # Cleanup memory state
    try:
        progress_messages.pop(session_id, None)
    except Exception:
        pass
    try:
        app.state.tasks.pop(session_id, None)
    except Exception:
        pass
    try:
        app.state.canceled.discard(session_id)
    except Exception:
        pass
    return {"ok": True, "session_id": session_id}
