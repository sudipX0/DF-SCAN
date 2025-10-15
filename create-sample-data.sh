#!/bin/bash

RAW_DATA=~/DF-SCAN/data/raw/ff-c23/FaceForensics++_C23
SAMPLE_DATA=~/DF-SCAN/data/experiment_10/ff-c23/FaceForensics++_C23

mkdir -p $SAMPLE_DATA

for class in DeepFakeDetection Deepfakes Face2Face FaceShifter FaceSwap NeuralTextures original; do
    echo "Processing $class..."
    mkdir -p "$SAMPLE_DATA/$class"

    find "$RAW_DATA/$class" -maxdepth 1 -type f -name "*.mp4" | sort | head -n 10 | \
    while read file; do
        cp "$file" "$SAMPLE_DATA/$class/"
    done
done
