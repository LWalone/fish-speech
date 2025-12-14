# Fish Speech - Advanced Text-to-Speech with Speaker Management

[English](README.md) | [简体中文](README_CN.md) | [繁體中文](README_TW.md) | [日本語](README_JP.md)

[![Docker Pulls](https://img.shields.io/docker/pulls/neosun/fish-speech)](https://hub.docker.com/r/neosun/fish-speech)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.2.0-green.svg)](https://github.com/neosun100/fish-speech/releases)

> 🐟 Advanced multilingual Text-to-Speech system with speaker management, auto-transcription, and emotion control

## ✨ Features

- 🎤 **Speaker Management** - Register and reuse voice profiles
- 🔄 **Auto-Transcription** - Automatic reference text generation with Whisper Turbo
- 🌍 **Multilingual** - Support for 8+ languages (EN, ZH, JA, KO, FR, DE, AR, ES)
- 😊 **Emotion Control** - 40+ emotion and tone markers
- ⚡ **GPU Accelerated** - Fast inference with CUDA support
- 🐳 **Docker Ready** - One-command deployment
- 📡 **REST API** - Complete FastAPI + Swagger documentation
- 🎨 **WebUI** - User-friendly Gradio interface

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
docker run -d \
  --name fish-speech \
  --gpus all \
  -p 7864:7864 \
  -v $(pwd)/checkpoints:/app/checkpoints \
  -v $(pwd)/speakers:/app/speakers \
  neosun/fish-speech:all-in-one-v1.2.0
```

Access:
- WebUI: http://localhost:7864
- API Docs: http://localhost:7864/docs

### Option 2: From Source

```bash
# Clone repository
git clone https://github.com/neosun100/fish-speech.git
cd fish-speech

# Install dependencies
pip install -r requirements.txt

# Download models
# Place models in checkpoints/openaudio-s1-mini/

# Run server
python unified_server.py --port 7864 --device cuda
```

## 📦 Installation

### Prerequisites

- Python 3.10+
- CUDA 11.8+ (for GPU acceleration)
- Docker 20.10+ (for Docker deployment)
- 8GB+ GPU memory recommended

### Docker Deployment

#### Pull Image

```bash
docker pull neosun/fish-speech:all-in-one-v1.2.0
```

#### Run Container

```bash
docker run -d \
  --name fish-speech-v1.2.0 \
  --gpus '"device=0"' \
  -p 7864:7864 \
  -e PORT=7864 \
  -v $(pwd)/checkpoints:/app/checkpoints \
  -v $(pwd)/speakers:/app/speakers \
  --health-cmd "curl -f http://localhost:7864/health || exit 1" \
  --health-interval=30s \
  neosun/fish-speech:all-in-one-v1.2.0
```

#### Using Docker Compose

```yaml
version: '3.8'
services:
  fish-speech:
    image: neosun/fish-speech:all-in-one-v1.2.0
    container_name: fish-speech
    ports:
      - "7864:7864"
    environment:
      - PORT=7864
      - DEVICE=cuda
    volumes:
      - ./checkpoints:/app/checkpoints
      - ./speakers:/app/speakers
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:7864/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

Run: `docker-compose up -d`

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 7862 | Server port |
| `DEVICE` | cuda | Device (cuda/cpu) |
| `COMPILE` | 0 | Enable torch compile |
| `HALF` | 0 | Use half precision |
| `LLAMA_CHECKPOINT_PATH` | checkpoints/openaudio-s1-mini | Model path |

### Volume Mounts

- `/app/checkpoints` - Model files (required)
- `/app/speakers` - Speaker profiles (persistent storage)

## 💡 Usage Examples

### 1. Register a Speaker

```bash
curl -X POST "http://localhost:7864/api/speakers" \
  -F "name=Alice" \
  -F "description=Professional female voice" \
  -F "audio=@reference.wav"
```

### 2. Generate Speech with Speaker

```bash
curl -X POST "http://localhost:7864/api/tts/speaker/{speaker_id}" \
  -F "text=Hello, this is a test." \
  -o output.wav
```

### 3. TTS with Emotions

```bash
curl -X POST "http://localhost:7864/api/tts" \
  -F "text=(excited) This is amazing! (laughing) Ha ha ha!" \
  -F "reference_audio=@voice.wav" \
  -o emotional_speech.wav
```

### 4. Auto-Transcription

```bash
curl -X POST "http://localhost:7864/api/transcribe" \
  -F "audio=@audio.wav"
```

## 📡 API Documentation

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/gpu/status` | GPU status |
| POST | `/api/transcribe` | Transcribe audio |
| GET | `/api/speakers` | List speakers |
| POST | `/api/speakers` | Register speaker |
| GET | `/api/speakers/{id}` | Get speaker |
| PUT | `/api/speakers/{id}` | Update speaker |
| DELETE | `/api/speakers/{id}` | Delete speaker |
| POST | `/api/tts` | Generate speech |
| POST | `/api/tts/speaker/{id}` | TTS with speaker |

Full API documentation: http://localhost:7864/docs

## 🏗️ Project Structure

```
fish-speech/
├── unified_server.py      # Main server
├── gpu_manager.py          # GPU management
├── fish_speech/            # Core TTS engine
├── tools/                  # Utilities
├── checkpoints/            # Model files
├── speakers/               # Speaker profiles
├── Dockerfile.allinone     # Docker build
└── docs/                   # Documentation
```

## 🛠️ Tech Stack

- **Framework**: FastAPI + Gradio
- **Model**: OpenAudio S1-mini (0.5B parameters)
- **Transcription**: Whisper Turbo
- **Inference**: PyTorch + CUDA
- **Deployment**: Docker + NVIDIA Container Toolkit

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 Changelog

### v1.2.0 (2025-12-14)
- ✨ Added complete speaker management system
- ✨ Speaker registration with auto-transcription
- ✨ Persistent speaker storage
- 📚 Complete API documentation

### v1.1.3 (2025-12-14)
- 🐛 Fixed Gradio auto-transcription bug
- 🔧 Improved audio file handling

### v1.1.2 (2025-12-14)
- ✨ Integrated Whisper Turbo
- ✨ Added transcription API

[Full Changelog](RELEASE_v1.2.0.md)

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

Model weights are released under CC-BY-NC-SA-4.0 License.

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=neosun100/fish-speech&type=Date)](https://star-history.com/#neosun100/fish-speech)

## 📱 Follow Us

![公众号](https://img.aws.xin/uPic/扫码_搜索联合传播样式-标准色版.png)

---

**Made with ❤️ by the Fish Speech Community**
