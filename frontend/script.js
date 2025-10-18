// New improved frontend with drag-and-drop, stages, progress, cancel/retry
function detectApiBase() {
  try {
    if (window.location && /^https?:\/\//.test(window.location.origin)) {
      return window.location.origin; // If served via http(s), prefer same-origin
    }
  } catch {}
  return "http://127.0.0.1:8000"; // Fallback when opening index.html via file://
}

const API = {
  base: detectApiBase(),
  upload: "/upload",
  scan: (id) => `/scan/${id}`,
  stream: (id) => `/stream/${id}`,
  status: (id) => `/status/${id}`,
  cancel: (id) => `/cancel/${id}`,
  clear: (id) => `/clear/${id}`,
};

const els = {
  dropzone: document.getElementById("dropzone"),
  fileInput: document.getElementById("fileInput"),
  browseBtn: document.getElementById("browseBtn"),
  fileInfo: document.getElementById("fileInfo"),
  startBtn: document.getElementById("startBtn"),
  cancelBtn: document.getElementById("cancelBtn"),
  clearBtn: document.getElementById("clearBtn"),
  retryBtn: document.getElementById("retryBtn"),
  errorBanner: document.getElementById("errorBanner"),
  progressFill: document.getElementById("progressFill"),
  progressText: document.getElementById("progressText"),
  stageBadges: {
    frames: document.getElementById("stage-frames"),
    faces: document.getElementById("stage-faces"),
    inference: document.getElementById("stage-inference"),
  },
  // Optional grids (may not exist in current layout)
  framesGrid: document.getElementById("framesGrid"),
  cropsGrid: document.getElementById("cropsGrid"),
  resultSection: document.getElementById("resultSection"),
  resultText: document.getElementById("resultText"),
  liveFrame: document.getElementById("liveFrame"),
  liveStatus: document.getElementById("liveStatus"),
  liveCurrentCrop: document.getElementById("liveCurrentCrop"),
  // legacy
  legacy: {
    progressLog: document.getElementById("progressLog"),
    framesPreview: document.getElementById("framesPreview"),
    facePreview: document.getElementById("facePreview"),
    croppedPreview: document.getElementById("croppedPreview"),
    finalResult: document.getElementById("finalResult"),
    uploadedVideo: document.getElementById("uploadedVideo"),
  },
  uploadedVideoMain: document.getElementById("uploadedVideoMain"),
};

let state = {
  file: null,
  sessionId: null,
  sse: null,
  done: false,
  canceled: false,
};

function resetUI() {
  els.errorBanner.hidden = true;
  els.errorBanner.textContent = "";
  els.resultSection.hidden = true;
  els.resultText.textContent = "";
  if (els.framesGrid) els.framesGrid.innerHTML = "";
  if (els.cropsGrid) els.cropsGrid.innerHTML = "";
  if (els.liveFrame) els.liveFrame.removeAttribute("src");
  if (els.liveStatus) els.liveStatus.textContent = "Idle";
  if (els.liveCurrentCrop) els.liveCurrentCrop.innerHTML = "";
  setProgress(0, "Idle");
  setStage("frames", "pending");
  setStage("faces", "pending");
  setStage("inference", "pending");
  els.cancelBtn.disabled = true;
  if (els.clearBtn) els.clearBtn.disabled = true;
  els.retryBtn.hidden = true;
  // Clear outcome background tint when resetting
  try { document.body.classList.remove("outcome-real", "outcome-fake"); } catch {}
}

function setStage(stage, status) {
  const badge = els.stageBadges[stage];
  if (!badge) return;
  badge.classList.remove("pending", "active", "done", "error");
  badge.classList.add(status);
  // Update live status label to emphasize real-time feel
  const labelMap = { frames: "Extracting frames", faces: "Detecting faces", inference: "Predicting" };
  if (status === "active" && els.liveStatus) {
    els.liveStatus.textContent = labelMap[stage] || "Processing";
  }
}

function setProgress(pct, text) {
  els.progressFill.style.width = `${Math.max(0, Math.min(100, pct))}%`;
  els.progressText.textContent = text;
}

function showError(msg) {
  els.errorBanner.hidden = false;
  els.errorBanner.textContent = msg;
}

function humanResult(labelText, confidence) {
  const confPct = Math.round(confidence * 100);
  if (confidence >= 0.7) {
    return `${labelText} (${confPct}%)`;
  } else if (confidence >= 0.5) {
    return `Uncertain: leans ${labelText} (${confPct}%)`;
  } else {
    return `Uncertain (${confPct}%)`;
  }
}

async function apiFetch(url, opts = {}, timeoutMs = 300000) {
  const controller = new AbortController();
  const to = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, { ...opts, signal: controller.signal });
    return res;
  } finally {
    clearTimeout(to);
  }
}

// Drag & drop and browse
els.browseBtn?.addEventListener("click", () => els.fileInput.click());
els.dropzone?.addEventListener("click", () => els.fileInput.click());
els.fileInput?.addEventListener("change", (e) => {
  const file = e.target.files?.[0];
  if (file) onFileSelected(file);
});

["dragenter", "dragover"].forEach((ev) =>
  els.dropzone?.addEventListener(ev, (e) => {
    e.preventDefault();
    els.dropzone.classList.add("dragover");
  })
);
["dragleave", "drop"].forEach((ev) =>
  els.dropzone?.addEventListener(ev, (e) => {
    e.preventDefault();
    els.dropzone.classList.remove("dragover");
  })
);
els.dropzone?.addEventListener("drop", (e) => {
  const file = e.dataTransfer?.files?.[0];
  if (file) onFileSelected(file);
});

function onFileSelected(file) {
  state.file = file;
  els.fileInfo.textContent = `${file.name} — ${(file.size / (1024 * 1024)).toFixed(2)} MB`;
  els.startBtn.disabled = false;
  resetUI();
  // Show a local preview in the main panel
  if (els.uploadedVideoMain) {
    const url = URL.createObjectURL(file);
    els.uploadedVideoMain.src = url;
    try {
      els.uploadedVideoMain.load();
      // Do not autoplay here; will play after Start Scan is pressed
    } catch {}
  }
}

// Controls
els.startBtn?.addEventListener("click", startScan);
els.cancelBtn?.addEventListener("click", cancelScan);
els.clearBtn?.addEventListener("click", clearAll);
els.retryBtn?.addEventListener("click", () => {
  resetUI();
  if (els.clearBtn) els.clearBtn.disabled = false;
  if (state.file) startScan();
});

async function startScan() {
  resetUI();
  if (!state.file) return;
  state.done = false;
  state.canceled = false;
  els.startBtn.disabled = true; // prevent double starts

  // Upload
  setProgress(2, "Uploading video...");
  const form = new FormData();
  form.append("file", state.file);

  let session_id;
  try {
    const uploadRes = await apiFetch(`${API.base}${API.upload}`, { method: "POST", body: form }, 300000);
    if (!uploadRes.ok) {
      showError(`Upload failed (${uploadRes.status})`);
      els.retryBtn.hidden = false;
      els.startBtn.disabled = false;
      return;
    }
    ({ session_id } = await uploadRes.json());
    state.sessionId = session_id;
  } catch (err) {
    console.error("Upload error:", err);
    showError("Upload failed. Is the backend running?");
    els.retryBtn.hidden = false;
    els.startBtn.disabled = false;
    return;
  }
  // keep Start disabled after upload started

  // Start scan
  try {
    const startRes = await apiFetch(`${API.base}${API.scan(session_id)}`, { method: "POST" }, 15000);
    if (!startRes.ok) {
      showError(`Failed to start scan (${startRes.status})`);
      els.retryBtn.hidden = false;
      els.startBtn.disabled = false;
      return;
    }
  } catch (err) {
    console.error("Start scan error:", err);
    showError("Could not start scan. Check server.");
    els.retryBtn.hidden = false;
    els.startBtn.disabled = false;
    return;
  }

  els.cancelBtn.disabled = false;
  if (els.clearBtn) els.clearBtn.disabled = false;
  setProgress(5, "Queued...");
  setStage("frames", "active");
  // Ensure the preview video is playing during processing
  try {
    if (els.uploadedVideoMain) {
      els.uploadedVideoMain.muted = true;
      els.uploadedVideoMain.play().catch(() => {});
    }
  } catch {}

  openSSE();
}

function openSSE() {
  if (!state.sessionId) return;
  if (state.sse) state.sse.close();
  const es = new EventSource(`${API.base}${API.stream(state.sessionId)}`);
  state.sse = es;

  es.onmessage = (e) => {
    if (!e.data) return;
    try { handleEvent(JSON.parse(e.data)); } catch { /* noop */ }
  };
  es.addEventListener("keep-alive", () => {});
  es.addEventListener("error", () => {
    if (!state.done && !state.canceled) {
      showError("Stream error. Attempting to recover...");
      pollStatus();
    }
  });
  es.addEventListener("open", () => {
    // Stream opened: make the live status reflect that we're connected
    if (els.liveStatus) els.liveStatus.textContent = "Connected";
  });
}

async function pollStatus() {
  if (!state.sessionId) return;
  try {
    const res = await apiFetch(`${API.base}${API.status(state.sessionId)}`, {}, 5000);
    if (!res.ok) return;
    const m = await res.json();
    ["frames", "faces", "inference"].forEach((s) => {
      const st = m.stages?.[s]?.status || "pending";
      setStage(s, st === "running" ? "active" : st);
    });
    if (m.status === "done" && m.result) {
      finishWithResult(m.result);
    } else if (m.status === "error") {
      showError(m.error || "Error");
      els.retryBtn.hidden = false;
    }
  } catch { /* transient */ }
}

function handleEvent(data) {
  if (data.status) {
    els.legacy.progressLog && logLegacy(data.status);
  }

  // Update stage badges and progress
  if (data.stage) {
    const stage = String(data.stage);
    if (stage === "frames") {
      setStage("frames", "active");
      setStage("faces", "pending");
      setStage("inference", "pending");
      const n = Number(data.frames_count || 0);
      setProgress(25, `Extracting frames... (${n})`);
    } else if (stage === "faces") {
      setStage("frames", "done");
      setStage("faces", "active");
      setStage("inference", "pending");
      const n = Number(data.faces_count || 0);
      setProgress(65, `Detecting faces... (${n})`);
      // Draw boxes with scores on the live frame if provided
      if (els.liveFrame && data.faces && data.faces.length > 0 && Array.isArray(data.boxes) && Array.isArray(data.box_preds)) {
        // liveFrame already shows the vis image with server-side overlays; nothing extra needed
        // But if in future we send raw frames + boxes, we could draw overlays on a canvas here.
      }
    } else if (stage === "inference") {
      setStage("frames", "done");
      setStage("faces", "done");
      setStage("inference", "active");
      setProgress(90, "Predicting...");
    }
  }

  // Live frame: prefer last faces vis, else last crop, else last frame
  const nextB64 = (Array.isArray(data.faces) && data.faces[data.faces.length - 1])
               || (Array.isArray(data.crops) && data.crops[data.crops.length - 1])
               || (Array.isArray(data.frames) && data.frames[data.frames.length - 1]);
  if (nextB64 && els.liveFrame) {
    els.liveFrame.src = `data:image/jpeg;base64,${nextB64}`;
  }
  // Update the side "Current face" with the most recent crop
  if (Array.isArray(data.crops) && els.liveCurrentCrop) {
    const b64 = data.crops[data.crops.length - 1];
    if (b64) {
      els.liveCurrentCrop.innerHTML = "";
      const img = new Image();
      img.src = `data:image/jpeg;base64,${b64}`;
      img.loading = "lazy";
      els.liveCurrentCrop.appendChild(img);
    }
  }
  if (data.prediction) {
    const label = data.prediction?.prediction || "";
    const conf = Number(data.prediction?.confidence || 0);
    const pct = Math.round(conf * 100);
    const isFake = String(label).toUpperCase() === "FAKE";
    // Swap live frame to a clean raw frame to avoid leftover boxes
    if (Array.isArray(data.frames) && data.frames.length > 0 && els.liveFrame) {
      const raw = data.frames[data.frames.length - 1];
      els.liveFrame.src = `data:image/jpeg;base64,${raw}`;
    }
    const badge = `<span class="result-badge ${isFake ? "fake" : "real"}">${isFake ? "DEEPFAKE" : "REAL"}</span>`;
    const confHtml = `<span class="result-confidence ${isFake ? "fake" : "real"}"><span class="val">${pct}%</span> confidence</span>`;
    els.resultText.innerHTML = `${badge} ${confHtml}`;
    els.resultSection.hidden = false;
    setProgress(100, "Done");
    state.done = true;
    if (els.liveStatus) els.liveStatus.textContent = "Done";
    // Apply subtle background tint by outcome
    try {
      document.body.classList.remove("outcome-real", "outcome-fake");
      document.body.classList.add(isFake ? "outcome-fake" : "outcome-real");
    } catch {}
  }
  if (data.done) {
    state.done = true;
    setStage("frames", "done");
    setStage("faces", "done");
    setStage("inference", "done");
    setProgress(100, "Done");
    if (els.liveStatus) els.liveStatus.textContent = "Done";
    // Also ensure the final live frame is raw if available
    if (Array.isArray(data.frames) && data.frames.length > 0 && els.liveFrame) {
      const raw = data.frames[data.frames.length - 1];
      els.liveFrame.src = `data:image/jpeg;base64,${raw}`;
    }
  }

  // Show errors if status indicates
  if (typeof data.status === "string" && data.status.toLowerCase().startsWith("error")) {
    showError(data.status);
  }
}

function addB64Img(container, b64) {
  const img = new Image();
  img.loading = "lazy";
  img.decoding = "async";
  img.src = `data:image/jpeg;base64,${b64}`;
  container.appendChild(img);
}

function finishWithResult(result) {
  const label = result?.prediction || "";
  const conf = Number(result?.confidence || 0);
  const pct = Math.round(conf * 100);
  const isFake = String(label).toUpperCase() === "FAKE";
  const badge = `<span class="result-badge ${isFake ? "fake" : "real"}">${isFake ? "DEEPFAKE" : "REAL"}</span>`;
  els.resultText.innerHTML = `${badge} &nbsp; ${pct}% confidence`;
  els.resultSection.hidden = false;
  setProgress(100, "Done");
  if (els.liveStatus) els.liveStatus.textContent = "Done";
  try {
    document.body.classList.remove("outcome-real", "outcome-fake");
    document.body.classList.add(isFake ? "outcome-fake" : "outcome-real");
  } catch {}

  // Color-code previews
  const gridImgs = [
    ...((els.cropsGrid && els.cropsGrid.querySelectorAll("img")) || []),
    ...((els.framesGrid && els.framesGrid.querySelectorAll("img")) || []),
  ];
  gridImgs.forEach((img) => {
    img.classList.remove("real", "fake");
    img.classList.add(isFake ? "fake" : "real");
  });
}

async function clearAll() {
  try {
    if (state.sessionId) {
      try { await apiFetch(`${API.base}${API.cancel(state.sessionId)}`, { method: "POST" }, 8000); } catch {}
      try { await apiFetch(`${API.base}${API.clear(state.sessionId)}`, { method: "POST" }, 20000); } catch {}
    }
  } finally {
    if (state.sse) { try { state.sse.close(); } catch {} }
    state = { file: null, sessionId: null, sse: null, done: false, canceled: false };
    resetUI();
    if (els.fileInput) els.fileInput.value = "";
    els.fileInfo.textContent = "";
    els.startBtn.disabled = true;
    if (els.uploadedVideoMain) {
      try { els.uploadedVideoMain.pause?.(); } catch {}
      els.uploadedVideoMain.removeAttribute("src");
      try { els.uploadedVideoMain.load(); } catch {}
    }
  }
}

async function cancelScan() {
  if (!state.sessionId) return;
  els.cancelBtn.disabled = true;
  try {
    await apiFetch(`${API.base}${API.cancel(state.sessionId)}`, { method: "POST" }, 10000);
    state.canceled = true;
    if (state.sse) state.sse.close();
  } catch {}
  showError("Canceled");
  els.retryBtn.hidden = false;
}

// Legacy helpers (kept for hidden elements)
function logLegacy(message) {
  const el = els.legacy.progressLog;
  if (!el) return;
  const entry = document.createElement("div");
  entry.textContent = message;
  el.appendChild(entry);
  el.scrollTop = el.scrollHeight;
}
