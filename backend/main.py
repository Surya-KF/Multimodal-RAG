from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
from datetime import datetime
from typing import List, Optional
import aiofiles
import json
from pathlib import Path

from .models import QueryRequest, QueryResponse, UploadResponse
from .services.document_processor import DocumentProcessor
from .services.vector_store import VectorStore
from .services.llm_service import LLMService
from .middleware.logging_middleware import LoggingMiddleware
from .config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Multimodal RAG Chatbot API",
    description="FastAPI backend for multimodal RAG chatbot supporting PDF, audio, and video",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom logging middleware
app.add_middleware(LoggingMiddleware)

# Initialize services
settings = get_settings()
document_processor = DocumentProcessor()
vector_store = VectorStore()
llm_service = LLMService()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Multimodal RAG Chatbot API")
    
    # Ensure directories exist
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    os.makedirs("vector_db", exist_ok=True)
    
    # Initialize vector store
    await vector_store.initialize()
    logger.info("Vector store initialized")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Multimodal RAG Chatbot API is running", "timestamp": datetime.now().isoformat()}

@app.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload and process files (PDF, audio, video)"""
    try:
        # Validate file type
        allowed_types = [
            "application/pdf",
            "audio/wav", "audio/mp3", "audio/mpeg", "audio/ogg",
            "video/mp4", "video/avi", "video/mov", "video/mkv"
        ]
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file.content_type}"
            )
        
        # Check file size
        max_size = settings.max_file_size_mb * 1024 * 1024  # Convert MB to bytes
        file_size = 0
        
        # Save file
        file_path = f"uploads/{file.filename}"
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            file_size = len(content)
            
            if file_size > max_size:
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB"
                )
            
            await f.write(content)
        
        logger.info(f"File uploaded: {file.filename}, size: {file_size} bytes")
        
        # Process the file
        processed_content = await document_processor.process_file(file_path, file.content_type)
        
        # Store in vector database
        document_id = await vector_store.add_document(
            content=processed_content,
            metadata={
                "filename": file.filename,
                "file_type": file.content_type,
                "file_size": file_size,
                "upload_time": datetime.now().isoformat()
            }
        )
        
        logger.info(f"Document processed and stored with ID: {document_id}")
        
        return UploadResponse(
            success=True,
            document_id=document_id,
            filename=file.filename,
            file_type=file.content_type,
            processed_content_length=len(processed_content)
        )
        
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Query the RAG system with user input"""
    try:
        logger.info(f"Received query: {request.query[:100]}...")
        
        # Retrieve relevant documents
        relevant_docs = await vector_store.search(
            query=request.query,
            limit=request.max_results or 5
        )
        
        if not relevant_docs:
            return QueryResponse(
                query=request.query,
                answer="I couldn't find any relevant information in the uploaded documents to answer your question.",
                sources=[],
                confidence_score=0.0
            )
        
        # Generate answer using LLM
        answer, confidence = await llm_service.generate_answer(
            query=request.query,
            context_docs=relevant_docs
        )
        
        # Format sources
        sources = [
            {
                "content": doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"],
                "metadata": {
                    "title": doc["metadata"].get("title", doc["metadata"].get("filename", "Unknown Document")),
                    "filename": doc["metadata"].get("filename", "Unknown File"),
                    "file_type": doc["metadata"].get("file_type", "Unknown"),
                    "chunk_index": doc["metadata"].get("chunk_index", 0),
                    "document_id": doc["metadata"].get("document_id", "unknown")
                },
                "relevance_score": doc["score"]
            }
            for doc in relevant_docs
        ]
        
        logger.info(f"Generated answer with confidence: {confidence}")
        
        return QueryResponse(
            query=request.query,
            answer=answer,
            sources=sources,
            confidence_score=confidence
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents")
async def list_documents():
    """List all uploaded documents"""
    try:
        documents = await vector_store.list_documents()
        return {"documents": documents}
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a specific document"""
    try:
        logger.info(f"Attempting to delete document: {document_id}")
        
        # First, try to find the document in the vector store
        vector_store.delete_document(document_id)
        
        # Delete file from uploads directory - try multiple filename patterns
        uploads_dir = Path("uploads")
        deleted = False
        
        # Try exact filename match first
        file_path = uploads_dir / document_id
        if file_path.exists():
            file_path.unlink()
            deleted = True
            logger.info(f"Deleted file: {file_path}")
        else:
            # Try to find files that contain the document_id
            for file_path in uploads_dir.glob("*"):
                if file_path.is_file() and (file_path.name == document_id or file_path.stem == document_id):
                    file_path.unlink()
                    deleted = True
                    logger.info(f"Deleted file: {file_path}")
                    break
        
        if not deleted:
            logger.warning(f"No file found to delete for document_id: {document_id}")
        
        logger.info(f"Document {document_id} deletion completed")
        return {"message": f"Document {document_id} deleted successfully"}
    
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

@app.delete("/documents")
async def clear_all_documents():
    """Clear all uploaded documents and reset vector store"""
    try:
        # Clear all files from uploads directory
        uploads_dir = Path("uploads")
        if uploads_dir.exists():
            for file_path in uploads_dir.glob("*"):
                if file_path.is_file():
                    file_path.unlink()
        
        # Reset the vector store
        vector_store.reset()
        
        logger.info("All documents cleared successfully")
        return {"message": "All documents cleared successfully"}
    
    except Exception as e:
        logger.error(f"Error clearing all documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error clearing documents: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
