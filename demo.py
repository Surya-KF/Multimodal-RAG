#!/usr/bin/env python3
"""
Demo script for the Multimodal RAG system.
Shows how to use the API programmatically.
"""

import time
import requests
import json
from pathlib import Path

# Server configuration
SERVER_URL = "http://localhost:8000"

def wait_for_server(timeout=30):
    """Wait for the server to be ready."""
    print("⏳ Waiting for server to start...")
    
    for i in range(timeout):
        try:
            response = requests.get(f"{SERVER_URL}/api/status", timeout=2)
            if response.status_code == 200:
                print("✅ Server is ready!")
                return True
        except requests.exceptions.RequestException:
            time.sleep(1)
            continue
    
    print("❌ Server didn't start within timeout")
    return False

def create_sample_files():
    """Create sample files for demonstration."""
    sample_dir = Path("./demo_files")
    sample_dir.mkdir(exist_ok=True)
    
    # Create sample text document
    with open(sample_dir / "ai_research.txt", "w") as f:
        f.write("""
        Artificial Intelligence Research Overview
        
        This document covers recent advances in AI research including:
        
        1. Large Language Models (LLMs)
        - GPT-4 and ChatGPT applications
        - BERT and transformer architectures
        - Fine-tuning techniques
        
        2. Computer Vision
        - Object detection and recognition
        - Image segmentation
        - Generative adversarial networks (GANs)
        
        3. Multimodal AI
        - Vision-language models
        - Audio-visual understanding
        - Cross-modal retrieval systems
        
        4. Machine Learning Operations (MLOps)
        - Model deployment strategies
        - Continuous integration for ML
        - Monitoring and maintenance
        
        These technologies are transforming industries including healthcare,
        autonomous vehicles, and natural language processing applications.
        """)
    
    # Create sample markdown document
    with open(sample_dir / "project_plan.md", "w") as f:
        f.write("""
        # Project Implementation Plan
        
        ## Phase 1: Data Collection
        - Gather training datasets
        - Clean and preprocess data
        - Validate data quality
        
        ## Phase 2: Model Development
        - Design neural network architecture
        - Implement training pipeline
        - Optimize hyperparameters
        
        ## Phase 3: Evaluation
        - Performance benchmarking
        - A/B testing setup
        - User acceptance testing
        
        ## Phase 4: Deployment
        - Production environment setup
        - Monitoring and logging
        - Continuous deployment pipeline
        """)
    
    print(f"📁 Sample files created in: {sample_dir}")
    return sample_dir

def upload_document(file_path):
    """Upload a document to the RAG system."""
    print(f"📤 Uploading document: {file_path.name}")
    
    with open(file_path, 'rb') as f:
        files = {'file': (file_path.name, f, 'text/plain')}
        response = requests.post(f"{SERVER_URL}/upload/document", files=files)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Upload successful: {result['file_hash']}")
        return result
    else:
        print(f"❌ Upload failed: {response.status_code}")
        print(response.text)
        return None

def search_content(query):
    """Search for content in the RAG system."""
    print(f"🔍 Searching for: '{query}'")
    
    response = requests.get(f"{SERVER_URL}/search", params={'query': query})
    
    if response.status_code == 200:
        results = response.json()
        print(f"📊 Found {results['count']} result(s)")
        
        for i, result in enumerate(results['results'], 1):
            print(f"\n{i}. {result['filename']} ({result['file_type']})")
            print(f"   Snippet: {result['relevance_snippet'][:100]}...")
        
        return results
    else:
        print(f"❌ Search failed: {response.status_code}")
        return None

def list_files():
    """List all uploaded files."""
    print("📋 Listing all uploaded files...")
    
    response = requests.get(f"{SERVER_URL}/files")
    
    if response.status_code == 200:
        data = response.json()
        print(f"📁 Total files: {data['count']}")
        
        for file_info in data['files']:
            print(f"  - {file_info['filename']} ({file_info['file_type']}) [{file_info['file_extension']}]")
        
        return data
    else:
        print(f"❌ Failed to list files: {response.status_code}")
        return None

def get_file_details(file_hash):
    """Get detailed information about a specific file."""
    print(f"🔍 Getting details for file: {file_hash}")
    
    response = requests.get(f"{SERVER_URL}/files/{file_hash}")
    
    if response.status_code == 200:
        details = response.json()
        print(f"📄 Filename: {details['filename']}")
        print(f"📊 Type: {details['file_type']}")
        print(f"📝 Text length: {details.get('full_text_length', 'N/A')} characters")
        print(f"🧩 Chunks: {len(details.get('chunks', []))} pieces")
        
        return details
    else:
        print(f"❌ Failed to get file details: {response.status_code}")
        return None

def run_demo():
    """Run the complete demonstration."""
    print("🚀 Starting Multimodal RAG Demo")
    print("=" * 50)
    
    # Wait for server
    if not wait_for_server():
        print("❌ Please start the server first: ./start.sh")
        return
    
    # Create sample files
    sample_dir = create_sample_files()
    
    print("\n" + "=" * 50)
    print("📤 UPLOADING DOCUMENTS")
    print("=" * 50)
    
    # Upload documents
    uploaded_files = []
    for file_path in sample_dir.glob("*.txt"):
        result = upload_document(file_path)
        if result:
            uploaded_files.append(result)
    
    for file_path in sample_dir.glob("*.md"):
        result = upload_document(file_path)
        if result:
            uploaded_files.append(result)
    
    print("\n" + "=" * 50)
    print("🔍 SEARCHING CONTENT")
    print("=" * 50)
    
    # Perform searches
    search_queries = [
        "machine learning",
        "GPT-4",
        "deployment",
        "neural network",
        "computer vision"
    ]
    
    for query in search_queries:
        search_content(query)
        time.sleep(0.5)  # Brief pause between searches
    
    print("\n" + "=" * 50)
    print("📋 FILE MANAGEMENT")
    print("=" * 50)
    
    # List files
    files_data = list_files()
    
    # Get details for first file
    if files_data and files_data['files']:
        first_file = files_data['files'][0]
        print(f"\n📄 Getting details for: {first_file['filename']}")
        get_file_details(first_file['file_hash'])
    
    print("\n" + "=" * 50)
    print("✅ DEMO COMPLETED")
    print("=" * 50)
    print("🌐 Visit http://localhost:8000 to try the web interface!")
    print("📚 Check the README.md for more information")

if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()