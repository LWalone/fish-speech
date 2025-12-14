#!/bin/bash

# Fish Speech All-in-One Container Launcher
# Version: 1.2.0
# Features: Speaker Management + Auto-transcription

VERSION="all-in-one-v1.2.0"
IMAGE="neosun/fish-speech:${VERSION}"
CONTAINER_NAME="fish-speech-v1.2.0"
PORT=7864
GPU_ID=2

echo "=========================================="
echo "Fish Speech All-in-One Launcher"
echo "=========================================="
echo "Image: ${IMAGE}"
echo "Container: ${CONTAINER_NAME}"
echo "Port: ${PORT}"
echo "GPU: ${GPU_ID}"
echo "=========================================="

# Stop and remove old container if exists
if [ "$(docker ps -aq -f name=${CONTAINER_NAME})" ]; then
    echo "Stopping existing container..."
    docker stop ${CONTAINER_NAME}
    docker rm ${CONTAINER_NAME}
fi

# Pull latest image
echo "Pulling latest image..."
docker pull ${IMAGE}

# Start container
echo "Starting container..."
docker run -d \
    --name ${CONTAINER_NAME} \
    --gpus '"device='${GPU_ID}'"' \
    -p ${PORT}:7864 \
    -v $(pwd)/checkpoints:/app/checkpoints \
    -v $(pwd)/speakers:/app/speakers \
    --health-cmd "curl -f http://localhost:7864/health || exit 1" \
    --health-interval=30s \
    --health-timeout=10s \
    --health-retries=3 \
    ${IMAGE}

echo "=========================================="
echo "Container started successfully!"
echo "UI:     http://localhost:${PORT}"
echo "API:    http://localhost:${PORT}/api/tts"
echo "Docs:   http://localhost:${PORT}/docs"
echo "Health: http://localhost:${PORT}/health"
echo "=========================================="
echo ""
echo "Features:"
echo "✓ Auto-transcription with Whisper Turbo"
echo "✓ Voice cloning (5-10s reference audio)"
echo "✓ Emotion & tone markers support"
echo "✓ GPU acceleration (GPU ${GPU_ID})"
echo "=========================================="
echo ""
echo "Check logs: docker logs -f ${CONTAINER_NAME}"
echo "Stop:       docker stop ${CONTAINER_NAME}"
