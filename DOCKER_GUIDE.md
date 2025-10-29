# Docker Build & Push Guide for DF-SCAN

## Quick Start

### 1. Build and Push to Docker Hub

```bash
# Login to Docker Hub (first time only)
docker login

# Build and push with automatic version
./build-and-push.sh

# Or specify a custom version
./build-and-push.sh v1.2.0
```

### 2. Test Locally First

```bash
# Build the image
docker build -t sudipxo/df-scan:test .

# Run locally to test
docker run -p 8000:8000 sudipxo/df-scan:test

# Or use docker-compose
docker-compose up
```

## Manual Build & Push Commands

```bash
# 1. Login to Docker Hub
docker login

# 2. Build the image with tags
docker build -t sudipxo/df-scan:v1.2.0 -t sudipxo/df-scan:latest .

# 3. Push to Docker Hub
docker push sudipxo/df-scan:v1.2.0
docker push sudipxo/df-scan:latest
```

## Multi-platform Build (ARM64 + AMD64)

For supporting multiple architectures:

```bash
# Create a builder instance (first time only)
docker buildx create --name mybuilder --use

# Build and push for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t sudipxo/df-scan:v1.2.0 \
  -t sudipxo/df-scan:latest \
  --push \
  .
```

## Verify Your Image

```bash
# Check local images
docker images | grep df-scan

# Pull from Docker Hub to verify
docker pull sudipxo/df-scan:latest

# Run health check
docker run -p 8000:8000 sudipxo/df-scan:latest &
sleep 10
curl http://localhost:8000/health
```

## Update Version in docker-compose.yml

After pushing a new version, update `docker-compose.yml`:

```yaml
services:
  df-scan:
    image: sudipxo/df-scan:v1.2.0 # Needs Update
```

## Troubleshooting

### Build fails due to missing models
- Ensure `backend/models/production1000_temporal_model.pth` exists
- Check that the model file is not in `.dockerignore`

### Image is too large
- Current Dockerfile uses slim base and cleanup
- Consider using multi-stage build if needed
- Check `.dockerignore` to exclude unnecessary files

### Push fails with authentication error
```bash
# Re-login to Docker Hub
docker logout
docker login
```

### Test container won't start
```bash
# Check logs
docker logs <container_id>

# Inspect the container
docker inspect <container_id>

# Run interactively for debugging
docker run -it --entrypoint /bin/bash sudipxo/df-scan:latest
```

## Docker Hub Repository

Image will be available at:
- https://hub.docker.com/r/sudipxo/df-scan

