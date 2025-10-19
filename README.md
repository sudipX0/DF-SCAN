!["DFSCAN Banner"](banner.png)

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
| **Model 5** | CNN + LSTM (Final Expanded) | **800** | **0.95** | **0.9746** | **0.82** | **0.97** | Outstanding generalization; strong REAL recovery; approaching deployment quality |

## Accuracy by Deepfake Type

| **Deepfake Type** | **Model 1 (100V ResNet18)** | **Model 2 (100V CNN + LSTM)** | **Model 3 (300V)** | **Model 4 (500V)** | **Model 5 (800V)** | **Trend** |
|--------------------|------------------------------:|-------------------------------:|--------------------:|--------------------:|--------------------:|------------|
| **Face2Face** | 100.00 % | 93.75 % | 88.24 % | **100.00 %** | **94.29 %** | Slight dip; still robust |
| **NeuralTextures** | 83.33 % | 79.17 % | 82.05 % | **95.95 %** | **91.53 %** | Minor regression, likely due to higher variety |
| **Deepfakes** | 82.35 % | 88.24 % | 97.37 % | **98.72 %** | **100.00 %** | Perfect detection |
| **FaceSwap** | 94.44 % | 94.44 % | 85.71 % | **92.94 %** | **97.35 %** | Consistent improvement |
| **DeepFakeDetection** | 100.00 % | 100.00 % | 100.00 % | **100.00 %** | **100.00 %** | Fully saturated |
| **FaceShifter** | 100.00 % | 90.00 % | 98.04 % | **100.00 %** | **95.28 %** | Slightly lower but stable |
| **REAL** | 53.33 % | 46.67 % | 75.56 % | **69.33 %** | **85.00 %** | Huge recovery; best so far |


## Observations

**Scaling Up Helps**  
Each dataset expansion improved overall accuracy and ROC-AUC; the model has not yet saturated.  
**REAL Class Recovery**  
Substantial F1 gain (0.52 → 0.82) and accuracy (53 % → 85 %), indicating stronger generalization.  
**High AUC (0.9746)**  
Suggests excellent class separability and confidence calibration.  
**Minor Type Variance**  
Slight dips in *Face2Face* and *NeuralTextures* likely due to diverse motion artifacts or dataset imbalance.  

