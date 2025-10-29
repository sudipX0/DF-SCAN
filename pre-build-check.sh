#!/bin/bash
# Pre-build verification script for DF-SCAN Docker image
# Run this before building to ensure everything is ready

set -e

echo "================================================"
echo "DF-SCAN Docker Pre-Build Verification"
echo "================================================"
echo ""

ERRORS=0
WARNINGS=0

# Check 1: Required files
echo "✓ Checking required files..."
REQUIRED_FILES=(
    "Dockerfile"
    "requirements.txt"
    "backend/app.py"
    "backend/model.py"
    "backend/models/production1000_temporal_model.pth"
    "frontend/index.html"
    "frontend/script.js"
    "frontend/style.css"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ Missing: $file"
        ((ERRORS++))
    fi
done

# Check 2: Model file size
echo ""
echo "✓ Checking model files..."
MODEL_FILE="backend/models/production1000_temporal_model.pth"
if [ -f "$MODEL_FILE" ]; then
    SIZE=$(stat -f%z "$MODEL_FILE" 2>/dev/null || stat -c%s "$MODEL_FILE" 2>/dev/null || echo "0")
    SIZE_MB=$((SIZE / 1024 / 1024))
    if [ $SIZE_MB -gt 10 ]; then
        echo "  ✅ Model file size: ${SIZE_MB}MB (OK)"
    else
        echo "  ⚠️  Model file seems small: ${SIZE_MB}MB"
        ((WARNINGS++))
    fi
else
    echo "  ❌ Model file not found"
    ((ERRORS++))
fi

# Check 3: Docker installation
echo ""
echo "✓ Checking Docker..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo "  ✅ $DOCKER_VERSION"
else
    echo "  ❌ Docker not installed"
    ((ERRORS++))
fi

# Check 4: Docker daemon running
if docker info &> /dev/null; then
    echo "  ✅ Docker daemon is running"
else
    echo "  ❌ Docker daemon is not running"
    ((ERRORS++))
fi

# Check 5: Disk space
echo ""
echo "✓ Checking disk space..."
AVAILABLE=$(df -h . | awk 'NR==2 {print $4}')
echo "  Available space: $AVAILABLE"

# Check 6: .dockerignore
echo ""
echo "✓ Checking .dockerignore..."
if [ -f ".dockerignore" ]; then
    echo "  ✅ .dockerignore exists"
    if grep -q "backend/temp" .dockerignore; then
        echo "  ✅ Excludes backend/temp"
    else
        echo "  ⚠️  Should exclude backend/temp"
        ((WARNINGS++))
    fi
else
    echo "  ⚠️  No .dockerignore file"
    ((WARNINGS++))
fi

# Check 7: Python dependencies
echo ""
echo "✓ Checking requirements.txt..."
if [ -f "requirements.txt" ]; then
    DEPS=$(wc -l < requirements.txt)
    echo "  ✅ $DEPS dependencies listed"
    
    # Check for key dependencies
    for dep in "fastapi" "torch" "opencv" "Pillow"; do
        if grep -qi "$dep" requirements.txt; then
            echo "  ✅ $dep found"
        else
            echo "  ⚠️  $dep not found in requirements.txt"
            ((WARNINGS++))
        fi
    done
else
    echo "  ❌ requirements.txt not found"
    ((ERRORS++))
fi

# Check 8: Docker Hub login (optional)
echo ""
echo "✓ Checking Docker Hub login..."
if docker info 2>/dev/null | grep -q "Username:"; then
    USERNAME=$(docker info 2>/dev/null | grep "Username:" | awk '{print $2}')
    echo "  ✅ Logged in as: $USERNAME"
else
    echo "  ⚠️  Not logged in to Docker Hub (required for push)"
    echo "     Run: docker login"
    ((WARNINGS++))
fi

# Summary
echo ""
echo "================================================"
echo "Verification Summary"
echo "================================================"
echo "Errors: $ERRORS"
echo "Warnings: $WARNINGS"
echo ""

if [ $ERRORS -eq 0 ]; then
    echo "✅ All critical checks passed!"
    echo ""
    echo "Ready to build! Run:"
    echo "  ./build-and-push.sh"
    echo ""
    echo "Or manually:"
    echo "  docker build -t sudipxo/df-scan:v1.2.0 ."
    exit 0
else
    echo "❌ Please fix errors before building"
    exit 1
fi
