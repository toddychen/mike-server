# Mike Server

A clean and simple audio-to-text conversion server using **local Whisper models** - no network connection or API keys required.

## Features

- 🎵 Support for multiple audio formats (mp3, mp4, mpeg, mpga, m4a, wav, webm)
- 🤖 Local Whisper models for completely offline operation
- 🔄 Multiple model options (tiny, base, small, medium, large)
- 📱 Mobile-friendly API design
- 🧹 Automatic file cleanup
- 📚 Auto-generated API documentation

## Tech Stack

- **FastAPI** - Modern, fast web framework
- **OpenAI Whisper** - Local audio-to-text models
- **PyTorch** - Deep learning framework
- **Uvicorn** - ASGI server
- **Python 3.8+**

## Prerequisites

### **FFmpeg Installation (Required)**

Whisper requires FFmpeg to process various audio formats. You must install FFmpeg before running the server.

#### **macOS (using Homebrew)**
```bash
brew install ffmpeg
```

#### **Ubuntu/Debian**
```bash
sudo apt update
sudo apt install ffmpeg
```

#### **Windows**
Download from [FFmpeg official website](https://ffmpeg.org/download.html) or use Chocolatey:
```bash
choco install ffmpeg
```

#### **Verify Installation**
```bash
ffmpeg -version
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: The first run will automatically download Whisper models, which may take some time.

### 2. Configure Environment Variables

Copy `env.example` to `.env` and fill in your configuration:

```bash
cp env.example .env
```

Edit the `.env` file:
```env
WHISPER_MODEL=base
PORT=3000
MAX_FILE_SIZE=10485760
```

### 3. Start the Server

```bash
python run.py
```

Or use uvicorn directly:
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 3000
```

### 4. Access the API

- Server: http://localhost:3000
- API Documentation: http://localhost:3000/docs
- Health Check: http://localhost:3000/health

## API Endpoints

### POST /api/audio/transcribe
Upload an audio file and convert it to text

**Request:**
- Content-Type: multipart/form-data
- Parameter: audio_file (audio file)

**Response:**
```json
{
  "success": true,
  "transcription": "Converted text content",
  "filename": "filename",
  "file_size": file_size,
  "model": "model_name_used"
}
```

### GET /api/audio/supported-formats
Get supported audio formats

### GET /api/audio/models
Get available Whisper model information

### POST /api/audio/change-model/{model_name}
Switch Whisper models

## Whisper Model Comparison

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| tiny | 39MB | Fastest | Lower | Quick testing |
| base | 74MB | Fast | Medium | Daily use |
| small | 244MB | Medium | Good | Balanced choice |
| medium | 769MB | Slower | High | High quality needs |
| large | 1550MB | Slowest | Highest | Professional use |

## Project Structure

```
mike-server/
├── src/
│   ├── main.py              # FastAPI main application
│   ├── routes/
│   │   └── audio.py         # Audio processing routes
│   └── services/
│       └── whisper_service.py # Local Whisper service
├── requirements.txt          # Python dependencies
├── env.example              # Environment variables example
├── run.py                   # Startup script
└── README.md
```

## Development

### Development Mode
The server runs in development mode by default with hot reload support.

### Environment Variables
- `WHISPER_MODEL`: Whisper model name (default: base)
- `PORT`: Server port (default: 3000)
- `MAX_FILE_SIZE`: Maximum file size in bytes (default: 10MB)

### Model Download
On first run, Whisper will automatically download the specified model to the `~/.cache/whisper/` directory.

## Troubleshooting

### **FFmpeg Not Found Error**
If you see `[Errno 2] No such file or directory: 'ffmpeg'`:
1. Install FFmpeg using the instructions above
2. Verify installation with `ffmpeg -version`
3. Restart the server

### **Audio Processing Issues**
- Ensure your audio file is in a supported format
- Check that the file is not corrupted
- Verify FFmpeg is properly installed

## License

MIT License
