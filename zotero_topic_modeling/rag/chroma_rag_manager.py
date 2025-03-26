import logging
import threading
import os
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional
import requests
import json
import time

class ChromaRAGManager:
    """
    RAG Manager using simple retrieval methods for document Q&A.
    """
    
    def __init__(self, api_key=None, use_ollama=False, ollama_model="llama3.2:3b", 
                 embedding_model_name="all-MiniLM-L6-v2", persist_directory=None,
                 temperature=0.7, top_k=40, top_p=0.9):
        """
        Initialize the RAG manager.
        
        Args:
            api_key: Anthropic API key (optional if using Ollama)
            use_ollama: Whether to use Ollama instead of Anthropic API
            ollama_model: Model name to use with Ollama
            embedding_model_name: Embedding model to use
            persist_directory: Directory to store vector database
            temperature, top_k, top_p: Generation parameters
        """
        # LLM parameters
        self.api_key = api_key
        self.use_ollama = use_ollama
        self.ollama_model = ollama_model
        self.temperature = temperature
        self.top_k = top_k
        self.top_p = top_p
        
        # Vector DB parameters
        self.embedding_model_name = embedding_model_name
        self.persist_directory = persist_directory
        if persist_directory and not os.path.exists(persist_directory):
            os.makedirs(persist_directory)
        
        # State and storage
        self.ready = False
        self.documents = []
        self.titles = []
        self.document_index = []
        
        # API endpoints
        self.anthropic_endpoint = "https://api.anthropic.com/v1/messages"
        self.ollama_endpoint = "http://localhost:11434/api/generate"
        
        logging.info("SimpleRAGManager initialized")
        
    def process_documents(self, documents, on_complete=None):
        """Process documents in background thread"""
        threading.Thread(
            target=self._process_documents_thread,
            args=(documents, on_complete),
            daemon=True
        ).start()
    
    def _process_documents_thread(self, documents, on_complete=None):
        """Process and index documents using a simple approach"""
        try:
            logging.info(f"Processing {len(documents)} documents")
            start_time = time.time()
            
            # Reset for new processing
            self.titles = []
            self.documents = []
            self.document_index = []
            
            for doc_idx, doc in enumerate(documents):
                title = doc.get('title', 'Untitled Document')
                text = doc.get('text', '')
                
                # Store title
                self.titles.append(title)
                
                if not text:
                    logging.warning(f"Document '{title}' has no text content")
                    continue
                
                # Store the document
                self.documents.append({
                    'title': title,
                    'text': text,
                    'doc_idx': doc_idx
                })
                
                # Create chunks for the document
                chunks = self._chunk_document(text, title)
                
                # Add chunks to document index
                self.document_index.extend(chunks)
            
            self.ready = True
            elapsed_time = time.time() - start_time
            logging.info(f"Indexing completed in {elapsed_time:.2f}s. {len(self.document_index)} chunks indexed")
            
            # Call completion callback
            if on_complete:
                on_complete(True)
                
        except Exception as e:
            logging.error(f"Error processing documents: {str(e)}")
            if on_complete:
                on_complete(False)
    
    def _chunk_document(self, text, title, chunk_size=1000, overlap=200):
        """Split a document into overlapping chunks"""
        chunks = []
        
        # Check if text is long enough to chunk
        if len(text) <= chunk_size:
            return [{
                'text': text,
                'title': title,
                'chunk_id': 0
            }]
        
        # Split into chunks with overlap
        for i in range(0, len(text), chunk_size - overlap):
            chunk_text = text[i:i + chunk_size]
            
            # Ensure we're not cutting in the middle of a sentence if possible
            if i > 0 and i + chunk_size < len(text):
                # Find the first sentence end after the start of this chunk
                import re
                match = re.search(r'[.!?]\s+', chunk_text[:overlap])
                if match:
                    start_pos = match.end()
                    chunk_text = chunk_text[start_pos:]
                
                # Find the last sentence end before the end of this chunk
                last_part = chunk_text[-overlap:] if len(chunk_text) > overlap else chunk_text
                match = re.search(r'[.!?]\s+[A-Z]', last_part)
                if match:
                    end_pos = len(chunk_text) - overlap + match.start() + 1
                    chunk_text = chunk_text[:end_pos]
            
            # Create chunk with metadata
            chunk_id = len(chunks)
            chunks.append({
                'text': chunk_text,
                'title': f"{title} (Part {chunk_id + 1})",
                'chunk_id': chunk_id
            })
        
        return chunks
    
    def retrieve_relevant_documents(self, query, top_k=3):
        """
        Retrieve the most relevant documents for a query using simple keyword matching.
        
        Args:
            query: User's question
            top_k: Number of documents to retrieve
        
        Returns:
            List of relevant document dictionaries
        """
        if not self.ready or not self.document_index:
            return []
        
        # Simple keyword matching
        query_words = set(query.lower().split())
        
        # Score all chunks
        scored_chunks = []
        for chunk in self.document_index:
            # Count matching words
            chunk_text = chunk['text'].lower()
            score = sum(1 for word in query_words if word in chunk_text)
            
            if score > 0:
                scored_chunks.append({
                    'title': chunk['title'],
                    'text': chunk['text'],
                    'score': score
                })
        
        # Sort by score (descending) and take top k
        scored_chunks.sort(key=lambda x: x['score'], reverse=True)
        return scored_chunks[:top_k]
    
    def is_ready(self):
        """Check if system is ready to process queries"""
        return self.ready and len(self.document_index) > 0
    
    def estimate_tokens(self, text):
        """Estimate number of tokens in text"""
        if not text:
            return 0
        
        # Simple estimation: ~4 chars per token for most languages
        return int(len(text) / 4.0)
    
    def generate_response(self, query):
        """Generate response to user query using RAG"""
        if not self.is_ready():
            return "I'm still processing your documents. Please wait a moment."
        
        try:
            # Retrieve relevant document chunks
            relevant_chunks = self.retrieve_relevant_documents(query)
            
            if not relevant_chunks:
                context = "I don't have enough information to answer this question based on the documents."
            else:
                # Create context from relevant chunks
                context = "Here's information from relevant documents:\n\n"
                
                for i, chunk in enumerate(relevant_chunks):
                    context += f"Document {i+1}: {chunk['title']}\n{chunk['text']}\n\n"
                
                # Limit context length to avoid token limits
                context_tokens = self.estimate_tokens(context)
                if context_tokens > 4000:  # Reasonable limit
                    context = context[:16000]  # ~4000 tokens
                    context += "\n\n(Some information was truncated due to context limits.)"
            
            # Generate response with appropriate model
            if self.use_ollama:
                return self._generate_ollama_response(query, context)
            else:
                return self._generate_claude_response(query, context)
                
        except Exception as e:
            logging.error(f"Error generating response: {str(e)}")
            return f"I encountered an error while generating a response: {str(e)}"
    
    def _generate_claude_response(self, query, context):
        """Generate response using Claude API"""
        if not self.api_key:
            return "No Anthropic API key provided. Please configure your API key or switch to Ollama."
        
        try:
            # Prepare prompt
            system_prompt = (
                "You are a helpful assistant answering questions about scientific documents. "
                "Base your answers only on the provided context. "
                "If you don't know the answer, say so clearly. "
                "Provide detailed and precise answers, citing relevant documents."
            )
            
            user_message = f"Context:\n{context}\n\nQuestion: {query}\nPlease answer based on the provided context."
            
            # Prepare API request
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            
            data = {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 1000,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "system": system_prompt,
                "messages": [
                    {"role": "user", "content": user_message}
                ]
            }
            
            # Make API request
            response = requests.post(
                self.anthropic_endpoint,
                headers=headers,
                json=data,
                timeout=30
            )
            
            # Process response
            if response.status_code == 200:
                result = response.json()
                return result.get("content", [{}])[0].get("text", "No API response")
            else:
                error_msg = f"API error: {response.status_code} - {response.text}"
                logging.error(error_msg)
                return f"Error: {error_msg}"
                
        except Exception as e:
            logging.error(f"Claude API error: {str(e)}")
            return f"I encountered an error: {str(e)}"
    
    def _generate_ollama_response(self, query, context):
        """Generate response using local Ollama model"""
        try:
            # Prepare prompt
            prompt = f"""You are a helpful assistant answering questions about scientific documents.
Base your answers only on the provided context.
If you don't know the answer, say so clearly.
Provide detailed and precise answers, citing relevant documents.

Context:
{context}

Question: {query}

Please answer based on the provided context.
"""
            
            # Prepare API request
            data = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": 1000,
                    "temperature": self.temperature,
                    "top_k": self.top_k,
                    "top_p": self.top_p
                }
            }
            
            # Log token usage estimate
            prompt_tokens = self.estimate_tokens(prompt)
            logging.info(f"Ollama request: ~{prompt_tokens} tokens in prompt")
            
            # Make API request
            response = requests.post(
                self.ollama_endpoint,
                json=data,
                timeout=60  # Longer timeout for local models
            )
            
            # Process response
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "No response from Ollama")
            else:
                error_msg = f"Ollama API error: {response.status_code} - {response.text}"
                logging.error(error_msg)
                return f"Error: {error_msg}"
                
        except requests.exceptions.ConnectionError:
            return "Could not connect to Ollama. Please make sure it's running at http://localhost:11434."
        except Exception as e:
            logging.error(f"Ollama API error: {str(e)}")
            return f"I encountered an error: {str(e)}"
    
    def get_available_ollama_models(self):
        """Get list of available models from Ollama"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [model.get('name') for model in models]
            return []
        except:
            return []
            
    def fetch_available_ollama_models(self):
        """Fetch and return available Ollama models"""
        return self.get_available_ollama_models()
