#!/bin/bash

RAW_DATA=~/DF-SCAN/data/raw/ff-c23/FaceForensics++_C23
SAMPLE_DATA=~/DF-SCAN/data/experiment_100_batch10/ff-c23/FaceForensics++_C23

mkdir -p $SAMPLE_DATA

# For each manipulation class
for class in DeepFakeDetection Deepfakes Face2Face FaceShifter FaceSwap NeuralTextures original; do
    echo "Processing $class..."
    mkdir -p "$SAMPLE_DATA/$class"

    # Skip first 100 and take next 100
    find "$RAW_DATA/$class" -maxdepth 1 -type f -name "*.mp4" | sort | tail -n +901 | head -n 100 | \
    while read file; do
        cp "$file" "$SAMPLE_DATA/$class/"
    done
done
