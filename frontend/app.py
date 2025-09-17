import streamlit as st
import requests
import json
from typing import List, Dict, Any
import os
from datetime import datetime
import time

# Configure Streamlit page
st.set_page_config(
    page_title="Multimodal RAG Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern UI - Fixed for sidebar visibility
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Force sidebar to be visible on all screen sizes with gradient background */
    section[data-testid="stSidebar"] {
        width: 320px !important;
        min-width: 320px !important;
        max-width: 320px !important;
        background: linear-gradient(135deg, #ffffff 0%, #e3f2fd 50%, #f5f5f5 100%) !important;
    }
    
    section[data-testid="stSidebar"] > div {
        width: 320px !important;
        min-width: 320px !important;
        max-width: 320px !important;
        padding: 1rem !important;
        background: linear-gradient(135deg, #ffffff 0%, #e3f2fd 50%, #f5f5f5 100%) !important;
    }
    
    /* Ensure sidebar content is visible with dark text */
    .css-1d391kg, .css-1lcbmhc {
        padding-top: 1rem !important;
        padding-right: 1rem !important;
        padding-left: 1rem !important;
        background: linear-gradient(135deg, #ffffff 0%, #e3f2fd 50%, #f5f5f5 100%) !important;
    }
    
    /* Sidebar text colors - dark text on gradient background */
    section[data-testid="stSidebar"] * {
        color: #2c3e50 !important;
    }
    
    /* Sidebar headers */
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #1976d2 !important;
        text-shadow: 0 1px 2px rgba(255,255,255,0.8) !important;
    }
    
    /* Sidebar markdown text */
    section[data-testid="stSidebar"] .markdown-text-container {
        color: #37474f !important;
    }
    
    /* Sidebar info boxes */
    section[data-testid="stSidebar"] .stAlert {
        background: linear-gradient(135deg, rgba(227, 242, 253, 0.8) 0%, rgba(255, 255, 255, 0.9) 100%) !important;
        color: #1976d2 !important;
        border: 1px solid #bbdefb !important;
        backdrop-filter: blur(10px) !important;
    }
    
    /* Sidebar file uploader */
    section[data-testid="stSidebar"] .stFileUploader {
        background: linear-gradient(135deg, rgba(248, 249, 250, 0.9) 0%, rgba(227, 242, 253, 0.7) 100%) !important;
        border: 2px dashed #667eea !important;
        border-radius: 10px !important;
        backdrop-filter: blur(5px) !important;
    }
    
    /* Sidebar buttons - ensure they are visible and styled properly */
    section[data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 600 !important;
        width: 100% !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
    }
    
    /* Force all button types in sidebar to have same styling */
    section[data-testid="stSidebar"] button[kind="primary"],
    section[data-testid="stSidebar"] button[kind="secondary"],
    section[data-testid="stSidebar"] button[kind="tertiary"],
    section[data-testid="stSidebar"] button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
    }
    
    /* Sidebar button hover effect - applies to all sidebar buttons including delete buttons */
    section[data-testid="stSidebar"] .stButton > button:hover,
    section[data-testid="stSidebar"] button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4) !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    }
    
    /* Main content area adjustment */
    .main .block-container {
        padding-left: 2rem;
        max-width: none;
    }
    
    /* Custom font for the entire app */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Header styles */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    /* Chat container */
    .chat-container {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: 1px solid #e1e8ed;
        margin-bottom: 1rem;
    }
    
    /* Message styles */
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 18px 18px 5px 18px;
        margin: 1rem 0;
        margin-left: 20%;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        color: #2c3e50;
        padding: 1rem 1.5rem;
        border-radius: 18px 18px 18px 5px;
        margin: 1rem 0;
        margin-right: 10%;
        border-left: 4px solid #667eea;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        font-weight: 600;
        font-size: 1rem;
    }
    
    /* Enhanced styling for assistant content within the message box */
    .assistant-content {
        margin-top: 0.5rem;
        line-height: 1.6;
    }
    
    .assistant-content h1, .assistant-content h2, .assistant-content h3 {
        color: #2c3e50;
        margin-top: 1.2rem;
        margin-bottom: 0.6rem;
        font-weight: 700;
    }
    
    .assistant-content h3 {
        color: #667eea;
        font-size: 1.1rem;
        border-bottom: 1px solid #e9ecef;
        padding-bottom: 0.2rem;
    }
    
    .assistant-content ul, .assistant-content ol {
        margin: 0.8rem 0;
        padding-left: 1.2rem;
    }
    
    .assistant-content li {
        margin: 0.3rem 0;
        line-height: 1.5;
    }
    
    .assistant-content strong {
        color: #495057;
        font-weight: 700;
    }
    
    .assistant-content em {
        color: #6c757d;
        font-style: italic;
    }
    
    .assistant-content code {
        background: #ffffff;
        color: #e83e8c;
        padding: 0.2rem 0.4rem;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
        font-size: 0.85rem;
        border: 1px solid #dee2e6;
    }
    
    .assistant-content blockquote {
        border-left: 3px solid #667eea;
        background: #ffffff;
        margin: 0.8rem 0;
        padding: 0.8rem;
        border-radius: 0 6px 6px 0;
        font-style: italic;
    }
    
    .assistant-content p {
        margin: 0.5rem 0;
        line-height: 1.6;
    }
    
    /* File upload area */
    .upload-area {
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        border: 2px dashed #667eea;
        border-radius: 15px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    
    .upload-area:hover {
        border-color: #764ba2;
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
    }
    
    /* Sidebar styles - keep simple */
    /* No special sidebar styling */
    
    /* Metrics cards */
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border: 1px solid #e1e8ed;
        margin: 0.5rem 0;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
        margin-bottom: 0.5rem;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Source cards */
    .source-card {
        background: #ffffff;
        border: 1px solid #e1e8ed;
        border-left: 4px solid #2196f3;
        padding: 1.2rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        color: #2c3e50;
    }
    
    /* Success/Error messages */
    .success-msg {
        background: linear-gradient(135deg, #d4edda 0%, #f8f9fa 100%);
        color: #155724;
        border: 1px solid #c3e6cb;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .error-msg {
        background: linear-gradient(135deg, #f8d7da 0%, #f8f9fa 100%);
        color: #721c24;
        border: 1px solid #f5c6cb;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Button styles */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Input fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 10px;
        border: 2px solid #e1e8ed;
        padding: 0.75rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Spinner customization */
    .stSpinner > div > div {
        border-color: #667eea;
    }
    
    /* Hide Streamlit branding but keep sidebar */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
</style>
""", unsafe_allow_html=True)

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

def upload_file(file) -> Dict[str, Any]:
    """Upload file to backend"""
    try:
        files = {"file": (file.name, file.getvalue(), file.type)}
        response = requests.post(f"{BACKEND_URL}/upload", files=files)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Upload failed: {response.text}")
            return None
    except Exception as e:
        st.error(f"Upload error: {str(e)}")
        return None

def query_chatbot(query: str, max_results: int = 5) -> Dict[str, Any]:
    """Query the chatbot"""
    try:
        payload = {
            "query": query,
            "max_results": max_results
        }
        response = requests.post(f"{BACKEND_URL}/query", json=payload)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Query failed: {response.text}")
            return None
    except Exception as e:
        st.error(f"Query error: {str(e)}")
        return None

@st.cache_data(ttl=10)  # Cache for 10 seconds
def get_documents() -> List[Dict[str, Any]]:
    """Get list of uploaded documents"""
    try:
        response = requests.get(f"{BACKEND_URL}/documents")
        if response.status_code == 200:
            return response.json().get("documents", [])
        else:
            return []
    except Exception as e:
        st.error(f"Error fetching documents: {str(e)}")
        return []

def delete_document(document_id: str) -> bool:
    """Delete a specific document"""
    try:
        response = requests.delete(f"{BACKEND_URL}/documents/{document_id}")
        if response.status_code == 200:
            return True
        else:
            st.error(f"Failed to delete document: {response.text}")
            return False
    except Exception as e:
        st.error(f"Error deleting document: {str(e)}")
        return False

def clear_all_documents() -> bool:
    """Clear all documents"""
    try:
        response = requests.delete(f"{BACKEND_URL}/documents")
        if response.status_code == 200:
            return True
        else:
            st.error(f"Failed to clear documents: {response.text}")
            return False
    except Exception as e:
        st.error(f"Error clearing documents: {str(e)}")
        return False

def display_modern_header():
    """Display modern header with branding"""
    st.markdown("""
    <div class="main-header">
        <h1>🤖 Multimodal RAG Assistant</h1>
        <p>Intelligent document analysis with AI-powered insights • Upload • Chat • Discover</p>
    </div>
    """, unsafe_allow_html=True)

def display_metrics(documents):
    """Display metrics in modern cards"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(documents)}</div>
            <div class="metric-label">📄 Documents</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        pdf_count = sum(1 for doc in documents if 'pdf' in doc.get('file_type', '').lower())
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{pdf_count}</div>
            <div class="metric-label">📑 PDFs</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        audio_count = sum(1 for doc in documents if 'audio' in doc.get('file_type', '').lower())
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{audio_count}</div>
            <div class="metric-label">🎵 Audio</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        video_count = sum(1 for doc in documents if 'video' in doc.get('file_type', '').lower())
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{video_count}</div>
            <div class="metric-label">🎬 Video</div>
        </div>
        """, unsafe_allow_html=True)

def display_chat_message(message, is_user=True):
    """Display chat message with modern RAG styling"""
    import html
    import re
    
    if is_user:
        # Simple user message display
        st.markdown(f"""
        <div class="user-message">
            <strong>👤 You:</strong><br>
            {html.escape(message)}
        </div>
        """, unsafe_allow_html=True)
    else:
        # Enhanced assistant message with markdown support - all content inside the white box
        content_html = f"""
        <div class="assistant-message">
            <strong>🤖 Assistant:</strong><br><br>
            <div class="assistant-content">
                {message}
            </div>
        </div>
        """
        st.markdown(content_html, unsafe_allow_html=True)

def display_sources(sources):
    """Display sources with collapsible expander using titles"""
    if sources:
        with st.expander(f"📚 Sources ({len(sources)} found)", expanded=False):
            for i, source in enumerate(sources, 1):
                # Handle different possible metadata structures
                metadata = source.get('metadata', {})
                
                # Extract title with multiple fallback options
                title = (
                    metadata.get('title') or
                    source.get('title') or
                    metadata.get('filename') or
                    source.get('filename') or
                    source.get('document_id') or
                    metadata.get('document_id') or
                    f"Document_{i}"
                )
                
                # Extract filename separately
                filename = (
                    metadata.get('filename') or
                    source.get('filename') or
                    source.get('file_name') or
                    source.get('document_name') or
                    metadata.get('file_name') or
                    metadata.get('source') or
                    metadata.get('document') or
                    metadata.get('document_name') or
                    metadata.get('file') or
                    metadata.get('name') or
                    "Unknown File"
                )
                
                # Get content from multiple possible fields
                content = (
                    source.get('content') or 
                    source.get('text') or 
                    source.get('content_preview') or
                    "No content available"
                )
                
                if len(content) > 200:
                    content = content[:200] + "..."
                
                # Escape HTML characters
                import html
                escaped_title = html.escape(str(title))
                escaped_filename = html.escape(str(filename))
                escaped_content = html.escape(str(content))
                
                # Show title prominently, filename as subtitle if different
                if title != filename and filename != "Unknown File":
                    source_header = f"📄 Source {i}: {escaped_title}<br><small>File: {escaped_filename}</small>"
                else:
                    source_header = f"📄 Source {i}: {escaped_title}"
                
                st.markdown(f"""
                <div class="source-card">
                    <strong>{source_header}</strong><br>
                    <em>{escaped_content}</em>
                </div>
                """, unsafe_allow_html=True)

def main():
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "documents" not in st.session_state:
        st.session_state.documents = []
    if 'processed_files' not in st.session_state:
        st.session_state.processed_files = set()
    if 'uploaded_files_pending' not in st.session_state:
        st.session_state.uploaded_files_pending = []
    if 'is_generating' not in st.session_state:
        st.session_state.is_generating = False

    # Display modern header
    display_modern_header()
    
    # Get documents and update session state only if needed
    if 'documents' not in st.session_state or not st.session_state.documents:
        documents = get_documents()
        st.session_state.documents = documents
    else:
        documents = st.session_state.documents
    
    # Display metrics
    display_metrics(documents)
    
    # SIDEBAR - Modified implementation with process button
    with st.sidebar:
        st.markdown("# 📁 Document Management")
        st.markdown("---")
        
        # File upload section
        st.markdown("### 📤 Upload Files")
        uploaded_files = st.file_uploader(
            "Choose files to upload",
            type=['pdf', 'wav', 'mp3', 'mp4', 'avi', 'mov', 'mkv', 'm4a', 'flac'],
            help="Supported: PDF, Audio, Video files",
            accept_multiple_files=True,
            key="file_uploader_main"
        )
        
        # Store uploaded files in session state without processing
        if uploaded_files:
            st.session_state.uploaded_files_pending = uploaded_files
            st.info(f"📁 {len(uploaded_files)} file(s) ready to process")
            
            # Display pending files
            for file in uploaded_files:
                st.write(f"• {file.name} ({file.type})")
        
        # Process button - only show if there are pending files
        if st.session_state.uploaded_files_pending:
            if st.button("🚀 Process Files", use_container_width=True, type="primary"):
                processed_count = 0
                failed_count = 0
                
                for uploaded_file in st.session_state.uploaded_files_pending:
                    file_key = f"{uploaded_file.name}_{uploaded_file.size}"
                    
                    if file_key not in st.session_state.processed_files:
                        with st.spinner(f"Processing {uploaded_file.name}..."):
                            success = upload_file(uploaded_file)
                            if success:
                                st.success(f"✅ {uploaded_file.name} processed!")
                                st.session_state.processed_files.add(file_key)
                                processed_count += 1
                            else:
                                st.error(f"❌ Failed to process {uploaded_file.name}")
                                failed_count += 1
                
                # Clear pending files after processing
                st.session_state.uploaded_files_pending = []
                
                if processed_count > 0:
                    st.success(f"Successfully processed {processed_count} file(s)!")
                if failed_count > 0:
                    st.error(f"Failed to process {failed_count} file(s)")
                
                # Only rerun once after all processing is complete
                time.sleep(1)
                st.rerun()
        
        st.markdown("---")
        st.markdown("### 📚 Your Documents")
        
        # Document list
        if documents:
            for idx, doc in enumerate(documents):
                filename = doc.get('filename', 'Unknown')
                file_type = doc.get('file_type', 'Unknown')
                
                # File type icon
                if 'pdf' in file_type.lower():
                    icon = "📄"
                elif 'audio' in file_type.lower():
                    icon = "🎵"
                elif 'video' in file_type.lower():
                    icon = "🎬"
                else:
                    icon = "📁"
                
                # Display file info
                st.markdown(f"{icon} **{filename}**")
                st.caption(f"Type: {file_type}")
                
                # Delete button
                delete_key = f"delete_{idx}_{hash(filename) % 10000}"
                if st.button("🗑️ Delete", key=delete_key, help=f"Delete {filename}", use_container_width=True, type="primary"):
                    doc_id = doc.get('id', filename)
                    if delete_document(doc_id):
                        st.success("File deleted!")
                        # Use a flag to prevent multiple reruns
                        st.session_state.documents = []  # Clear cache
                        time.sleep(0.5)  # Reduced delay
                        st.rerun()
                    else:
                        st.error("Delete failed!")
                
                if idx < len(documents) - 1:
                    st.markdown("---")
        else:
            st.info("📭 No documents uploaded yet.")
            st.markdown("Upload files above and click 'Process Files'!")
        
        # Quick actions
        if documents:
            st.markdown("---")
            st.markdown("### ⚡ Quick Actions")
            
            if st.button("🗑️ Clear All Documents", use_container_width=True, type="primary"):
                if clear_all_documents():
                    st.success("All documents cleared!")
                    st.session_state.processed_files.clear()
                    st.session_state.documents = []  # Clear cache
                    time.sleep(0.5)  # Reduced delay
                    st.rerun()
                else:
                    st.error("Failed to clear documents")
            
            if st.button("🔄 Refresh List", use_container_width=True, type="primary"):
                st.session_state.documents = []  # Clear cache
                st.rerun()
        
        # App info
        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.markdown("""
        **Multimodal RAG Assistant**
        
        Upload documents to chat with your content using AI.
        
        🔹 **PDF**: Text extraction  
        🔹 **Audio**: Speech transcription  
        🔹 **Video**: Audio extraction + transcription  
        """)

    # Main chat interface
    st.markdown("### 💬 Chat with Your Documents")
    
    # Add example queries for better UX
    if not st.session_state.messages:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%); padding: 1.5rem; border-radius: 12px; margin: 1rem 0; border-left: 4px solid #667eea;">
            <h4 style="color: #2c3e50; margin-top: 0;">💡 Try asking questions like:</h4>
            <ul style="color: #495057; margin-bottom: 0;">
                <li><strong>"Summarize the main findings of this document"</strong></li>
                <li><strong>"What are the key arguments presented by the author?"</strong></li>
                <li><strong>"Extract the methodology used in this research"</strong></li>
                <li><strong>"What are the limitations mentioned in the study?"</strong></li>
                <li><strong>"Compare different approaches discussed in the documents"</strong></li>
                <li><strong>"What conclusions can be drawn from the data?"</strong></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Display chat messages
    if st.session_state.messages:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for message in st.session_state.messages:
            if message["role"] == "user":
                display_chat_message(message["content"], is_user=True)
            else:
                display_chat_message(message["content"], is_user=False)
                if "sources" in message:
                    display_sources(message["sources"])
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="chat-container">
            <div class="assistant-message">
                <strong>🤖 Assistant:</strong><br>
                Hello! I'm your multimodal RAG assistant. Upload some documents using the sidebar and ask me anything about their content!
                <br><br>
                <strong>Try asking:</strong>
                <ul>
                    <li>"What are the main topics in my documents?"</li>
                    <li>"Summarize the key points from my uploaded files"</li>
                    <li>"What did the speaker mention about [topic]?"</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
   
    
    # Create a placeholder for the thinking spinner
    thinking_placeholder = st.empty()
    
    # Show thinking spinner above input when generating
    if st.session_state.is_generating:
        with thinking_placeholder.container():
            with st.spinner("🤔 Thinking..."):
                # This will keep the spinner active while processing
                time.sleep(0.1)
    
    # Create form for Enter key submission
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "Type your question here...",
            placeholder="Ask me anything about your uploaded documents... (Press Ctrl+Enter to send)",
            height=100,
            key="user_input_main",
            help="Press Ctrl+Enter to send your message"
        )
        
        # Dynamic button based on generation state
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.session_state.is_generating:
                # Show pause/stop button during generation
                send_button = st.form_submit_button(
                    "⏸️ Generating...", 
                    type="secondary", 
                    use_container_width=True,
                    disabled=True
                )
            else:
                # Show send button when ready
                send_button = st.form_submit_button(
                    "🚀 Send Message", 
                    type="primary", 
                    use_container_width=True
                )
    
    # Handle form submission first - this ensures user message is added immediately
    if send_button and user_input.strip() and not st.session_state.is_generating:
        if not documents:
            st.warning("⚠️ Please upload some documents first!")
        else:
            # Add user message immediately
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.session_state.is_generating = True
            st.rerun()  # Rerun to show thinking indicator immediately
    
    # Process the query when generating (this runs after rerun)
    if st.session_state.is_generating and len(st.session_state.messages) > 0:
        last_message = st.session_state.messages[-1]
        if last_message["role"] == "user":
            # Query backend with spinner shown above
            with thinking_placeholder.container():
                with st.spinner("🤔 Analyzing your question and searching through documents..."):
                    response = query_chatbot(last_message["content"])
            
            if response:
                answer = response.get('answer', 'No answer received')
                sources = response.get('sources', [])
                confidence = response.get('confidence_score', 0.0)
                
                # Enhance answer with confidence indicator
                if confidence > 0:
                    confidence_text = f"\n\n**Confidence Level:** {confidence:.1%}"
                    if confidence >= 0.8:
                        confidence_text += " 🟢 *High confidence*"
                    elif confidence >= 0.6:
                        confidence_text += " 🟡 *Medium confidence*"
                    else:
                        confidence_text += " 🔴 *Low confidence - consider asking for clarification*"
                    
                    answer = answer + confidence_text
                
                message_data = {"role": "assistant", "content": answer}
                if sources:
                    message_data["sources"] = sources
                if confidence > 0:
                    message_data["confidence"] = confidence
                st.session_state.messages.append(message_data)
            else:
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": "❌ Sorry, I couldn't process your question. Please try again or check if your documents are properly uploaded."
                })
            
            # Reset generating state and clear thinking spinner
            st.session_state.is_generating = False
            thinking_placeholder.empty()
            st.rerun()
    
    elif send_button and not user_input.strip():
        st.warning("⚠️ Please enter a question!")

   

if __name__ == "__main__":
    main()
