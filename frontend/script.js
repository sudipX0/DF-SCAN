const videoInput = document.getElementById("videoInput");
const scanBtn = document.getElementById("scanBtn");
const progressLog = document.getElementById("progressLog");
const framesPreview = document.getElementById("framesPreview");
const facePreview = document.getElementById("facePreview");
const croppedPreview = document.getElementById("croppedPreview");
const finalResult = document.getElementById("finalResult");
const uploadedVideo = document.getElementById("uploadedVideo");

let sessionId = null;

scanBtn.addEventListener("click", async () => {
  const file = videoInput.files[0];
  if (!file) {
    alert("Please select a video!");
    return;
  }

  resetUI();
  logMessage("Uploading video...");

  // Upload video
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch("http://127.0.0.1:8000/upload", {
    method: "POST",
    body: formData,
  });

  const data = await response.json();
  sessionId = data.session_id;
  logMessage("Upload complete. Video ready.");

  // Show uploaded video
  const videoURL = URL.createObjectURL(file);
  uploadedVideo.src = videoURL;
  uploadedVideo.style.display = "block";

  // Start scan
  logMessage("Starting scan...");
  await fetch(`http://127.0.0.1:8000/scan/${sessionId}`, { method: "POST" });

  // Start listening to SSE
  const evtSource = new EventSource(`http://127.0.0.1:8000/stream/${sessionId}`);

  evtSource.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.status) {
      logMessage(data.status);
    }

    // Frames preview
    if (data.frames && data.frames.length > 0) {
      framesPreview.innerHTML = ""; // show latest batch
      data.frames.forEach((b64) => appendImage(framesPreview, b64));
    }

    // Faces preview (bounding boxes)
    if (data.faces && data.faces.length > 0) {
      facePreview.innerHTML = "";
      data.faces.forEach((b64) => appendImage(facePreview, b64));
    }

    // Cropped faces
    if (data.crops && data.crops.length > 0) {
      croppedPreview.innerHTML = "";
      data.crops.forEach((b64) => appendImage(croppedPreview, b64));
    }

    // Final prediction
    if (data.prediction) {
      finalResult.innerHTML = `<strong>${data.prediction.prediction} (Confidence: ${(
        data.prediction.confidence * 100
      ).toFixed(2)}%)</strong>`;
    }

    if (data.done) {
      evtSource.close();
      logMessage("Scan complete ✅");
    }
  };

  evtSource.onerror = () => {
    logMessage("❌ Connection error or stream closed.");
    evtSource.close();
  };
});

function logMessage(message) {
  const entry = document.createElement("div");
  entry.textContent = message;
  progressLog.appendChild(entry);
  progressLog.scrollTop = progressLog.scrollHeight;
}

function appendImage(container, b64) {
  const img = document.createElement("img");
  img.src = `data:image/jpeg;base64,${b64}`;
  container.appendChild(img);
}

function resetUI() {
  progressLog.innerHTML = "";
  framesPreview.innerHTML = "";
  facePreview.innerHTML = "";
  croppedPreview.innerHTML = "";
  finalResult.innerHTML = "";
  uploadedVideo.src = "";
  uploadedVideo.style.display = "none";
}
