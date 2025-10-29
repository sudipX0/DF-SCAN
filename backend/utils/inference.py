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
    # Temperature scaling and thresholding
    T = 1.58
    FAKE_THRESHOLD = 0.58
    with torch.no_grad():
        outputs = model(inputs.unsqueeze(0))  # batch_size=1, logits
        # apply temperature scaling: divide logits by T before softmax
        logits_scaled = outputs / T
        probs = torch.softmax(logits_scaled, dim=1)
        # compute per-class probabilities
        real_prob = probs[0, 0].item()
        fake_prob = probs[0, 1].item()
        # Use threshold for declaring FAKE, otherwise REAL
        if fake_prob >= FAKE_THRESHOLD:
            label = "FAKE"
            conf = fake_prob
        else:
            label = "REAL"
            conf = real_prob
    return {"prediction": label, "confidence": float(conf)}


def predict_image(model, image_path, device):
    """Predict a single face crop using the video model with sequence length 1."""
    model.eval()
    img = Image.open(image_path).convert("RGB")
    x = val_transform(img).unsqueeze(0).unsqueeze(0).to(device)  # [1,1,3,224,224]
    with torch.no_grad():
        logits = model(x)
        # Temperature scaling and thresholding
        T = 1.58
        FAKE_THRESHOLD = 0.58
        logits_scaled = logits / T
        probs = torch.softmax(logits_scaled, dim=1)
        real_prob = probs[0, 0].item()
        fake_prob = probs[0, 1].item()
        if fake_prob >= FAKE_THRESHOLD:
            label = "FAKE"
            conf = fake_prob
        else:
            label = "REAL"
            conf = real_prob
    return {"prediction": label, "confidence": float(conf)}
