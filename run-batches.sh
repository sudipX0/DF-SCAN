#!/bin/bash

# Array of batch numbers
batches=(9 10)

# Loop through each batch
for batch in "${batches[@]}"; do
    echo "Starting face detection for intermediate_100_batch${batch}..."
    python scripts/detect_faces_v2.py \
        --frames_root ~/DF-SCAN/data/intermediate_100_batch${batch}/frames \
        --faces_root ~/DF-SCAN/data/intermediate_100_batch${batch}/faces \
        --workers 6
    echo "Completed face detection for intermediate_100_batch${batch}."
done

echo "All batches processed!"
