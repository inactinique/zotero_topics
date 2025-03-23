import numpy as np
import logging
from typing import List, Dict, Any, Optional
import pickle
import os
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class DocumentEmbedder:
    """
    Creates and manages vector embeddings for document chunks using TF-IDF.
    This is a simpler implementation that doesn't rely on transformer models.
    """
    
    def __init__(self):
        """Initialize document embedder with TF-IDF vectorizer"""
        self.vectorizer = TfidfVectorizer(
            max_features=10000,  # Limit features for efficiency
            min_df=2,            # Ignore terms that appear in fewer than 2 documents
            max_df=0.85,         # Ignore terms that appear in more than 85% of documents
            stop_words='english',
            ngram_range=(1, 2)   # Use both unigrams and bigrams
        )
        self.embeddings = None
        self.chunks = []
        logging.info("Initialized DocumentEmbedder with TF-IDF vectorizer")
    
    def embed_chunks(self, chunks: List[Dict[str, Any]]) -> None:
        """
        Create embeddings for a list of chunks using TF-IDF.
        
        Args:
            chunks: List of chunk dictionaries with 'text' key
        """
        if not chunks:
            logging.warning("No chunks provided for embedding")
            return
            
        try:
            # Store the chunks for later retrieval
            self.chunks = chunks
            
            # Get text from each chunk for embedding
            texts = [chunk['text'] for chunk in chunks]
            
            logging.info(f"Creating TF-IDF embeddings for {len(texts)} chunks")
            self.embeddings = self.vectorizer.fit_transform(texts)
            
            logging.info(f"Created TF-IDF embeddings with shape {self.embeddings.shape}")
            
        except Exception as e:
            logging.error(f"Error embedding chunks: {str(e)}")
            raise
    
    def find_similar_chunks(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Find chunks most similar to the query using cosine similarity.
        
        Args:
            query: Query string
            k: Number of similar chunks to retrieve
            
        Returns:
            List of most similar chunk dictionaries
        """
        if self.embeddings is None or not self.chunks:
            logging.warning("No embeddings or chunks available for similarity search")
            return []
            
        try:
            # Transform query using the same vectorizer
            query_vector = self.vectorizer.transform([query])
            
            # Calculate cosine similarity between query and all chunks
            similarities = cosine_similarity(query_vector, self.embeddings).flatten()
            
            # Get indices of top k most similar chunks
            top_indices = similarities.argsort()[-k:][::-1]
            
            # Get the corresponding chunks
            similar_chunks = [self.chunks[idx] for idx in top_indices]
            
            logging.info(f"Found {len(similar_chunks)} chunks similar to query: {query[:50]}...")
            return similar_chunks
            
        except Exception as e:
            logging.error(f"Error finding similar chunks: {str(e)}")
            return []
    
    def save_embeddings(self, save_dir: str) -> bool:
        """
        Save the embeddings and chunks to disk.
        
        Args:
            save_dir: Directory to save the embeddings and chunks
            
        Returns:
            True if successful, False otherwise
        """
        if self.embeddings is None or not self.chunks:
            logging.warning("No embeddings or chunks available to save")
            return False
            
        try:
            # Create directory if it doesn't exist
            os.makedirs(save_dir, exist_ok=True)
            
            # Save the chunks
            with open(os.path.join(save_dir, 'chunks.pkl'), 'wb') as f:
                pickle.dump(self.chunks, f)
            
            # Save the vectorizer
            with open(os.path.join(save_dir, 'vectorizer.pkl'), 'wb') as f:
                pickle.dump(self.vectorizer, f)
            
            # Save the embeddings - convert to scipy sparse matrix format
            with open(os.path.join(save_dir, 'embeddings.pkl'), 'wb') as f:
                pickle.dump(self.embeddings, f)
            
            logging.info(f"Saved embeddings and chunks to {save_dir}")
            return True
            
        except Exception as e:
            logging.error(f"Error saving embeddings: {str(e)}")
            return False
    
    def load_embeddings(self, save_dir: str) -> bool:
        """
        Load embeddings and chunks from disk.
        
        Args:
            save_dir: Directory containing saved embeddings and chunks
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load the chunks
            with open(os.path.join(save_dir, 'chunks.pkl'), 'rb') as f:
                self.chunks = pickle.load(f)
            
            # Load the vectorizer
            with open(os.path.join(save_dir, 'vectorizer.pkl'), 'rb') as f:
                self.vectorizer = pickle.load(f)
            
            # Load the embeddings
            with open(os.path.join(save_dir, 'embeddings.pkl'), 'rb') as f:
                self.embeddings = pickle.load(f)
            
            logging.info(f"Loaded embeddings and {len(self.chunks)} chunks from {save_dir}")
            return True
            
        except Exception as e:
            logging.error(f"Error loading embeddings: {str(e)}")
            return False
