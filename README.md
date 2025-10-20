!["DFSCAN Banner"](logo.png)

# DF-SCAN  
A deepfake video detection system that determines whether a video is **real** or **fake** using deep learning.  
The system analyzes both spatial (frame-level) and temporal (sequence-level) patterns to identify manipulations and display authenticity results with confidence scores and visual cues.

## Experimental Architecture  
Hybrid **CNN + LSTM** architecture that captures  
- **Spatial inconsistencies** (per-frame CNN features)  
- **Temporal correlations** (LSTM sequence modeling)  

## Model Evolution Summary (Currently Experimenting)

| **Model** | **Architecture** | **Video Samples** | **Accuracy** | **ROC-AUC** | **REAL F1** | **FAKE F1** | **Key Observation** |
|------------|------------------|------------------:|--------------:|-------------:|-------------:|-------------:|----------------------|
| **Model 1** | ResNet18 (Frame-based Baseline) | 100 | **0.86** | 0.8415 | 0.52 | 0.92 | Strong on fakes, weak on reals; lacks temporal cues |
| **Model 2** | CNN + LSTM (Temporal Baseline) | 100 | **0.83** | 0.7719 | 0.44 | 0.90 | Temporal modeling added, but underfit due to limited data |
| **Model 3** | CNN + LSTM | 300 | **0.90** | 0.9020 | 0.68 | 0.94 | Temporal learning effective; significant jump in AUC |
| **Model 4** | CNN + LSTM | 500 | **0.94** | **0.9506** | **0.76** | **0.96** | Excellent balance; near production-grade performance |
| **Model 5** | CNN + LSTM | **800** | **0.95** | **0.9746** | **0.82** | **0.97** | Outstanding generalization; strong REAL recovery; approaching deployment quality |
| **Model 6** | CNN + LSTM | **1000** | **0.96** | **0.9830** | **0.87** | **0.98** | Production-grade reliability; nearly perfect fake detection; strong real recall; robust and stable model behavior |

## Accuracy by Deepfake Type

| **Deepfake Type** | **Model 1 (100V ResNet18)** | **Model 2 (100V CNN + LSTM)** | **Model 3 (300V)** | **Model 4 (500V)** | **Model 5 (800V)** | **Model 6 (1000V)** | **Trend** |
|--------------------|------------------------------:|-------------------------------:|--------------------:|--------------------:|--------------------:|--------------------:|------------|
| **Face2Face** | 100.00 % | 93.75 % | 88.24 % | **100.00 %** | **94.29 %** | **97.14 %** | Stable high accuracy; slight recovery after minor dip |
| **NeuralTextures** | 83.33 % | 79.17 % | 82.05 % | **95.95 %** | **91.53 %** | **93.28 %** | Improved consistency; handles visual texture variations better |
| **Deepfakes** | 82.35 % | 88.24 % | 97.37 % | **98.72 %** | **100.00 %** | **100.00 %** | Fully saturated detection; perfect classification |
| **FaceSwap** | 94.44 % | 94.44 % | 85.71 % | **92.94 %** | **97.35 %** | **98.52 %** | Steady enhancement; strong across versions |
| **DeepFakeDetection** | 100.00 % | 100.00 % | 100.00 % | **100.00 %** | **100.00 %** | **100.00 %** | Saturated; complete detection |
| **FaceShifter** | 100.00 % | 90.00 % | 98.04 % | **100.00 %** | **95.28 %** | **96.47 %** | Marginal improvement; robust temporal capture |
| **REAL** | 53.33 % | 46.67 % | 75.56 % | **69.33 %** | **85.00 %** | **82.00 %** | Slight dip due to dataset imbalance but strong overall recovery |

## Observations

### **Scaling Up Helps**  
Each dataset expansion improved overall accuracy and ROC-AUC; the model exhibits continued growth, with performance nearing saturation at 1000 videos.

### **REAL Class Recovery**  
REAL class recall and F1 show large gains over earlier versions (0.52 → 0.87), though a small decline in recall at 1000V indicates minor overfitting toward fake-dominant samples.

### **High AUC (0.9830)**  
Model achieves exceptional class separability and well-calibrated probabilities. Predictions are highly confident and consistent across fake types.

### **Fake Class Robustness**  
Fake categories maintain near-perfect scores across all versions. Model successfully generalizes across manipulation methods, highlighting its strength in learning consistent spatiotemporal artifacts.

### **Minor REAL Sensitivity Drop**  
REAL recall (0.82) indicates a small number of genuine videos still misclassified as fake, likely due to dataset imbalance and real-video variability such as lighting or compression artifacts.

### **Approaching Production Readiness**  
At 1000 samples, DF-SCAN demonstrates stable, generalizable, and nearly saturated performance.