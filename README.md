# Multimodal RAG System

A FastAPI-based Retrieval-Augmented Generation (RAG) system that can process and search through documents, videos, and audio files.

## Features

🤖 **Multimodal Processing**: Handle documents, videos, and audio files  
📄 **Document Support**: PDF, TXT, DOCX files  
🎥 **Video Support**: MP4, AVI, MOV files  
🎵 **Audio Support**: MP3, WAV, M4A files  
🔍 **Intelligent Search**: Search across all file types  
🌐 **Web Interface**: Easy-to-use web UI  
📊 **File Management**: Track and organize uploaded files  

## Quick Start

1. **Clone and run the system:**
```bash
git clone https://github.com/Surya-KF/Multimodal-RAG.git
cd Multimodal-RAG
./start.sh
```

2. **Open your browser and go to:**
```
http://localhost:8000
```

3. **Start uploading files and searching!**

## Installation

### Option 1: Automatic Setup (Recommended)
```bash
./start.sh
```
The startup script will handle dependency installation automatically.

### Option 2: Manual Installation
```bash
# Install core dependencies
pip install fastapi uvicorn python-multipart

# Install optional dependencies for advanced features
pip install PyPDF2 python-docx moviepy librosa soundfile openai-whisper

# Start the server
python3 main.py
```

## Usage

### Web Interface
1. Open http://localhost:8000 in your browser
2. Upload files using the web interface:
   - **Documents**: PDF, TXT, DOCX
   - **Videos**: MP4, AVI, MOV
   - **Audio**: MP3, WAV, M4A
3. Search through uploaded content using natural language queries
4. View and manage uploaded files

### API Endpoints

#### Upload Files
- `POST /upload/document` - Upload documents
- `POST /upload/video` - Upload videos  
- `POST /upload/audio` - Upload audio files

#### Search and Query
- `GET /search?query=<your_query>` - Search through all files
- `GET /search?query=<query>&file_types=document,video` - Filter by file types

#### File Management
- `GET /files` - List all uploaded files
- `GET /files/{file_hash}` - Get detailed file information

### Example API Usage

```python
import requests

# Upload a document
with open('document.pdf', 'rb') as f:
    response = requests.post('http://localhost:8000/upload/document', 
                           files={'file': f})
    print(response.json())

# Search for content
response = requests.get('http://localhost:8000/search?query=machine learning')
print(response.json())
```

## System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Frontend  │    │   FastAPI Server │    │  File Storage   │
│                 │◄──►│                  │◄──►│                 │
│  Upload & Search│    │  Process & Index │    │ Documents/Video │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │  Search Engine   │
                       │                  │
                       │ Metadata & Index │
                       └──────────────────┘
```

## File Processing

### Documents
- **PDF**: Extracts text using PyPDF2
- **TXT**: Direct text processing
- **DOCX**: Extracts text using python-docx
- **Chunking**: Text is split into searchable chunks

### Videos
- **Metadata**: Duration, format information
- **Transcription**: Audio track transcription (requires Whisper)
- **Frame Extraction**: Key frames for visual analysis

### Audio
- **Metadata**: Duration, sample rate, format
- **Transcription**: Speech-to-text using Whisper
- **Audio Analysis**: Feature extraction using librosa

## Advanced Features

### Enhanced Processing (Optional Dependencies)

Install additional packages for advanced features:

```bash
# For better PDF processing
pip install PyPDF2

# For DOCX support
pip install python-docx

# For video processing
pip install moviepy opencv-python

# For audio processing
pip install librosa soundfile

# For speech-to-text
pip install openai-whisper

# For vector embeddings
pip install sentence-transformers chromadb
```

### Configuration

The system creates a `data/` directory structure:
```
data/
├── documents/     # Uploaded documents
├── videos/        # Uploaded videos
├── audio/         # Uploaded audio files
├── embeddings/    # Vector embeddings (future)
└── metadata.json  # File metadata
```

## Development

### Running Tests
```bash
python3 test_rag.py
```

### Project Structure
```
Multimodal-RAG/
├── main.py              # Core RAG system and API
├── test_rag.py          # Test suite
├── start.sh             # Startup script
├── requirements.txt     # Dependencies
├── static/
│   └── index.html       # Web interface
└── data/               # File storage (created automatically)
```

## API Documentation

When the server is running, visit:
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Troubleshooting

### Common Issues

1. **Port 8000 already in use**
   ```bash
   # Change port in main.py or kill existing process
   lsof -ti:8000 | xargs kill -9
   ```

2. **Missing dependencies**
   ```bash
   # Install minimal requirements
   pip install fastapi uvicorn python-multipart
   ```

3. **File upload errors**
   - Check file size limits
   - Verify file format support
   - Ensure sufficient disk space

### Performance Tips

- **Large files**: Consider chunking for large video/audio files
- **Memory usage**: Monitor RAM usage with many uploaded files
- **Search speed**: Index optimization for large document collections

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is open source. See LICENSE file for details.

## Future Enhancements

- [ ] Vector embeddings for semantic search
- [ ] Real-time transcription
- [ ] Multiple language support
- [ ] Cloud storage integration
- [ ] Advanced video analysis
- [ ] Audio feature extraction
- [ ] Batch processing
- [ ] User authentication
- [ ] RESTful API versioning
- [ ] Docker containerization