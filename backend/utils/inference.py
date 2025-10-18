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


def predict_image(model, image_path, device):
    """Predict a single face crop using the video model with sequence length 1."""
    model.eval()
    img = Image.open(image_path).convert("RGB")
    x = val_transform(img).unsqueeze(0).unsqueeze(0).to(device)  # [1,1,3,224,224]
    with torch.no_grad():
        logits = model(x)
        probs = torch.softmax(logits, dim=1)
        conf, pred = torch.max(probs, dim=1)
    label = "FAKE" if pred.item() == 1 else "REAL"
    return {"prediction": label, "confidence": float(conf.item())}
