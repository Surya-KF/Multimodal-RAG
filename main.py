import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any
import json
import hashlib
import base64

# Simple HTTP server as fallback if FastAPI isn't available
try:
    from fastapi import FastAPI, File, UploadFile, HTTPException, Form
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

class MultimodalRAG:
    """Multimodal RAG system that processes documents, videos, and audio files."""
    
    def __init__(self, storage_dir: str = "./data"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for different file types
        self.doc_dir = self.storage_dir / "documents"
        self.video_dir = self.storage_dir / "videos"
        self.audio_dir = self.storage_dir / "audio"
        self.embeddings_dir = self.storage_dir / "embeddings"
        
        for dir_path in [self.doc_dir, self.video_dir, self.audio_dir, self.embeddings_dir]:
            dir_path.mkdir(exist_ok=True)
            
        # Metadata storage
        self.metadata_file = self.storage_dir / "metadata.json"
        self.metadata = self._load_metadata()
        
    def _load_metadata(self) -> Dict[str, Any]:
        """Load metadata from JSON file."""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_metadata(self):
        """Save metadata to JSON file."""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def _get_file_hash(self, file_content: bytes) -> str:
        """Generate hash for file content."""
        return hashlib.md5(file_content).hexdigest()
    
    def process_document(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Process document file (PDF, TXT, DOCX)."""
        file_hash = self._get_file_hash(file_content)
        file_ext = Path(filename).suffix.lower()
        
        # Save file
        saved_path = self.doc_dir / f"{file_hash}{file_ext}"
        with open(saved_path, 'wb') as f:
            f.write(file_content)
        
        # Extract text based on file type
        text_content = ""
        if file_ext == '.txt':
            text_content = file_content.decode('utf-8', errors='ignore')
        elif file_ext == '.pdf':
            text_content = self._extract_pdf_text(file_content)
        elif file_ext in ['.docx', '.doc']:
            text_content = self._extract_docx_text(file_content)
        else:
            text_content = f"Unsupported document type: {file_ext}"
        
        # Store metadata
        metadata = {
            'filename': filename,
            'file_type': 'document',
            'file_extension': file_ext,
            'file_hash': file_hash,
            'file_path': str(saved_path),
            'text_content': text_content[:1000],  # Store first 1000 chars
            'full_text_length': len(text_content),
            'chunks': self._chunk_text(text_content)
        }
        
        self.metadata[file_hash] = metadata
        self._save_metadata()
        
        return {
            'file_hash': file_hash,
            'status': 'processed',
            'type': 'document',
            'text_preview': text_content[:200],
            'chunks_count': len(metadata['chunks'])
        }
    
    def process_video(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Process video file (MP4, AVI, MOV)."""
        file_hash = self._get_file_hash(file_content)
        file_ext = Path(filename).suffix.lower()
        
        # Save file
        saved_path = self.video_dir / f"{file_hash}{file_ext}"
        with open(saved_path, 'wb') as f:
            f.write(file_content)
        
        # Extract video metadata and transcription
        video_info = self._extract_video_info(saved_path)
        
        metadata = {
            'filename': filename,
            'file_type': 'video',
            'file_extension': file_ext,
            'file_hash': file_hash,
            'file_path': str(saved_path),
            'duration': video_info.get('duration', 0),
            'transcription': video_info.get('transcription', 'Transcription not available'),
            'frames_extracted': video_info.get('frames_count', 0)
        }
        
        self.metadata[file_hash] = metadata
        self._save_metadata()
        
        return {
            'file_hash': file_hash,
            'status': 'processed',
            'type': 'video',
            'duration': metadata['duration'],
            'transcription_preview': metadata['transcription'][:200]
        }
    
    def process_audio(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Process audio file (MP3, WAV, M4A)."""
        file_hash = self._get_file_hash(file_content)
        file_ext = Path(filename).suffix.lower()
        
        # Save file
        saved_path = self.audio_dir / f"{file_hash}{file_ext}"
        with open(saved_path, 'wb') as f:
            f.write(file_content)
        
        # Extract audio transcription
        audio_info = self._extract_audio_info(saved_path)
        
        metadata = {
            'filename': filename,
            'file_type': 'audio',
            'file_extension': file_ext,
            'file_hash': file_hash,
            'file_path': str(saved_path),
            'duration': audio_info.get('duration', 0),
            'transcription': audio_info.get('transcription', 'Transcription not available'),
            'sample_rate': audio_info.get('sample_rate', 0)
        }
        
        self.metadata[file_hash] = metadata
        self._save_metadata()
        
        return {
            'file_hash': file_hash,
            'status': 'processed',
            'type': 'audio',
            'duration': metadata['duration'],
            'transcription_preview': metadata['transcription'][:200]
        }
    
    def _extract_pdf_text(self, file_content: bytes) -> str:
        """Extract text from PDF file."""
        try:
            # Try to import PyPDF2 if available
            import PyPDF2
            import io
            
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except ImportError:
            return "PDF text extraction requires PyPDF2 library"
        except Exception as e:
            return f"Error extracting PDF text: {str(e)}"
    
    def _extract_docx_text(self, file_content: bytes) -> str:
        """Extract text from DOCX file."""
        try:
            # Try to import python-docx if available
            from docx import Document
            import io
            
            doc = Document(io.BytesIO(file_content))
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except ImportError:
            return "DOCX text extraction requires python-docx library"
        except Exception as e:
            return f"Error extracting DOCX text: {str(e)}"
    
    def _extract_video_info(self, file_path: Path) -> Dict[str, Any]:
        """Extract information from video file."""
        try:
            # Try to use moviepy if available
            from moviepy.editor import VideoFileClip
            
            clip = VideoFileClip(str(file_path))
            duration = clip.duration
            
            # Extract a few frames for analysis
            frames_count = min(10, int(duration))
            
            # Simple transcription placeholder
            transcription = "Video transcription requires Whisper or similar speech-to-text service"
            
            clip.close()
            
            return {
                'duration': duration,
                'transcription': transcription,
                'frames_count': frames_count
            }
        except ImportError:
            return {
                'duration': 0,
                'transcription': 'Video processing requires moviepy library',
                'frames_count': 0
            }
        except Exception as e:
            return {
                'duration': 0,
                'transcription': f'Error processing video: {str(e)}',
                'frames_count': 0
            }
    
    def _extract_audio_info(self, file_path: Path) -> Dict[str, Any]:
        """Extract information from audio file."""
        try:
            # Try to use librosa if available
            import librosa
            
            y, sr = librosa.load(str(file_path))
            duration = librosa.get_duration(y=y, sr=sr)
            
            # Simple transcription placeholder
            transcription = "Audio transcription requires Whisper or similar speech-to-text service"
            
            return {
                'duration': duration,
                'transcription': transcription,
                'sample_rate': sr
            }
        except ImportError:
            return {
                'duration': 0,
                'transcription': 'Audio processing requires librosa library',
                'sample_rate': 0
            }
        except Exception as e:
            return {
                'duration': 0,
                'transcription': f'Error processing audio: {str(e)}',
                'sample_rate': 0
            }
    
    def _chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """Split text into chunks for vector storage."""
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0
        
        for word in words:
            if current_size + len(word) > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_size = len(word)
            else:
                current_chunk.append(word)
                current_size += len(word) + 1
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def search(self, query: str, file_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Search through processed files."""
        results = []
        
        for file_hash, metadata in self.metadata.items():
            if file_types and metadata['file_type'] not in file_types:
                continue
            
            # Simple keyword matching (can be enhanced with vector similarity)
            content_to_search = ""
            if metadata['file_type'] == 'document':
                content_to_search = metadata.get('text_content', '')
            else:
                content_to_search = metadata.get('transcription', '')
            
            if query.lower() in content_to_search.lower():
                results.append({
                    'file_hash': file_hash,
                    'filename': metadata['filename'],
                    'file_type': metadata['file_type'],
                    'relevance_snippet': self._get_snippet(content_to_search, query),
                    'metadata': metadata
                })
        
        return results
    
    def _get_snippet(self, text: str, query: str, context_size: int = 100) -> str:
        """Get a snippet of text around the query match."""
        lower_text = text.lower()
        lower_query = query.lower()
        
        index = lower_text.find(lower_query)
        if index == -1:
            return text[:context_size] + "..."
        
        start = max(0, index - context_size // 2)
        end = min(len(text), index + len(query) + context_size // 2)
        
        snippet = text[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."
        
        return snippet
    
    def get_file_info(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific file."""
        return self.metadata.get(file_hash)
    
    def list_files(self) -> List[Dict[str, Any]]:
        """List all processed files."""
        return [
            {
                'file_hash': file_hash,
                'filename': metadata['filename'],
                'file_type': metadata['file_type'],
                'file_extension': metadata['file_extension']
            }
            for file_hash, metadata in self.metadata.items()
        ]

# Initialize the RAG system
rag_system = MultimodalRAG()

def create_basic_server():
    """Create a basic HTTP server if FastAPI is not available."""
    if not FASTAPI_AVAILABLE:
        # Create a simple HTTP server using built-in modules
        import http.server
        import socketserver
        import urllib.parse
        import cgi
        
        class RAGHandler(http.server.SimpleHTTPRequestHandler):
            def do_POST(self):
                if self.path == '/upload':
                    content_type = self.headers['content-type']
                    if not content_type:
                        self.send_error(400, 'Content-Type header is missing')
                        return
                    
                    # Simple file upload handling
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    
                    response = {'status': 'received', 'message': 'File upload endpoint - FastAPI not available'}
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode())
                
                elif self.path == '/search':
                    # Simple search endpoint
                    response = {'status': 'search endpoint', 'message': 'Search functionality available'}
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode())
            
            def do_GET(self):
                if self.path == '/':
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    html_content = """
                    <!DOCTYPE html>
                    <html>
                    <head><title>Multimodal RAG</title></head>
                    <body>
                        <h1>Multimodal RAG System</h1>
                        <p>Upload documents, videos, and audio files for processing.</p>
                        <p>Note: Install FastAPI for full functionality</p>
                    </body>
                    </html>
                    """
                    self.wfile.write(html_content.encode())
                else:
                    super().do_GET()
        
        return RAGHandler, socketserver
    
    # FastAPI implementation
    app = FastAPI(title="Multimodal RAG API", description="Upload and search documents, videos, and audio files")
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse
    
    # Mount static files
    app.mount("/static", StaticFiles(directory="static"), name="static")
    
    @app.get("/")
    async def root():
        # Serve the HTML interface
        return FileResponse('static/index.html')
    
    @app.get("/api/status")
    async def api_status():
        return {"message": "Multimodal RAG API", "status": "running"}
    
    @app.post("/upload/document")
    async def upload_document(file: UploadFile = File(...)):
        """Upload and process a document (PDF, TXT, DOCX)."""
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ['.pdf', '.txt', '.docx', '.doc']:
            raise HTTPException(status_code=400, detail="Unsupported document type")
        
        content = await file.read()
        result = rag_system.process_document(content, file.filename)
        
        return result
    
    @app.post("/upload/video")
    async def upload_video(file: UploadFile = File(...)):
        """Upload and process a video (MP4, AVI, MOV)."""
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ['.mp4', '.avi', '.mov', '.mkv']:
            raise HTTPException(status_code=400, detail="Unsupported video type")
        
        content = await file.read()
        result = rag_system.process_video(content, file.filename)
        
        return result
    
    @app.post("/upload/audio")
    async def upload_audio(file: UploadFile = File(...)):
        """Upload and process an audio file (MP3, WAV, M4A)."""
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ['.mp3', '.wav', '.m4a', '.aac', '.flac']:
            raise HTTPException(status_code=400, detail="Unsupported audio type")
        
        content = await file.read()
        result = rag_system.process_audio(content, file.filename)
        
        return result
    
    @app.get("/search")
    async def search_files(query: str, file_types: Optional[str] = None):
        """Search through processed files."""
        if not query:
            raise HTTPException(status_code=400, detail="Query parameter is required")
        
        types_list = None
        if file_types:
            types_list = [t.strip() for t in file_types.split(',')]
        
        results = rag_system.search(query, types_list)
        
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
    
    @app.get("/files")
    async def list_files():
        """List all processed files."""
        files = rag_system.list_files()
        return {
            "files": files,
            "count": len(files)
        }
    
    @app.get("/files/{file_hash}")
    async def get_file_info(file_hash: str):
        """Get detailed information about a specific file."""
        file_info = rag_system.get_file_info(file_hash)
        if not file_info:
            raise HTTPException(status_code=404, detail="File not found")
        
        return file_info
    
    return app

if __name__ == "__main__":
    if FASTAPI_AVAILABLE:
        try:
            import uvicorn
            app = create_basic_server()
            print("🚀 Starting FastAPI server on http://localhost:8000")
            uvicorn.run(app, host="0.0.0.0", port=8000)
        except ImportError:
            print("❌ uvicorn not available")
            print("📦 Install with: pip install uvicorn")
    else:
        print("FastAPI not available. Please install: pip install fastapi uvicorn")
        print("Starting basic HTTP server...")
        handler, socketserver = create_basic_server()
        with socketserver.TCPServer(("", 8000), handler) as httpd:
            print("Server running on http://localhost:8000")
            httpd.serve_forever()