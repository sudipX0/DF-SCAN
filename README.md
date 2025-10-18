!["DFSCAN Banner"](banner.png)
# DF-SCAN
A deepfake video detection system that detects whether a video is real or fake using deep learning techniques. The system analyzes video frames and temporal patterns to identify manipulations and display authenticity results with confidence scores and visual cues.
# EXPERIMENTAL ARCHITECTURE  
Hybrid **CNN + LSTM** architecture to train both **spatial (per-frame)** and **temporal (across-frames)** inconsistencies for near-accurate classifcation.

## Model Evolution Summary (Currently Experimenting)

| **Model** | **Architecture** | **# Videos** | **Accuracy** | **ROC-AUC** | **REAL F1** | **FAKE F1** | **Key Observation** |
|------------|------------------|--------------|---------------|--------------|--------------|--------------|----------------------|
| **Model 1** | ResNet18 (Frame-based Baseline) | 100 | **0.86** | 0.8415 | 0.52 | 0.92 | Strong on fakes, weak on reals; lacks temporal cues |
| **Model 2** | CNN + LSTM (Temporal Baseline) | 100 | **0.83** | 0.7719 | 0.44 | 0.90 | Added temporal modeling, but underfit due to limited data |
| **Model 3** | CNN + LSTM | 300 | **0.90** | 0.9020 | 0.68 | 0.94 | Temporal learning effective; significant jump in AUC |
| **Model 4** | CNN + LSTM | 500 | **0.94** | **0.9506** | **0.76** | **0.96** | Excellent balance; near production-grade performance |

## Accuracy by Deepfake Type

| **Deepfake Type** | **Model 1 (100V ResNet18)** | **Model 2 (100V CNN + LSTM)** | **Model 3 (300V)** | **Model 4 (500V)** | **Trend** |
|--------------------|------------------------------|-------------------------------|--------------------|--------------------|------------|
| **Face2Face** | 100.00 % | 93.75 % | 88.24 % | **100.00 %** | Recovered to perfection |
| **NeuralTextures** | 83.33 % | 79.17 % | 82.05 % | **95.95 %** | Steady improvement |
| **Deepfakes** | 82.35 % | 88.24 % | 97.37 % | **98.72 %** | Excellent progress |
| **FaceSwap** | 94.44 % | 94.44 % | 85.71 % | **92.94 %** | Stable overall |
| **DeepFakeDetection** | 100.00 % | 100.00 % | 100.00 % | **100.00 %** | Fully saturated |
| **FaceShifter** | 100.00 % | 90.00 % | 98.04 % | **100.00 %** | Fully saturated |
| **REAL** | 53.33 % | 46.67 % | 75.56 % | **69.33 %** | Major improvement, still a gap |

## Observations

- **Scaling Up Helps:**  
  Every increase in dataset size improves accuracy and AUC the model hasn’t yet saturated.  

- **REAL Class Challenge:**  
  REAL videos remain slightly under-recognized.

## Next Steps

1. **Freeze & Export Final Model:**  
   Save as `dfscan_resnetlstm_500.pth` or convert to TorchScript for deployment.  

2. **Backend API (FastAPI):**  
   Handle video upload → preprocess frames → run inference → return JSON results.  

3. **Frontend (React):**  
   Simple interface for video upload, progress indicator, and a confidence-based real/fake output visualization.  

4. **Future Work:**  
   - Try bidirectional LSTM for richer temporal encoding.  
   - Explore stronger backbones (ResNet34, EfficientNet).  
   - Integrate attention or transformer-based temporal modules.  
   
My experimentation demonstrates how combining **spatial feature extraction** with **temporal dynamics** can yield a highly reliable, end-to-end deepfake detection pipeline.

