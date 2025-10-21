!['DFSCAN Banner'](logo.png)

# DF-SCAN  
A deepfake video detection system that determines whether a video is **real** or **fake** using deep learning.  
The system analyzes both spatial (frame-level) and temporal (sequence-level) patterns to identify manipulations and display authenticity results with confidence scores and visual cues.

## Experimental Architecture  
Hybrid **CNN + LSTM** or **CNN + Transformer** architecture that captures:  
- **Spatial inconsistencies** (per-frame CNN features)  
- **Temporal correlations** (LSTM/Transformer sequence modeling)  

## Model Evolution Summary (Currently Experimenting)

| **Model** | **Architecture** | **Video Samples** | **Accuracy** | **ROC-AUC** | **REAL F1** | **FAKE F1** | **Key Observation** |
|------------|------------------|------------------:|--------------:|-------------:|-------------:|-------------:|----------------------|
| **Model 1** | ResNet18 (Frame-based Baseline) | 100 | **0.86** | 0.8415 | 0.52 | 0.92 | Strong on fakes, weak on reals; lacks temporal cues |
| **Model 2** | CNN + LSTM (Temporal Baseline) | 100 | **0.83** | 0.7719 | 0.44 | 0.90 | Temporal modeling added, but underfit due to limited data |
| **Model 3** | CNN + LSTM | 300 | **0.90** | 0.9020 | 0.68 | 0.94 | Temporal learning effective; significant jump in AUC |
| **Model 4** | CNN + LSTM | 500 | **0.94** | **0.9506** | **0.76** | **0.96** | Excellent balance; near production-grade performance |
| **Model 5** | CNN + LSTM | **800** | **0.95** | **0.9746** | **0.82** | **0.97** | Outstanding generalization; strong REAL recovery; approaching deployment quality |
| **Model 6** | CNN + LSTM | **1000** | **0.96** | **0.9830** | **0.87** | **0.98** | Production-grade reliability; nearly perfect fake detection; strong real recall; robust and stable model behavior |
| **Model 7 (Celeb-DF Fine-tuned)** | CNN + LSTM | **Celeb-DF (980 samples)** | **0.77** | **0.8243** | **0.44** | **0.86** | Good generalization but biased toward fakes; REAL recall needs improvement |
| **Model 8 (FaceForensics++ Transformer)** | CNN + Transformer | **1000** | **0.95** | **0.9510** | **0.82** | **0.97** | Strong overall performance; balanced REAL/FAKE detection; robust across fake types; best choice for deployment |

---

## Accuracy by Deepfake Type

| **Deepfake Type** | **Model 6 (LSTM 1000V)** | **Model 7 (Celeb-DF)** | **Model 8 (Transformer 1000V)** |
|--------------------|--------------------------:|------------------------:|------------------------------:|
| **Face2Face**      | 97.14 %                  | -                      | 96.95 %                        |
| **NeuralTextures** | 93.28 %                  | -                      | 93.84 %                        |
| **Deepfakes**      | 100.00 %                 | -                      | 97.99 %                        |
| **FaceSwap**       | 98.52 %                  | -                      | 96.38 %                        |
| **DeepFakeDetection** | 100.00 %               | -                      | 98.71 %                        |
| **FaceShifter**    | 96.47 %                  | -                      | 94.59 %                        |
| **REAL**           | 82.00 %                  | 67.16 %                | 84.67 %                        |

---

## Observations

### **Scaling Up Helps**  
Each dataset expansion improved overall accuracy and ROC-AUC; the model exhibits continued growth, with performance nearing saturation at 1000 videos.

### **REAL Class Recovery**  
- LSTM Model 6: 0.87 F1  
- Transformer Model 8: 0.82 F1  
- Celeb-DF fine-tune: 0.44 F1  

The Transformer model slightly trades some AUC for improved REAL/FAKE balance and robustness across fake types.

### **High AUC**  
- LSTM Model 6: 0.9830  
- Transformer Model 8: 0.9510  

Both models are highly capable, but the Transformer offers more balanced predictions for real videos.

### **Fake Class Robustness**  
All models consistently achieve 94–100% across all fake types. Transformer Model 8 maintains strong generalization without biasing toward a single fake category.

### **Domain Transfer Risk**  
Celeb-DF fine-tuned Model 7 shows that naive fine-tuning can hurt REAL recall due to domain shift and dataset imbalance.

### **Best Model Recommendation**  
- **Use CNN + Transformer (Model 8) for deployment** on FaceForensics++.  
- Strong balanced REAL/FAKE detection (accuracy 0.95, AUC 0.951).  
- Excellent per-fake type generalization.  
- Optional fine-tuning can be considered **with class-balancing strategies** for further REAL recall improvement.
