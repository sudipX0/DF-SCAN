import os
import cv2
import face_recognition


def detect_and_crop_faces(frames_dir, vis_dir, crop_dir, max_preview=8):
  """
  Detect faces on frames and crop them.
  Yields three things per frame:
    - vis_path: frame image with bounding boxes
    - cropped_faces: list of saved crop image paths
    - boxes: list of (top, right, bottom, left) for each face
  """
  os.makedirs(vis_dir, exist_ok=True)
  os.makedirs(crop_dir, exist_ok=True)

  frame_files = sorted([f for f in os.listdir(frames_dir) if f.endswith(".jpg")])

  for f in frame_files:
    frame_path = os.path.join(frames_dir, f)
    img = cv2.imread(frame_path)
    if img is None:
      continue
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    boxes = face_recognition.face_locations(rgb, model="hog")

    vis_img = img.copy()
    cropped_faces = []

    for i, (top, right, bottom, left) in enumerate(boxes):
      cv2.rectangle(vis_img, (left, top), (right, bottom), (0, 255, 0), 2)
      face_crop = img[top:bottom, left:right]
      crop_path = os.path.join(crop_dir, f"{os.path.splitext(f)[0]}_face_{i}.jpg")
      cv2.imwrite(crop_path, face_crop)
      cropped_faces.append(crop_path)

    vis_path = os.path.join(vis_dir, f)
    cv2.imwrite(vis_path, vis_img)

    # Return also bounding boxes for this frame for potential overlay with scores
    yield vis_path, cropped_faces, boxes
