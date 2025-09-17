import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import uuid
import logging
from typing import List, Dict, Any, Optional
import hashlib

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.client = None
        self.collection = None
        self.collection_name = "multimodal_rag_docs"
    
    async def initialize(self):
        """Initialize ChromaDB client and collection"""
        try:
            self.client = chromadb.PersistentClient(
                path="./vector_db",
                settings=Settings(allow_reset=True)
            )
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(self.collection_name)
                logger.info(f"Loaded existing collection: {self.collection_name}")
            except:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "Multimodal RAG documents"}
                )
                logger.info(f"Created new collection: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    async def add_document(self, content: str, metadata: Dict[str, Any]) -> str:
        """Add a document to the vector store"""
        try:
            # Generate unique ID
            document_id = str(uuid.uuid4())
            
            # Split content into chunks if it's too long
            chunks = self._split_content(content)
            
            # Add each chunk to the collection
            chunk_ids = []
            chunk_metadatas = []
            chunk_documents = []
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{document_id}_chunk_{i}"
                chunk_metadata = {
                    **metadata,
                    "document_id": document_id,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    # Ensure filename is preserved in multiple formats
                    "filename": metadata.get('filename', metadata.get('source', 'Unknown')),
                    "source": metadata.get('filename', metadata.get('source', 'Unknown')),
                    "file_name": metadata.get('filename', metadata.get('source', 'Unknown'))
                }
                
                chunk_ids.append(chunk_id)
                chunk_metadatas.append(chunk_metadata)
                chunk_documents.append(chunk)
            
            self.collection.add(
                ids=chunk_ids,
                documents=chunk_documents,
                metadatas=chunk_metadatas
            )
            
            logger.info(f"Added document {document_id} with {len(chunks)} chunks")
            return document_id
            
        except Exception as e:
            logger.error(f"Error adding document to vector store: {e}")
            raise
    
    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant documents"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=limit,
                include=["documents", "metadatas", "distances"]
            )
            
            if not results['documents'] or not results['documents'][0]:
                return []
            
            # Format results
            formatted_results = []
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "score": 1.0 - results['distances'][0][i]  # Convert distance to similarity
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            raise
    
    async def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents in the vector store"""
        try:
            # Get all items from collection
            results = self.collection.get(include=["metadatas"])
            
            # Group by document_id and get unique documents
            documents = {}
            for metadata in results['metadatas']:
                doc_id = metadata.get('document_id')
                if doc_id and doc_id not in documents:
                    documents[doc_id] = {
                        "document_id": doc_id,
                        "filename": metadata.get('filename', 'Unknown'),
                        "file_type": metadata.get('file_type', 'Unknown'),
                        "upload_time": metadata.get('upload_time', 'Unknown'),
                        "total_chunks": metadata.get('total_chunks', 1)
                    }
            
            return list(documents.values())
            
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            raise
    
    # Improve delete_document method with better search
    def delete_document(self, document_id: str):
        """Delete a document from the vector store by its ID"""
        try:
            # Try multiple search patterns for the document
            search_patterns = [
                {"source": document_id},  # Exact match
            ]
            
            deleted_count = 0
            for pattern in search_patterns:
                try:
                    results = self.collection.get(where=pattern)
                    if results and results['ids']:
                        self.collection.delete(ids=results['ids'])
                        deleted_count += len(results['ids'])
                        logger.info(f"Deleted {len(results['ids'])} chunks for pattern {pattern}")
                        break  # Stop after first successful match
                except Exception as pattern_error:
                    logger.debug(f"Pattern {pattern} failed: {pattern_error}")
                    continue
            
            if deleted_count == 0:
                # Try to find any documents that might match by filename
                all_docs = self.collection.get()
                matching_ids = []
                if all_docs and all_docs['metadatas']:
                    for i, metadata in enumerate(all_docs['metadatas']):
                        if metadata and isinstance(metadata, dict):
                            source = metadata.get('source', '')
                            if document_id in source or source in document_id:
                                matching_ids.append(all_docs['ids'][i])
                
                if matching_ids:
                    self.collection.delete(ids=matching_ids)
                    deleted_count = len(matching_ids)
                    logger.info(f"Deleted {deleted_count} chunks by metadata search")
                else:
                    logger.warning(f"No documents found with ID {document_id}")
            
            return deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {str(e)}")
            return False
    
    def reset(self):
        """Reset the collection by deleting all documents"""
        try:
            # Delete the collection and recreate it
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction()
            )
            logger.info("Vector store collection reset successfully")
        except Exception as e:
            logger.error(f"Error resetting vector store: {str(e)}")
            raise
    
    def _split_content(self, content: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split content into chunks with overlap"""
        if len(content) <= chunk_size:
            return [content]
        
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(content):
                # Look for sentence ending within the last 200 characters
                sentence_end = max(
                    content.rfind('.', start, end),
                    content.rfind('!', start, end),
                    content.rfind('?', start, end)
                )
                
                if sentence_end > start + chunk_size - 200:
                    end = sentence_end + 1
            
            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            
            if start >= len(content):
                break
        
        return chunks
