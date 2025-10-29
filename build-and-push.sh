#!/bin/bash
# Build and push DF-SCAN Docker image to Docker Hub
# Usage: ./build-and-push.sh [version]

set -e

# Configuration
DOCKER_USERNAME="sudipxo"
IMAGE_NAME="df-scan"
VERSION="${1:-v1.2.0}"  # Default to v1.2.0 if no version specified

# Full image name
FULL_IMAGE="${DOCKER_USERNAME}/${IMAGE_NAME}"

echo "================================================"
echo "Building DF-SCAN Docker Image"
echo "================================================"
echo "Image: ${FULL_IMAGE}"
echo "Version: ${VERSION}"
echo "================================================"

# Check if logged in to Docker Hub
if ! docker info | grep -q "Username: ${DOCKER_USERNAME}"; then
    echo ""
    echo "⚠️  Not logged in to Docker Hub. Please run:"
    echo "   docker login"
    echo ""
    read -p "Do you want to login now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker login
    else
        echo "❌ Aborted. Please login first with: docker login"
        exit 1
    fi
fi

# Build the image
echo ""
echo "🔨 Building Docker image..."
docker build -t "${FULL_IMAGE}:${VERSION}" -t "${FULL_IMAGE}:latest" .

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

echo ""
echo "✅ Build successful!"
echo ""
echo "Images created:"
docker images | grep "${IMAGE_NAME}" | head -2

# Ask for confirmation before pushing
echo ""
read -p "Do you want to push to Docker Hub now? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "⏸️  Skipping push. You can push later with:"
    echo "   docker push ${FULL_IMAGE}:${VERSION}"
    echo "   docker push ${FULL_IMAGE}:latest"
    exit 0
fi

# Push to Docker Hub
echo ""
echo "📤 Pushing to Docker Hub..."
echo "Pushing ${FULL_IMAGE}:${VERSION}..."
docker push "${FULL_IMAGE}:${VERSION}"

echo "Pushing ${FULL_IMAGE}:latest..."
docker push "${FULL_IMAGE}:latest"

if [ $? -eq 0 ]; then
    echo ""
    echo "================================================"
    echo "✅ Successfully pushed to Docker Hub!"
    echo "================================================"
    echo "Image: ${FULL_IMAGE}:${VERSION}"
    echo "Latest: ${FULL_IMAGE}:latest"
    echo ""
    echo "You can now pull it with:"
    echo "   docker pull ${FULL_IMAGE}:${VERSION}"
    echo "   docker pull ${FULL_IMAGE}:latest"
    echo ""
    echo "Or run with docker-compose:"
    echo "   docker-compose up -d"
    echo "================================================"
else
    echo "❌ Push failed!"
    exit 1
fi
