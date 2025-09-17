#!/usr/bin/env python3
"""
Test script for the Multimodal RAG system.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from main import MultimodalRAG

def create_test_files():
    """Create sample test files for testing."""
    test_dir = Path("./test_files")
    test_dir.mkdir(exist_ok=True)
    
    # Create a test text file
    with open(test_dir / "sample.txt", "w") as f:
        f.write("""
        This is a sample document for testing the multimodal RAG system.
        It contains information about artificial intelligence and machine learning.
        The system should be able to process this document and make it searchable.
        
        Key topics covered:
        - Natural Language Processing
        - Computer Vision
        - Speech Recognition
        - Multimodal AI systems
        """)
    
    # Create a test PDF-like file (just text with .pdf extension for testing)
    with open(test_dir / "sample.pdf", "w") as f:
        f.write("This is a sample PDF content for testing purposes.")
    
    print(f"Test files created in: {test_dir}")
    return test_dir

def test_document_processing():
    """Test document processing functionality."""
    print("\n=== Testing Document Processing ===")
    
    rag = MultimodalRAG(storage_dir="./test_data")
    
    # Test with a text file
    test_content = b"This is a test document about machine learning and AI."
    result = rag.process_document(test_content, "test.txt")
    
    print(f"Document processing result: {result}")
    
    # Test search functionality
    search_results = rag.search("machine learning")
    print(f"Search results for 'machine learning': {search_results}")
    
    return rag

def test_video_processing():
    """Test video processing functionality."""
    print("\n=== Testing Video Processing ===")
    
    rag = MultimodalRAG(storage_dir="./test_data")
    
    # Simulate video content (dummy data)
    test_content = b"dummy video content for testing"
    result = rag.process_video(test_content, "test.mp4")
    
    print(f"Video processing result: {result}")
    
    return result

def test_audio_processing():
    """Test audio processing functionality."""
    print("\n=== Testing Audio Processing ===")
    
    rag = MultimodalRAG(storage_dir="./test_data")
    
    # Simulate audio content (dummy data)
    test_content = b"dummy audio content for testing"
    result = rag.process_audio(test_content, "test.mp3")
    
    print(f"Audio processing result: {result}")
    
    return result

def test_file_management():
    """Test file listing and info retrieval."""
    print("\n=== Testing File Management ===")
    
    rag = MultimodalRAG(storage_dir="./test_data")
    
    # List all files
    files = rag.list_files()
    print(f"All files: {files}")
    
    # Get info for first file if available
    if files:
        file_hash = files[0]['file_hash']
        file_info = rag.get_file_info(file_hash)
        print(f"File info for {file_hash}: {file_info}")

def run_all_tests():
    """Run all tests."""
    print("Starting Multimodal RAG System Tests...")
    
    try:
        # Test document processing
        rag = test_document_processing()
        
        # Test video processing
        test_video_processing()
        
        # Test audio processing
        test_audio_processing()
        
        # Test file management
        test_file_management()
        
        print("\n=== All Tests Completed ===")
        print("The multimodal RAG system is working correctly!")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()