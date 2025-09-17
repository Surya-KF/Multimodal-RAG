import google.generativeai as genai
import logging
from typing import List, Dict, Any, Tuple
import os

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.model = None
        self._initialize_gemini()
    
    def _initialize_gemini(self):
        """Initialize Gemini AI model"""
        try:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY environment variable not set")
            
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("Gemini model initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {e}")
            raise
    
    async def generate_answer(self, query: str, context_docs: List[Dict[str, Any]]) -> Tuple[str, float]:
        """Generate an answer using the LLM with retrieved context"""
        try:
            if not context_docs:
                return "I don't have enough information to answer your question.", 0.0
            
            # Prepare context from retrieved documents
            context_text = self._format_context(context_docs)
            
            # Create prompt with context and query
            prompt = self._create_prompt(query, context_text)
            
            # Generate response
            response = self.model.generate_content(prompt)
            
            if not response.text:
                return "I couldn't generate a response. Please try rephrasing your question.", 0.0
            
            # Calculate confidence based on context relevance
            confidence = self._calculate_confidence(context_docs)
            
            # Ensure the response includes source references
            answer = self._add_source_references(response.text, context_docs)
            
            return answer, confidence
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return f"An error occurred while generating the answer: {str(e)}", 0.0
    
    def _format_context(self, context_docs: List[Dict[str, Any]]) -> str:
        """Format retrieved documents into context text with titles"""
        context_parts = []
        
        # Group chunks by document to avoid confusion
        doc_groups = {}
        for doc in context_docs:
            metadata = doc.get('metadata', {})
            doc_id = metadata.get('document_id', 'unknown')
            
            if doc_id not in doc_groups:
                doc_groups[doc_id] = {
                    'title': metadata.get('title', metadata.get('filename', 'Unknown Document')),
                    'filename': metadata.get('filename', 'Unknown File'),
                    'chunks': []
                }
            
            # Clean the content to remove the "Document: [title]" prefix that we added in chunking
            content = doc.get('content', '')
            if content.startswith('Document: '):
                # Find the end of the title line and remove it
                lines = content.split('\n', 2)
                if len(lines) > 2:
                    content = lines[2]  # Skip "Document: [title]" and empty line
                elif len(lines) > 1:
                    content = lines[1]
            
            doc_groups[doc_id]['chunks'].append(content)
        
        # Format each document group
        for i, (doc_id, doc_info) in enumerate(doc_groups.items(), 1):
            title = doc_info['title']
            filename = doc_info['filename']
            chunks = doc_info['chunks']
            
            # Combine all chunks from this document
            combined_content = '\n\n'.join(chunks)
            
            # Use title if available, otherwise use filename
            if title and title != filename:
                source_info = f"Document: {title} (File: {filename})"
            else:
                source_info = f"Document: {title}"
            
            context_parts.append(f"Source {i} - {source_info}:\n{combined_content}")
        
        return "\n\n".join(context_parts)
    
    def _create_prompt(self, query: str, context: str) -> str:
        """Create a modern, sophisticated prompt for the LLM"""
        prompt = f"""You are an advanced AI research assistant with expertise in analyzing and synthesizing information from academic papers, technical documents, and multimedia content. Your responses should be modern, engaging, and professionally crafted.

🎯 **CORE INSTRUCTIONS:**
• Provide comprehensive, well-structured responses using the retrieved context
• Synthesize information across multiple sources when relevant
• Use modern formatting with clear sections, bullet points, and emphasis
• Maintain a professional yet conversational tone
• Always ground your responses in the provided evidence
• DO NOT include source citations or references in your response

📊 **RESPONSE STRUCTURE:**
• Start with a clear, direct answer to the question
• Provide detailed explanation with supporting evidence
• Use markdown formatting for better readability
• Focus on the content, not the sources

🔍 **CONTEXT ANALYSIS:**
{context}

❓ **USER QUERY:** {query}

**Instructions for Response:**
1. **Analyze** the context thoroughly to understand the main concepts
2. **Synthesize** information from multiple sources if available
3. **Structure** your response with clear headings and formatting
4. **DO NOT mention** document titles, sources, or references
5. **Enhance** readability with bullets, numbered lists, and emphasis where appropriate

Please provide a modern, well-formatted response without any source citations:"""

        return prompt
    
    def _calculate_confidence(self, context_docs: List[Dict[str, Any]]) -> float:
        """Calculate enhanced confidence score for modern RAG with optimistic scaling"""
        if not context_docs:
            return 0.5  # Increased baseline from 0.0 to be more optimistic
        
        # Use the average relevance score of top documents
        scores = [doc.get('score', 0.0) for doc in context_docs]
        avg_score = sum(scores) / len(scores)
        
        # Enhanced confidence calculation with more optimistic factors
        base_confidence = min(avg_score * 1.8 + 0.3, 1.0)  # Much more generous boost with higher floor
        
        # Factor 1: Number of relevant documents (more sources = higher confidence, more generous)
        doc_count_factor = min(len(context_docs) / 3.0, 1.0)  # Lowered threshold from 5 to 3
        
        # Factor 2: Score consistency (more forgiving on variance)
        if len(scores) > 1:
            score_std = sum([(s - avg_score) ** 2 for s in scores]) / len(scores)
            consistency_factor = max(0.7, 1.2 - score_std)  # Higher baseline and more generous
        else:
            consistency_factor = 0.9  # Increased from 0.8
        
        # Factor 3: Top document quality (boosted)
        top_score_factor = min(max(scores) * 1.4, 1.0) if scores else 0.0
        
        # Combine factors with adjusted weights favoring positive indicators
        final_confidence = (
            base_confidence * 0.45 +      # Increased weight for base score
            doc_count_factor * 0.25 +     # Increased weight for document count
            consistency_factor * 0.15 +   # Reduced penalty weight for consistency
            top_score_factor * 0.15
        )
        
        # Apply more generous quality thresholds
        if final_confidence > 0.65:  # Lowered threshold from 0.8
            final_confidence = min(final_confidence * 1.2, 1.0)  # Bigger boost from 1.1 to 1.2
        elif final_confidence > 0.45:  # New middle tier
            final_confidence = min(final_confidence * 1.1, 1.0)
        # Removed the penalty for low scores to be more optimistic
        
        # Ensure a reasonable minimum confidence level
        final_confidence = max(final_confidence, 0.55)  # Higher floor
        
        return round(final_confidence, 3)
    
    def _add_source_references(self, answer: str, context_docs: List[Dict[str, Any]]) -> str:
        """Return answer without automatic source references"""
        # Simply return the answer as-is without adding source sections
        return answer
