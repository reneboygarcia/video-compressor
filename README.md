<p align="center">
    <img src="image/banner.webp" alt="Banner">
</p>

# Video Compression Tool

An efficient video compression tool powered by FFmpeg, supporting multiple quality presets and custom resolutions.

## 🚀 Quick Links

- [Simple Guide for Beginners (Google Colab)](COLAB_GUIDE.md)
- [Video Compressor Notebook](video_compressor.ipynb)

## ✨ Features

- 📦 Compress videos while maintaining good quality
- 🎯 Multiple quality presets (1080p to 240p)
- 📐 Smart aspect ratio maintenance
- 🔧 Custom resolution support
- 🎬 Compatible with common video formats
- ☁️ Run locally or in Google Colab

## 🛠️ Technical Details

### Supported Features

- **Resolution Presets:**
  - 1080p (1920×1080)
  - 720p (1280×720)
  - 480p (854×480)
  - 360p (640×360)
  - 240p (426×240)

- **Video Settings:**
  - Codec: H.264
  - Audio: AAC (128k)
  - Smart bitrate selection
  - Aspect ratio preservation

### Requirements

- Python 3.6+
- FFmpeg
- Required Python packages:
  - ffmpeg-python
  - numpy

## 💻 Local Installation

1. Clone the repository:
```bash
git clone https://github.com/reneboygarcia/video-compressor.git
cd video-compressor
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## 📖 Usage Examples

### Python Script
```python
from video_compressor import TelegramVideoCompressor

compressor = TelegramVideoCompressor()

# Compress to 720p
compressor.compress_video(
    input_path="input_video.mp4",
    output_path="compressed_video.mp4",
    target_resolution="720p"
)
```
