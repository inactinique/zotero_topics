import logging
from typing import List, Dict, Any, Optional
import os
from pathlib import Path
import threading

from zotero_topic_modeling.rag.chunk_processor import ChunkProcessor
from zotero_topic_modeling.rag.embedder import DocumentEmbedder
from zotero_topic_modeling.rag.generator import ResponseGenerator

class RAGManager:
    """
    Manages the complete RAG pipeline from document processing to response generation.
    """
    
    def __init__(self, api_key: Optional[str] = None, use_ollama: bool = False, ollama_model: str = "llama3.2:3b"):
        """
        Initialize the RAG manager.
        
        Args:
            api_key: API key for the language model service (optional)
            use_ollama: Whether to use Ollama instead of Anthropic API
            ollama_model: Model to use with Ollama 
        """
        self.chunk_processor = ChunkProcessor()
        self.embedder = DocumentEmbedder()
        self.generator = ResponseGenerator(
            api_key=api_key, 
            use_ollama=use_ollama, 
            ollama_model=ollama_model
        )
        
        self.is_initialized = False
        self.is_processing = False
        self.documents = []
        
        # Set up storage directory
        self.storage_dir = os.path.join(Path.home(), '.zotero_topic_modeling', 'rag_data')
        os.makedirs(self.storage_dir, exist_ok=True)
        
        logging.info("Initialized RAG manager")
        if use_ollama:
            logging.info(f"Using Ollama with model: {ollama_model}")
        elif api_key:
            logging.info("Using Anthropic API")
        else:
            logging.info("Using fallback response generation (no API)")
    
    def process_documents(self, documents: List[Dict[str, Any]], callback: Optional[callable] = None) -> None:
        """
        Process documents through the RAG pipeline.
        
        Args:
            documents: List of document dictionaries with text content
            callback: Function to call when processing is complete
        """
        if self.is_processing:
            logging.warning("Document processing already in progress")
            return
            
        self.is_processing = True
        self.is_initialized = False
        self.documents = documents
        
        # Start processing in a separate thread
        thread = threading.Thread(
            target=self._process_documents_thread,
            args=(documents, callback)
        )
        thread.daemon = True
        thread.start()
    
    def _process_documents_thread(self, documents: List[Dict[str, Any]], callback: Optional[callable] = None) -> None:
        """
        Thread function for document processing.
        
        Args:
            documents: List of document dictionaries
            callback: Function to call when processing is complete
        """
        try:
            logging.info(f"Starting to process {len(documents)} documents")
            
            # 1. Create chunks from documents
            chunks = self.chunk_processor.process_documents(documents)
            
            # 2. Create embeddings for the chunks
            self.embedder.embed_chunks(chunks)
            
            # 3. Save the embeddings for future use
            self.embedder.save_embeddings(self.storage_dir)
            
            self.is_initialized = True
            logging.info("Document processing complete")
            
        except Exception as e:
            logging.error(f"Error in document processing: {str(e)}")
        finally:
            self.is_processing = False
            if callback:
                callback(self.is_initialized)
    
    def generate_response(self, query: str) -> str:
        """
        Generate a response to a user query.
        
        Args:
            query: User's question
            
        Returns:
            Generated response
        """
        if not self.is_initialized:
            return "I'm still processing the documents. Please wait a moment before asking questions."
            
        try:
            # 1. Find similar chunks
            similar_chunks = self.embedder.find_similar_chunks(query, k=5)
            
            # 2. Generate response based on similar chunks
            response = self.generator.generate_response(query, similar_chunks)
            
            return response
            
        except Exception as e:
            logging.error(f"Error generating response: {str(e)}")
            return f"I encountered an error while trying to answer your question: {str(e)}"
    
    def load_saved_data(self) -> bool:
        """
        Load previously saved RAG data from disk.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if the necessary files exist
            index_path = os.path.join(self.storage_dir, 'embeddings.pkl')
            chunks_path = os.path.join(self.storage_dir, 'chunks.pkl')
            
            if not os.path.exists(index_path) or not os.path.exists(chunks_path):
                logging.warning("Saved RAG data not found")
                return False
                
            # Load the data
            success = self.embedder.load_embeddings(self.storage_dir)
            
            if success:
                self.is_initialized = True
                logging.info("Successfully loaded saved RAG data")
                return True
            else:
                return False
                
        except Exception as e:
            logging.error(f"Error loading saved RAG data: {str(e)}")
            return False
    
    def is_ready(self) -> bool:
        """
        Check if the RAG system is ready to answer questions.
        
        Returns:
            True if ready, False otherwise
        """
        return self.is_initialized
    
    def get_processing_status(self) -> bool:
        """
        Check if document processing is currently in progress.
        
        Returns:
            True if processing, False otherwise
        """
        return self.is_processing
