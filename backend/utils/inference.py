import os
import torch
from torchvision import transforms
from PIL import Image

val_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225])
])

def predict_from_faces(model, faces_dir, device):
    faces = [os.path.join(faces_dir,f) for f in os.listdir(faces_dir) if f.endswith(".jpg")]
    if not faces:
        return {"prediction": "REAL", "confidence": 0.0}

    model.eval()
    inputs = []
    for fpath in faces:
        img = Image.open(fpath).convert("RGB")
        inputs.append(val_transform(img))
    inputs = torch.stack(inputs).to(device)
    with torch.no_grad():
        outputs = model(inputs.unsqueeze(0))  # batch_size=1
        probs = torch.softmax(outputs, dim=1)
        conf, pred = torch.max(probs, dim=1)
    label = "FAKE" if pred.item()==1 else "REAL"
    return {"prediction": label, "confidence": float(conf.item())}
