# Fish Speech - 話者管理機能付き高度なテキスト読み上げシステム

[English](README.md) | [简体中文](README_CN.md) | [繁體中文](README_TW.md) | [日本語](README_JP.md)

[![Docker Pulls](https://img.shields.io/docker/pulls/neosun/fish-speech)](https://hub.docker.com/r/neosun/fish-speech)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.2.0-green.svg)](https://github.com/neosun100/fish-speech/releases)

> 🐟 話者管理、自動文字起こし、感情制御機能を備えた高度な多言語テキスト読み上げシステム

## ✨ 機能

- 🎤 **話者管理** - 音声プロファイルの登録と再利用
- 🔄 **自動文字起こし** - Whisper Turboによる参照テキストの自動生成
- 🌍 **多言語対応** - 8言語以上をサポート（日、英、中、韓、仏、独、アラビア、スペイン）
- 😊 **感情制御** - 40種類以上の感情とトーンマーカー
- ⚡ **GPU高速化** - CUDAによる高速推論
- 🐳 **Docker対応** - ワンコマンドでデプロイ
- 📡 **REST API** - FastAPI + Swagger完全ドキュメント
- 🎨 **Web UI** - ユーザーフレンドリーなGradioインターフェース

## 🚀 クイックスタート

### 方法1：Docker（推奨）

```bash
docker run -d \
  --name fish-speech \
  --gpus all \
  -p 7864:7864 \
  -v $(pwd)/checkpoints:/app/checkpoints \
  -v $(pwd)/speakers:/app/speakers \
  neosun/fish-speech:all-in-one-v1.2.0
```

アクセス：
- Web UI：http://localhost:7864
- APIドキュメント：http://localhost:7864/docs

### 方法2：ソースから実行

```bash
# リポジトリをクローン
git clone https://github.com/neosun100/fish-speech.git
cd fish-speech

# 依存関係をインストール
pip install -r requirements.txt

# モデルをダウンロード
# checkpoints/openaudio-s1-mini/ にモデルを配置

# サーバーを起動
python unified_server.py --port 7864 --device cuda
```

## 📦 インストール

### 前提条件

- Python 3.10+
- CUDA 11.8+（GPU高速化用）
- Docker 20.10+（Dockerデプロイ用）
- 8GB以上のGPUメモリ推奨

### Dockerデプロイ

```bash
docker pull neosun/fish-speech:all-in-one-v1.2.0

docker run -d \
  --name fish-speech-v1.2.0 \
  --gpus '"device=0"' \
  -p 7864:7864 \
  -e PORT=7864 \
  -v $(pwd)/checkpoints:/app/checkpoints \
  -v $(pwd)/speakers:/app/speakers \
  neosun/fish-speech:all-in-one-v1.2.0
```

## 💡 使用例

### 1. 話者を登録

```bash
curl -X POST "http://localhost:7864/api/speakers" \
  -F "name=Alice" \
  -F "description=プロフェッショナルな女性の声" \
  -F "audio=@reference.wav"
```

### 2. 話者を使用して音声を生成

```bash
curl -X POST "http://localhost:7864/api/tts/speaker/{speaker_id}" \
  -F "text=こんにちは、これはテストです。" \
  -o output.wav
```

### 3. 感情付き音声合成

```bash
curl -X POST "http://localhost:7864/api/tts" \
  -F "text=(excited) すごい！(laughing) はははは！" \
  -F "reference_audio=@voice.wav" \
  -o emotional_speech.wav
```

## 📡 APIドキュメント

完全なAPIドキュメント：http://localhost:7864/docs

## 🤝 貢献

貢献を歓迎します！以下の手順に従ってください：

1. リポジトリをフォーク
2. 機能ブランチを作成（`git checkout -b feature/AmazingFeature`）
3. 変更をコミット（`git commit -m 'Add AmazingFeature'`）
4. ブランチにプッシュ（`git push origin feature/AmazingFeature`）
5. プルリクエストを開く

## 📝 変更履歴

### v1.2.0 (2025-12-14)
- ✨ 完全な話者管理システムを追加
- ✨ 自動文字起こし機能付き話者登録
- ✨ 永続的な話者ストレージ
- 📚 完全なAPIドキュメント

## 📄 ライセンス

このプロジェクトはApache License 2.0の下でライセンスされています。

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=neosun100/fish-speech&type=Date)](https://star-history.com/#neosun100/fish-speech)

## 📱 フォローする

![公众号](https://img.aws.xin/uPic/扫码_搜索联合传播样式-标准色版.png)

---

**Fish Speechコミュニティによって❤️で作られました**
