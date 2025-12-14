# 🐟 Fish Speech Unified Deployment

> **OpenAudio S1** - State-of-the-art Text-to-Speech with UI, API, and MCP support

[![TTS-Arena2 #1](https://img.shields.io/badge/TTS_Arena2-Rank_%231-gold?style=flat-square)](https://huggingface.co/spaces/TTS-AGI/TTS-Arena-V2)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue?style=flat-square&logo=docker)](https://www.docker.com/)
[![GPU](https://img.shields.io/badge/GPU-CUDA-green?style=flat-square&logo=nvidia)](https://developer.nvidia.com/cuda-zone)

## 🎯 What's Included

This deployment provides **three access modes** in a single Docker container:

| Mode | Interface | Best For |
|------|-----------|----------|
| **UI** | Web Browser | Interactive testing, demos |
| **API** | REST/HTTP | Web services, integrations |
| **MCP** | Tool Protocol | Automation, scripts, AI agents |

**Key Features:**
- ✅ Automatic GPU selection (least used)
- ✅ Auto-offload after idle timeout
- ✅ Port conflict detection
- ✅ One-click startup
- ✅ Comprehensive monitoring
- ✅ Production-ready

## 🚀 Quick Start (3 Steps)

### 1. Download Models

```bash
python tools/download_models.py
```

Or manually from [HuggingFace](https://huggingface.co/fishaudio/openaudio-s1-mini)

### 2. Start Service

```bash
./start.sh
```

### 3. Access

```
✅ Fish Speech is running!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📱 UI:     http://0.0.0.0:7862
🔌 API:    http://0.0.0.0:7862/api/tts
📚 Docs:   http://0.0.0.0:7862/docs
💚 Health: http://0.0.0.0:7862/health
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [QUICKSTART.md](QUICKSTART.md) | Quick reference card |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Complete deployment guide |
| [MCP_GUIDE.md](MCP_GUIDE.md) | MCP server documentation |
| [CHECKLIST.md](CHECKLIST.md) | Deployment checklist |

## 🎨 Usage Examples

### Web UI

1. Open http://localhost:7862
2. Enter text: `(excited) This is amazing!`
3. Click "Generate"
4. Download audio

### REST API

```bash
# Basic generation
curl -X POST http://localhost:7862/api/tts \
  -F "text=Hello world" \
  -o output.wav

# Voice cloning
curl -X POST http://localhost:7862/api/tts \
  -F "text=Cloned voice speaking" \
  -F "reference_audio=@voice.wav" \
  -F "reference_text=Original text" \
  -o cloned.wav

# With emotions
curl -X POST http://localhost:7862/api/tts \
  -F "text=(laughing) Ha,ha,ha! (excited) Amazing!" \
  -o emotional.wav
```

### MCP (Model Context Protocol)

```python
# Generate speech programmatically
result = await mcp_client.call_tool(
    "generate_speech",
    {
        "text": "Hello from MCP!",
        "output_path": "/tmp/output.wav",
        "temperature": 0.8
    }
)

# Check GPU status
status = await mcp_client.call_tool("get_gpu_status", {})

# Free GPU memory
await mcp_client.call_tool("offload_gpu", {})
```

## 🎭 Emotion & Tone Control

### Basic Emotions
```
(angry) (sad) (excited) (surprised) (joyful) (confident)
(scared) (worried) (nervous) (frustrated) (empathetic)
```

### Tone Markers
```
(whispering) (shouting) (screaming) (soft tone) (in a hurry tone)
```

### Special Effects
```
(laughing) Ha,ha,ha
(chuckling) Hmm,hmm
(sighing) (crying loudly) (panting)
```

### Example
```
(excited) This is incredible! (laughing) Ha,ha,ha! 
(whispering) But keep it secret.
```

## ⚙️ Configuration

Edit `.env` file:

```bash
# Service
PORT=7862

# GPU (auto-selects least used)
NVIDIA_VISIBLE_DEVICES=auto
GPU_IDLE_TIMEOUT=60

# Performance
COMPILE=0  # 1 for faster (longer startup)
HALF=0     # 1 for less memory

# Model
LLAMA_CHECKPOINT_PATH=checkpoints/openaudio-s1-mini
DECODER_CHECKPOINT_PATH=checkpoints/openaudio-s1-mini/codec.pth
```

## 🔧 Management

```bash
# View logs
docker-compose logs -f

# Restart
docker-compose restart

# Stop
docker-compose down

# Rebuild
docker-compose build --no-cache
docker-compose up -d

# Test deployment
./test_deployment.sh
```

## 📊 GPU Management

### Automatic
- Model auto-offloads after `GPU_IDLE_TIMEOUT` seconds
- Frees memory for other tasks
- Reloads automatically on next request

### Manual
```bash
# Check status
curl http://localhost:7862/api/gpu/status

# Force offload
curl -X POST http://localhost:7862/api/gpu/offload
```

## 🐛 Troubleshooting

### Port in Use
```bash
# Script auto-finds available port
./start.sh
```

### Out of Memory
```bash
# Enable half precision
echo "HALF=1" >> .env
docker-compose restart
```

### Slow Generation
```bash
# Enable compilation
echo "COMPILE=1" >> .env
docker-compose restart
```

### Check Logs
```bash
docker-compose logs -f
```

## 📈 Performance Tips

| Goal | Configuration |
|------|---------------|
| **Best Quality** | `COMPILE=1 HALF=0 temperature=0.8` |
| **Best Speed** | `COMPILE=1 HALF=1 chunk_length=200` |
| **Low Memory** | `HALF=1 GPU_IDLE_TIMEOUT=30` |

## 🔒 Security

### API Authentication
```bash
# Set in .env
API_KEY=your-secret-key

# Use in requests
curl -H "Authorization: Bearer your-secret-key" \
  http://localhost:7862/api/tts -F "text=Hello"
```

### Network Restriction
```yaml
# In docker-compose.yml
ports:
  - "127.0.0.1:7862:7862"  # Localhost only
```

## 📦 What's Deployed

```
fish-speech/
├── unified_server.py      # Main server (UI + API)
├── gpu_manager.py         # GPU auto-management
├── mcp_server.py          # MCP protocol server
├── Dockerfile.unified     # Docker image
├── docker-compose.yml     # Container orchestration
├── start.sh              # One-click startup
├── test_deployment.sh    # Automated testing
├── .env.example          # Configuration template
├── DEPLOYMENT.md         # Full guide
├── MCP_GUIDE.md          # MCP documentation
├── QUICKSTART.md         # Quick reference
└── CHECKLIST.md          # Deployment checklist
```

## 🎯 Architecture

```
┌─────────────────────────────────────────────┐
│         GPU Resource Manager (Shared)        │
│  - Auto-offload after idle timeout          │
│  - Manual offload on demand                 │
│  - Status monitoring                        │
└─────────────────────────────────────────────┘
         ↓              ↓              ↓
    ┌────────┐    ┌────────┐    ┌────────┐
    │   UI   │    │  API   │    │  MCP   │
    │  Web   │    │  REST  │    │  Tool  │
    │ :7862  │    │ :7862  │    │ Stdio  │
    └────────┘    └────────┘    └────────┘
```

## 🌟 Features

### OpenAudio S1 Capabilities
- 🏆 #1 on TTS-Arena2 leaderboard
- 🎯 0.008 WER, 0.004 CER (best in class)
- 🌍 13 languages supported
- 🎭 Rich emotion and tone control
- 🎤 Zero-shot voice cloning
- ⚡ Fast inference with compilation
- 💰 Most affordable ($15/million bytes)

### Deployment Features
- 🐳 Docker containerized
- 🎮 GPU auto-selection
- 🔄 Auto-offload on idle
- 📊 Real-time monitoring
- 🔌 Three access modes
- 📚 Complete documentation
- ✅ Production-ready
- 🧪 Automated testing

## 📞 Support

- **GitHub:** https://github.com/fishaudio/fish-speech
- **Discord:** https://discord.gg/Es5qTB9BcN
- **Docs:** https://speech.fish.audio
- **Issues:** https://github.com/fishaudio/fish-speech/issues

## 📄 License

- **Code:** Apache License 2.0
- **Models:** CC-BY-NC-SA-4.0

See [LICENSE](LICENSE) for details.

## 🙏 Credits

Built on [Fish Speech](https://github.com/fishaudio/fish-speech) by Fish Audio.

---

**Ready to start?** Run `./start.sh` and visit http://localhost:7862 🚀
