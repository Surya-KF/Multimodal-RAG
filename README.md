# Multimodal RAG Chatbot

A powerful multimodal Retrieval-Augmented Generation (RAG) chatbot that processes PDFs, audio, and video files to provide intelligent, context-aware responses with proper source citations.

## 🚀 Features

- **Multimodal Input Support**: Upload and process PDF documents, audio files, and video files
- **Advanced Text Processing**: Extract text from PDFs using PyMuPDF (fitz)
- **Audio Transcription**: Multi-lingual speech-to-text using Vosk
- **Video Processing**: Extract audio from videos and transcribe to text
- **Semantic Search**: Vector-based similarity search using ChromaDB
- **AI-Powered Responses**: Context-grounded answers using Gemini-2.5-Flash
- **Source Citations**: All responses include proper references to source documents
- **Real-time Chat Interface**: Interactive Streamlit frontend
- **RESTful API**: FastAPI backend with comprehensive logging
- **Containerized Deployment**: Full Docker support for production environments

## 🛠️ Tech Stack

### Backend
- **FastAPI**: High-performance API framework
- **Python 3.11**: Latest stable Python version
- **ChromaDB**: Vector database for semantic search
- **Vosk**: Open-source speech recognition
- **PyMuPDF (fitz)**: PDF text extraction
- **MoviePy**: Video processing
- **Google Generative AI**: Gemini-2.5-Flash integration

### Frontend
- **Streamlit**: Interactive web application framework
- **Responsive UI**: File upload, chat interface, and source display

### Infrastructure
- **UV**: Universal virtualenv for dependency management
- **Docker**: Containerization for consistent deployments
- **Docker Compose**: Multi-service orchestration

## 📋 Prerequisites

- Python 3.11+
- UV (Universal Virtualenv)
- Docker and Docker Compose (for containerized deployment)
- Git

## 🚀 Quick Start

### Option 1: Docker Deployment (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd TASK1

# Start with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f
```

### Option 2: Manual Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd TASK1

# Install UV (if not already installed)
pip install uv

# Create virtual environment and install dependencies
uv sync

# Activate environment
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Start backend (Terminal 1)
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Start frontend (Terminal 2)
uv run streamlit run frontend/app.py --server.port 8501
```

### Option 3: Direct Python Execution

```bash
# Install dependencies
pip install -r requirements.txt

# Start backend
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Start frontend (in separate terminal)
streamlit run frontend/app.py --server.port 8501
```

## 🌐 Access Points

After successful setup:

- **Frontend (Streamlit)**: http://localhost:8501
- **Backend API (FastAPI)**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **API Redoc**: http://localhost:8000/redoc

## 📚 Usage

### 1. Upload Files
- Navigate to the Streamlit interface at http://localhost:8501
- Use the file uploader to add PDF, audio (WAV, MP3), or video (MP4, AVI) files
- Files are automatically processed and indexed for search

### 2. Chat with Your Documents
- Enter questions in the chat interface
- The system will search through your uploaded content
- Receive AI-generated responses with source citations
- View referenced document chunks for transparency

### 3. File Management
- View uploaded files in the sidebar
- Delete files when no longer needed
- Monitor processing status and file information

## 🔧 API Documentation

### Upload Endpoint
```http
POST /upload
Content-Type: multipart/form-data

Parameters:
- file: The file to upload (PDF, audio, or video)

Response:
{
    "message": "File uploaded and processed successfully",
    "filename": "document.pdf",
    "file_id": "unique-file-identifier"
}
```

### Query Endpoint
```http
POST /query
Content-Type: application/json

Body:
{
    "query": "Your question here"
}

Response:
{
    "response": "AI-generated answer",
    "sources": [
        {
            "content": "Relevant text chunk",
            "metadata": {
                "filename": "source.pdf",
                "page": 1
            }
        }
    ]
}
```

### Health Check
```http
GET /
Response: {"message": "Multimodal RAG Chatbot API"}
```

## 📁 Project Structure

```
TASK1/
├── backend/                    # FastAPI backend
│   ├── services/              # Business logic services
│   │   ├── __init__.py
│   │   ├── file_processor.py  # File processing logic
│   │   ├── vector_store.py    # ChromaDB integration
│   │   └── llm_client.py      # Gemini API integration
│   ├── __init__.py
│   ├── main.py               # FastAPI app and routes
│   └── middleware.py         # Logging and error handling
├── frontend/                 # Streamlit frontend
│   ├── __init__.py
│   └── app.py               # Main Streamlit application
├── uploads/                 # User uploaded files
├── logs/                   # Application logs
├── vector_db/             # ChromaDB storage
├── models/               # Downloaded Vosk models
├── docker-compose.yml   # Multi-service deployment
├── Dockerfile          # Container configuration
├── pyproject.toml     # UV dependencies
├── uv.lock           # Dependency lock file
└── README.md         # This file
```

## 🔍 Supported File Types

### PDFs
- Text extraction using PyMuPDF
- Maintains page references
- Handles complex layouts and formatting

### Audio Files
- **Formats**: WAV, MP3, FLAC, OGG
- **Languages**: Multi-lingual support via Vosk
- **Processing**: Automatic transcription with timestamps

### Video Files
- **Formats**: MP4, AVI, MOV, MKV
- **Processing**: Audio extraction → transcription
- **Optimization**: Efficient audio processing pipeline

## ⚙️ Configuration

### Environment Variables
Create a `.env` file in the project root:

```env
# Google Gemini API Key (required)
GOOGLE_API_KEY=your_gemini_api_key_here

# Optional configurations
MAX_FILE_SIZE=100MB
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
VOSK_MODEL_SIZE=small  # small, large
LOG_LEVEL=INFO
```

### Model Configuration
- **Vosk Models**: Automatically downloaded on first use
- **Embedding Model**: Uses ChromaDB default embeddings
- **LLM Model**: Gemini-2.5-Flash (configurable in llm_client.py)

## 🐛 Troubleshooting

### Common Issues

#### 1. Vosk Model Download Fails
```bash
# Manual model download
mkdir -p models
cd models
wget https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip
unzip vosk-model-en-us-0.22.zip
```

#### 2. FFmpeg Not Found
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

#### 3. Port Already in Use
```bash
# Check what's using the port
netstat -an | findstr :8000  # Windows
lsof -i :8000               # Linux/Mac

# Use different ports
uvicorn backend.main:app --port 8001
streamlit run frontend/app.py --server.port 8502
```

#### 4. Memory Issues with Large Files
- Reduce chunk size in vector_store.py
- Use smaller Vosk models
- Increase Docker memory limits

#### 5. Docker Build Issues
```bash
# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache
```

### Logs and Debugging

```bash
# View application logs
tail -f logs/app.log

# Docker logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Enable debug mode
export LOG_LEVEL=DEBUG
```

## 🚀 Production Deployment

### Docker Production Setup
```bash
# Production environment variables
cp .env.example .env
# Edit .env with your production values

# Start in production mode
docker-compose -f docker-compose.prod.yml up -d

# Monitor services
docker-compose ps
docker-compose logs -f
```

### Performance Optimization
- Use production ASGI server (Gunicorn + Uvicorn workers)
- Configure resource limits in Docker Compose
- Set up reverse proxy (Nginx) for load balancing
- Configure persistent volumes for data storage

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Commit with clear messages: `git commit -m "Add feature description"`
5. Push to your branch: `git push origin feature-name`
6. Submit a pull request



## 🙏 Acknowledgments

- [Vosk](https://alphacephei.com/vosk/) for open-source speech recognition
- [ChromaDB](https://www.trychroma.com/) for vector database
- [Streamlit](https://streamlit.io/) for the web framework
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [Google Gemini](https://ai.google.dev/) for language model integration
---

