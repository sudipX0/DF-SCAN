import os, cv2, base64, json, numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from pathlib import Path
from PIL import Image
import torch
from torchvision import transforms, models
from facenet_pytorch import MTCNN
from io import BytesIO

app = FastAPI()

UPLOAD_DIR = "uploaded_videos"
PROCESSED_DIR = "processed_videos"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

# ----------------------------
# Load Model
# ----------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = models.efficientnet_b0(pretrained=False)
num_features = model.classifier[1].in_features
model.classifier[1] = torch.nn.Linear(num_features, 2)
model.load_state_dict(torch.load("/home/sudeep/DF-SCAN/models/baseline_model.pth", map_location=device))
model = model.to(device)
model.eval()
class_names = ["real", "fake"]

# Face detector
mtcnn = MTCNN(keep_all=True, device=device)
val_transforms = transforms.Compose([
    transforms.Resize((224,224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])
])

# ----------------------------
# Utility: Convert frame to base64
# ----------------------------
def frame_to_base64(frame):
    _, buffer = cv2.imencode('.jpg', frame)
    b64_str = base64.b64encode(buffer).decode('utf-8')
    return b64_str

# ----------------------------
# WebSocket for live processing
# ----------------------------
@app.websocket("/ws/process_video")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_text()
        data = json.loads(data)
        file_name = data["file_name"]
        file_bytes = bytes(data["file_bytes"], encoding='latin1')  # convert string to bytes
        video_path = os.path.join(UPLOAD_DIR, file_name)
        with open(video_path, "wb") as f:
            f.write(file_bytes)

        output_dir = os.path.join(PROCESSED_DIR, Path(file_name).stem)
        os.makedirs(output_dir, exist_ok=True)

        cap = cv2.VideoCapture(video_path)
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        predicted_frames = []
        all_probs = []

        for i in range(frame_count):
            ret, frame = cap.read()
            if not ret: break

            # Step 1: Send raw frame
            await websocket.send_json({
                "step":"extract_frame",
                "frame_index": i+1,
                "total_frames": frame_count,
                "frame_b64": frame_to_base64(frame)
            })

            # Step 2: Detect faces
            pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            boxes, _ = mtcnn.detect(pil_img)

            if boxes is not None:
                for box in boxes:
                    x1,y1,x2,y2 = [int(b) for b in box]
                    face_crop = pil_img.crop((x1,y1,x2,y2))
                    tensor = val_transforms(face_crop).unsqueeze(0).to(device)
                    with torch.no_grad():
                        output = model(tensor)
                        probs = torch.softmax(output, dim=1).cpu().numpy()[0]
                        pred_class = int(np.argmax(probs))
                        label = class_names[pred_class]
                        conf = float(probs[pred_class])
                    all_probs.append(probs)

                    # Draw bbox + label on frame
                    cv2.rectangle(frame,(x1,y1),(x2,y2),(0,0,255),2)
                    cv2.putText(frame,f"{label}:{conf:.2f}",(x1,y1-10),
                                cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,255,0),2)

            predicted_frames.append(frame)

            # Step 3: Send frame with detection overlay
            await websocket.send_json({
                "step":"face_detected",
                "frame_index": i+1,
                "total_frames": frame_count,
                "frame_b64": frame_to_base64(frame)
            })

        cap.release()

        # Step 4: Save final video
        height, width, _ = predicted_frames[0].shape
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_out_path = os.path.join(output_dir,"predicted_video.mp4")
        out = cv2.VideoWriter(video_out_path, fourcc, fps, (width,height))
        for frame in predicted_frames:
            out.write(frame)
        out.release()

        mean_prob = np.mean(all_probs, axis=0)
        pred_label = class_names[int(np.argmax(mean_prob))]
        confidence = float(mean_prob[int(np.argmax(mean_prob))])

        # Step 5: Send final result
        await websocket.send_json({
            "step":"finished",
            "predicted_video": video_out_path,
            "label": pred_label,
            "confidence": round(confidence,2)
        })

    except WebSocketDisconnect:
        print("Client disconnected")
