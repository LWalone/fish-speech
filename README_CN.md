# Fish Speech - 高级文本转语音系统（支持说话人管理）

[English](README.md) | [简体中文](README_CN.md) | [繁體中文](README_TW.md) | [日本語](README_JP.md)

[![Docker Pulls](https://img.shields.io/docker/pulls/neosun/fish-speech)](https://hub.docker.com/r/neosun/fish-speech)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.2.0-green.svg)](https://github.com/neosun100/fish-speech/releases)

> 🐟 支持说话人管理、自动转录和情感控制的高级多语言文本转语音系统

## ✨ 功能特性

- 🎤 **说话人管理** - 注册并重复使用语音配置文件
- 🔄 **自动转录** - 使用 Whisper Turbo 自动生成参考文本
- 🌍 **多语言支持** - 支持 8+ 种语言（中、英、日、韩、法、德、阿、西）
- 😊 **情感控制** - 40+ 种情感和语气标记
- ⚡ **GPU 加速** - 支持 CUDA 快速推理
- 🐳 **Docker 就绪** - 一键部署
- 📡 **REST API** - 完整的 FastAPI + Swagger 文档
- 🎨 **Web 界面** - 用户友好的 Gradio 界面

## 🚀 快速开始

### 方式一：Docker（推荐）

```bash
docker run -d \
  --name fish-speech \
  --gpus all \
  -p 7864:7864 \
  -v $(pwd)/checkpoints:/app/checkpoints \
  -v $(pwd)/speakers:/app/speakers \
  neosun/fish-speech:all-in-one-v1.2.0
```

访问地址：
- Web 界面：http://localhost:7864
- API 文档：http://localhost:7864/docs

### 方式二：从源码运行

```bash
# 克隆仓库
git clone https://github.com/neosun100/fish-speech.git
cd fish-speech

# 安装依赖
pip install -r requirements.txt

# 下载模型
# 将模型放置在 checkpoints/openaudio-s1-mini/ 目录

# 运行服务器
python unified_server.py --port 7864 --device cuda
```

## 📦 安装部署

### 环境要求

- Python 3.10+
- CUDA 11.8+（GPU 加速）
- Docker 20.10+（Docker 部署）
- 推荐 8GB+ GPU 显存

### Docker 部署

#### 拉取镜像

```bash
docker pull neosun/fish-speech:all-in-one-v1.2.0
```

#### 运行容器

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

运行：`docker-compose up -d`

## ⚙️ 配置说明

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PORT` | 7862 | 服务器端口 |
| `DEVICE` | cuda | 设备（cuda/cpu）|
| `COMPILE` | 0 | 启用 torch 编译 |
| `HALF` | 0 | 使用半精度 |
| `LLAMA_CHECKPOINT_PATH` | checkpoints/openaudio-s1-mini | 模型路径 |

### 数据卷挂载

- `/app/checkpoints` - 模型文件（必需）
- `/app/speakers` - 说话人配置文件（持久化存储）

## 💡 使用示例

### 1. 注册说话人

```bash
curl -X POST "http://localhost:7864/api/speakers" \
  -F "name=小美" \
  -F "description=专业女声" \
  -F "audio=@reference.wav"
```

### 2. 使用说话人生成语音

```bash
curl -X POST "http://localhost:7864/api/tts/speaker/{speaker_id}" \
  -F "text=你好，这是一个测试。" \
  -o output.wav
```

### 3. 带情感的语音合成

```bash
curl -X POST "http://localhost:7864/api/tts" \
  -F "text=(excited) 太棒了！(laughing) 哈哈哈！" \
  -F "reference_audio=@voice.wav" \
  -o emotional_speech.wav
```

### 4. 自动转录

```bash
curl -X POST "http://localhost:7864/api/transcribe" \
  -F "audio=@audio.wav"
```

## 📡 API 文档

### 接口列表

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/api/gpu/status` | GPU 状态 |
| POST | `/api/transcribe` | 转录音频 |
| GET | `/api/speakers` | 列出说话人 |
| POST | `/api/speakers` | 注册说话人 |
| GET | `/api/speakers/{id}` | 获取说话人 |
| PUT | `/api/speakers/{id}` | 更新说话人 |
| DELETE | `/api/speakers/{id}` | 删除说话人 |
| POST | `/api/tts` | 生成语音 |
| POST | `/api/tts/speaker/{id}` | 使用说话人生成语音 |

完整 API 文档：http://localhost:7864/docs

## 🏗️ 项目结构

```
fish-speech/
├── unified_server.py      # 主服务器
├── gpu_manager.py          # GPU 管理
├── fish_speech/            # 核心 TTS 引擎
├── tools/                  # 工具集
├── checkpoints/            # 模型文件
├── speakers/               # 说话人配置
├── Dockerfile.allinone     # Docker 构建
└── docs/                   # 文档
```

## 🛠️ 技术栈

- **框架**：FastAPI + Gradio
- **模型**：OpenAudio S1-mini（0.5B 参数）
- **转录**：Whisper Turbo
- **推理**：PyTorch + CUDA
- **部署**：Docker + NVIDIA Container Toolkit

## 🤝 贡献指南

欢迎贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支（`git checkout -b feature/AmazingFeature`）
3. 提交更改（`git commit -m 'Add AmazingFeature'`）
4. 推送到分支（`git push origin feature/AmazingFeature`）
5. 开启 Pull Request

## 📝 更新日志

### v1.2.0 (2025-12-14)
- ✨ 添加完整的说话人管理系统
- ✨ 支持说话人注册和自动转录
- ✨ 持久化说话人存储
- 📚 完整的 API 文档

### v1.1.3 (2025-12-14)
- 🐛 修复 Gradio 自动转录 bug
- 🔧 改进音频文件处理

### v1.1.2 (2025-12-14)
- ✨ 集成 Whisper Turbo
- ✨ 添加转录 API

[完整更新日志](RELEASE_v1.2.0.md)

## 📄 许可证

本项目采用 Apache License 2.0 许可证 - 详见 [LICENSE](LICENSE) 文件。

模型权重采用 CC-BY-NC-SA-4.0 许可证发布。

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=neosun100/fish-speech&type=Date)](https://star-history.com/#neosun100/fish-speech)

## 📱 关注公众号

![公众号](https://img.aws.xin/uPic/扫码_搜索联合传播样式-标准色版.png)

---

**用 ❤️ 打造 by Fish Speech 社区**
