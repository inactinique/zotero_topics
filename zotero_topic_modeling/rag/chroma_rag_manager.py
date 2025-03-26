# File: zotero_topic_modeling/rag/chroma_rag_manager.py

import logging
import threading
import os
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional
import requests
import json
import time
import uuid
import sys

class ChromaRAGManager:
    """
    RAG Manager using LangChain and Chroma for vector search.
    """
    
    def __init__(self, api_key=None, use_ollama=False, ollama_model="llama3.2:3b", 
                 embedding_model_name="all-MiniLM-L6-v2", persist_directory=None,
                 temperature=0.7, top_k=40, top_p=0.9):
        """
        Initialize the RAG manager with Chroma.
        
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
        
        # IMPORTANT: Explicitly set cache directory for transformers
        # This helps manage model downloads on macOS
        os.environ['TRANSFORMERS_CACHE'] = os.path.join(Path.home(), '.cache', 'huggingface')
        cache_dir = os.environ['TRANSFORMERS_CACHE']
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)
        logging.info(f"Using transformers cache directory: {cache_dir}")
        
        # Initialize embedding model
        self.embeddings = None
        try:
            # Import here to handle import errors gracefully
            try:
                from langchain_community.embeddings import HuggingFaceEmbeddings
                logging.info("Successfully imported HuggingFaceEmbeddings")
            except ImportError as e:
                logging.error(f"Error importing HuggingFaceEmbeddings: {str(e)}")
                raise ImportError("Failed to import HuggingFaceEmbeddings. Please ensure langchain-community is installed.")
            
            # Explicitly download model if needed
            try:
                import sentence_transformers
                logging.info(f"Using sentence-transformers version: {sentence_transformers.__version__}")
                
                from sentence_transformers import SentenceTransformer
                # Try to load the model with explicit cache path
                model = SentenceTransformer(
                    embedding_model_name, 
                    cache_folder=cache_dir
                )
                logging.info(f"Successfully loaded model: {embedding_model_name}")
                
                # Initialize embeddings with the pre-loaded model
                self.embeddings = HuggingFaceEmbeddings(
                    model_name=embedding_model_name,
                    cache_folder=cache_dir
                )
                logging.info("HuggingFaceEmbeddings initialized successfully")
            except Exception as e:
                logging.error(f"Error loading embedding model: {str(e)}")
                raise ValueError(f"Failed to initialize embedding model: {str(e)}")
        except Exception as main_error:
            logging.error(f"Failed to initialize embeddings: {str(main_error)}")
            self.embeddings = None
        
        # Initialize text splitter
        try:
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=100,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            logging.info("Text splitter initialized")
        except ImportError:
            logging.error("Failed to import RecursiveCharacterTextSplitter")
            raise ImportError("Failed to import RecursiveCharacterTextSplitter. Please ensure langchain is installed.")
        
        # Vector store
        self.vector_store = None
        
        # Document metadata
        self.document_metadata = {}
        self.titles = []
        
        # State
        self.ready = False
        
        # API endpoints
        self.anthropic_endpoint = "https://api.anthropic.com/v1/messages"
        self.ollama_endpoint = "http://localhost:11434/api/generate"
        
        # Try to load existing Chroma database
        if self.persist_directory and os.path.exists(self.persist_directory):
            try:
                self.load_vector_store()
            except Exception as e:
                logging.error(f"Error loading Chroma DB: {str(e)}")
        
        logging.info("ChromaRAGManager initialized")
    
    def load_vector_store(self):
        """Load existing Chroma database"""
        if not self.embeddings:
            logging.error("Cannot load vector store: embedding model not initialized")
            return False
            
        try:
            # Import here to handle import errors gracefully
            try:
                from langchain_community.vectorstores import Chroma
                logging.info("Successfully imported Chroma")
            except ImportError:
                logging.error("Failed to import Chroma")
                return False
            
            # Load Chroma DB
            self.vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
            logging.info(f"Loaded Chroma DB from {self.persist_directory}")
            
            # Load metadata if available
            metadata_path = os.path.join(self.persist_directory, "metadata.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.document_metadata = data.get('document_metadata', {})
                    self.titles = data.get('titles', [])
                logging.info(f"Loaded metadata for {len(self.titles)} documents")
            
            self.ready = True
            return True
        except Exception as e:
            logging.error(f"Error loading Chroma DB: {str(e)}")
            return False
    
    def save_metadata(self):
        """Save document metadata separately"""
        if not self.persist_directory:
            return
            
        try:
            metadata_path = os.path.join(self.persist_directory, "metadata.json")
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'document_metadata': self.document_metadata,
                    'titles': self.titles
                }, f, ensure_ascii=False, indent=2)
            logging.info(f"Saved metadata to {metadata_path}")
        except Exception as e:
            logging.error(f"Error saving metadata: {str(e)}")
    
    def process_documents(self, documents, on_complete=None):
        """Process documents in background thread"""
        threading.Thread(
            target=self._process_documents_thread,
            args=(documents, on_complete),
            daemon=True
        ).start()
    
    def _process_documents_thread(self, documents, on_complete=None):
        """Process and index documents in Chroma"""
        try:
            if not self.embeddings:
                raise ValueError("Embedding model not available. Check that sentence-transformers is properly installed.")
                
            logging.info(f"Processing {len(documents)} documents")
            start_time = time.time()
            
            # Reset for new processing
            self.titles = []
            self.document_metadata = {}
            
            # Import here to handle import errors
            try:
                from langchain_community.vectorstores import Chroma
                from langchain_core.documents import Document
            except ImportError as e:
                logging.error(f"Failed to import required modules: {str(e)}")
                raise ImportError(f"Failed to import required modules: {str(e)}")
            
            # Prepare documents for LangChain
            processed_docs = []
            
            for doc_idx, doc in enumerate(documents):
                title = doc.get('title', 'Untitled Document')
                text = doc.get('text', '')
                
                # Store title
                self.titles.append(title)
                
                if not text:
                    logging.warning(f"Document '{title}' has no text content")
                    continue
                
                # Generate unique document ID
                doc_id = f"doc_{doc_idx}_{uuid.uuid4().hex[:8]}"
                
                # Store metadata
                self.document_metadata[doc_id] = {
                    'title': title,
                    'doc_index': doc_idx
                }
                
                # Split document into chunks
                try:
                    chunks = self.text_splitter.split_text(text)
                    logging.info(f"Split '{title}' into {len(chunks)} chunks")
                    
                    # Create LangChain documents
                    for i, chunk in enumerate(chunks):
                        processed_docs.append(
                            Document(
                                page_content=chunk,
                                metadata={
                                    "title": title,
                                    "doc_id": doc_id,
                                    "chunk_id": i,
                                    "source": f"{title} (Part {i+1})"
                                }
                            )
                        )
                except Exception as e:
                    logging.error(f"Error splitting document '{title}': {str(e)}")
            
            if processed_docs:
                # Initialize Chroma with these documents
                self.vector_store = Chroma.from_documents(
                    documents=processed_docs,
                    embedding=self.embeddings,
                    persist_directory=self.persist_directory
                )
                
                # Persist the database
                if self.persist_directory:
                    self.vector_store.persist()
                    self.save_metadata()
                    logging.info(f"Persisted Chroma DB to {self.persist_directory}")
            
            self.ready = True
            elapsed_time = time.time() - start_time
            logging.info(f"Indexing completed in {elapsed_time:.2f}s. {len(processed_docs)} chunks indexed")
            
            # Call completion callback
            if on_complete:
                on_complete(True)
                
        except Exception as e:
            logging.error(f"Error processing documents: {str(e)}")
            if on_complete:
                on_complete(False)
    
    def retrieve_relevant_documents(self, query, top_k=5):
        """Retrieve relevant documents using vector similarity"""
        if not self.ready or not self.vector_store:
            return []
        
        try:
            # Search documents similar to query
            results = self.vector_store.similarity_search_with_relevance_scores(
                query=query, 
                k=top_k
            )
            
            # Format results
            relevant_docs = []
            for doc, score in results:
                relevant_docs.append({
                    'title': doc.metadata.get('source', 'Unknown'),
                    'text': doc.page_content,
                    'score': score,
                    'doc_id': doc.metadata.get('doc_id', ''),
                    'doc_title': doc.metadata.get('title', 'Unknown')
                })
            
            return relevant_docs
            
        except Exception as e:
            logging.error(f"Error retrieving documents: {str(e)}")
            return []
    
    def is_ready(self):
        """Check if system is ready to process queries"""
        return self.ready and self.vector_store is not None
    
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
            relevant_chunks = self.retrieve_relevant_documents(query, top_k=5)
            
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
                "You are a helpful assistant answering questions about scientific documents in French. "
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
            prompt = f"""You are a helpful assistant answering questions about scientific documents in French.
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