# Fish Speech - 高级文本转語音系統（支援說話人管理）

[English](README.md) | [簡體中文](README_CN.md) | [繁體中文](README_TW.md) | [日本語](README_JP.md)

[![Docker Pulls](https://img.shields.io/docker/pulls/neosun/fish-speech)](https://hub.docker.com/r/neosun/fish-speech)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.2.0-green.svg)](https://github.com/neosun100/fish-speech/releases)

> 🐟 支援說話人管理、自動轉錄和情感控制的高级多語言文本转語音系統

## ✨ 功能特性

- 🎤 **說話人管理** - 註冊并重复使用語音配置檔案
- 🔄 **自動轉錄** - 使用 Whisper Turbo 自動生成参考文本
- 🌍 **多語言支援** - 支援 8+ 种語言（中、英、日、韩、法、德、阿、西）
- 😊 **情感控制** - 40+ 种情感和语气標記
- ⚡ **GPU 加速** - 支援 CUDA 快速推理
- 🐳 **Docker 就绪** - 一键部署
- 📡 **REST API** - 完整的 FastAPI + Swagger 文檔
- 🎨 **Web 介面** - 用戶友好的 Gradio 介面

## 🚀 快速開始

### 方式一：Docker（推薦）

```bash
docker run -d \
  --name fish-speech \
  --gpus all \
  -p 7864:7864 \
  -v $(pwd)/checkpoints:/app/checkpoints \
  -v $(pwd)/speakers:/app/speakers \
  neosun/fish-speech:all-in-one-v1.2.0
```

訪問地址：
- Web 介面：http://localhost:7864
- API 文檔：http://localhost:7864/docs

### 方式二：从原始碼運行

```bash
# 克隆倉庫
git clone https://github.com/neosun100/fish-speech.git
cd fish-speech

# 安裝依賴
pip install -r requirements.txt

# 下載模型
# 将模型放置在 checkpoints/openaudio-s1-mini/ 目錄

# 運行伺服器
python unified_server.py --port 7864 --device cuda
```

## 📦 安裝部署

### 環境要求

- Python 3.10+
- CUDA 11.8+（GPU 加速）
- Docker 20.10+（Docker 部署）
- 推薦 8GB+ GPU 顯存

### Docker 部署

#### 拉取鏡像

```bash
docker pull neosun/fish-speech:all-in-one-v1.2.0
```

#### 運行容器

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

#### 使用 Docker Compose

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

運行：`docker-compose up -d`

## ⚙️ 配置說明

### 環境變數

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `PORT` | 7862 | 伺服器埠 |
| `DEVICE` | cuda | 設備（cuda/cpu）|
| `COMPILE` | 0 | 啟用 torch 編譯 |
| `HALF` | 0 | 使用半精度 |
| `LLAMA_CHECKPOINT_PATH` | checkpoints/openaudio-s1-mini | 模型路徑 |

### 資料卷掛載

- `/app/checkpoints` - 模型檔案（必需）
- `/app/speakers` - 說話人配置檔案（持久化儲存）

## 💡 使用示例

### 1. 註冊說話人

```bash
curl -X POST "http://localhost:7864/api/speakers" \
  -F "name=小美" \
  -F "description=專業女聲" \
  -F "audio=@reference.wav"
```

### 2. 使用說話人生成語音

```bash
curl -X POST "http://localhost:7864/api/tts/speaker/{speaker_id}" \
  -F "text=你好，这是一个測試。" \
  -o output.wav
```

### 3. 帶情感的語音合成

```bash
curl -X POST "http://localhost:7864/api/tts" \
  -F "text=(excited) 太棒了！(laughing) 哈哈哈！" \
  -F "reference_audio=@voice.wav" \
  -o emotional_speech.wav
```

### 4. 自動轉錄

```bash
curl -X POST "http://localhost:7864/api/transcribe" \
  -F "audio=@audio.wav"
```

## 📡 API 文檔

### 介面列表

| 方法 | 端点 | 說明 |
|------|------|------|
| GET | `/health` | 健康檢查 |
| GET | `/api/gpu/status` | GPU 狀態 |
| POST | `/api/transcribe` | 轉錄音频 |
| GET | `/api/speakers` | 列出說話人 |
| POST | `/api/speakers` | 註冊說話人 |
| GET | `/api/speakers/{id}` | 獲取說話人 |
| PUT | `/api/speakers/{id}` | 更新說話人 |
| DELETE | `/api/speakers/{id}` | 刪除說話人 |
| POST | `/api/tts` | 生成語音 |
| POST | `/api/tts/speaker/{id}` | 使用說話人生成語音 |

完整 API 文檔：http://localhost:7864/docs

## 🏗️ 專案結構

```
fish-speech/
├── unified_server.py      # 主伺服器
├── gpu_manager.py          # GPU 管理
├── fish_speech/            # 核心 TTS 引擎
├── tools/                  # 工具集
├── checkpoints/            # 模型檔案
├── speakers/               # 說話人配置
├── Dockerfile.allinone     # Docker 構建
└── docs/                   # 文檔
```

## 🛠️ 技術棧

- **框架**：FastAPI + Gradio
- **模型**：OpenAudio S1-mini（0.5B 參數）
- **轉錄**：Whisper Turbo
- **推理**：PyTorch + CUDA
- **部署**：Docker + NVIDIA Container Toolkit

## 🤝 貢獻指南

歡迎貢獻！请遵循以下步驟：

1. Fork 本倉庫
2. 創建特性分支（`git checkout -b feature/AmazingFeature`）
3. 提交更改（`git commit -m 'Add AmazingFeature'`）
4. 推送到分支（`git push origin feature/AmazingFeature`）
5. 開啟 Pull Request

## 📝 更新日誌

### v1.2.0 (2025-12-14)
- ✨ 添加完整的說話人管理系統
- ✨ 支援說話人註冊和自動轉錄
- ✨ 持久化說話人儲存
- 📚 完整的 API 文檔

### v1.1.3 (2025-12-14)
- 🐛 修復 Gradio 自動轉錄 bug
- 🔧 改進音频檔案處理

### v1.1.2 (2025-12-14)
- ✨ 集成 Whisper Turbo
- ✨ 添加轉錄 API

[完整更新日誌](RELEASE_v1.2.0.md)

## 📄 許可證

本專案採用 Apache License 2.0 許可證 - 詳見 [LICENSE](LICENSE) 檔案。

模型權重採用 CC-BY-NC-SA-4.0 許可證發布。

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=neosun100/fish-speech&type=Date)](https://star-history.com/#neosun100/fish-speech)

## 📱 關注公眾號

![公眾號](https://img.aws.xin/uPic/扫码_搜索联合传播样式-标准色版.png)

---

**用 ❤️ 打造 by Fish Speech 社群**
