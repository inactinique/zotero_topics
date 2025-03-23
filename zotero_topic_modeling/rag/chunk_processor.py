import re
import logging
from typing import List, Dict, Any

class ChunkProcessor:
    """
    Processes documents into chunks suitable for embedding and retrieval.
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize chunk processor with configurable chunking parameters.
        
        Args:
            chunk_size: Target size of chunks in characters
            chunk_overlap: Overlap between consecutive chunks in characters
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        logging.info(f"Initialized ChunkProcessor with chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")
        
    def process_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process a list of documents into chunks.
        
        Args:
            documents: List of documents with text content
                Each document should have at least 'text' and 'title' keys
                
        Returns:
            List of chunks with metadata
        """
        chunks = []
        
        for doc in documents:
            doc_chunks = self.chunk_document(doc)
            chunks.extend(doc_chunks)
            
        logging.info(f"Created {len(chunks)} chunks from {len(documents)} documents")
        return chunks
    
    def chunk_document(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Split a single document into chunks.
        
        Args:
            document: Document dictionary with at least 'text' and 'title' keys
            
        Returns:
            List of chunk dictionaries with the document's text split into chunks
        """
        text = document.get('text', '')
        if not text:
            logging.warning(f"Empty text found for document: {document.get('title', 'Untitled')}")
            return []
            
        # Split the text into sentences
        sentences = self._split_into_sentences(text)
        
        # Create chunks from sentences
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_len = len(sentence)
            
            # If adding this sentence would exceed the chunk size and we already have content,
            # save the current chunk and start a new one
            if current_size + sentence_len > self.chunk_size and current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunks.append(self._create_chunk_dict(document, chunk_text, len(chunks)))
                
                # Start a new chunk with overlap
                overlap_size = 0
                new_chunk = []
                
                # Add sentences from the end of the previous chunk for overlap
                for prev_sentence in reversed(current_chunk):
                    if overlap_size + len(prev_sentence) <= self.chunk_overlap:
                        new_chunk.insert(0, prev_sentence)
                        overlap_size += len(prev_sentence)
                    else:
                        break
                
                current_chunk = new_chunk
                current_size = overlap_size
            
            # Add the current sentence to the chunk
            current_chunk.append(sentence)
            current_size += sentence_len
        
        # Add the last chunk if it contains any content
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append(self._create_chunk_dict(document, chunk_text, len(chunks)))
            
        logging.info(f"Created {len(chunks)} chunks from document: {document.get('title', 'Untitled')}")
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences, trying to preserve semantic units.
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        # Clean up the text
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Simple sentence splitting on periods, question marks and exclamation marks
        # This is a simplified approach; more sophisticated methods could be used
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        return sentences
    
    def _create_chunk_dict(self, document: Dict[str, Any], chunk_text: str, chunk_idx: int) -> Dict[str, Any]:
        """
        Create a chunk dictionary with metadata from the original document.
        
        Args:
            document: Original document dictionary
            chunk_text: Text content of the chunk
            chunk_idx: Index of the chunk within the document
            
        Returns:
            Chunk dictionary with text and metadata
        """
        return {
            'text': chunk_text,
            'document_title': document.get('title', 'Untitled'),
            'document_id': document.get('id', ''),
            'chunk_idx': chunk_idx,
            'metadata': {
                'title': document.get('title', 'Untitled'),
                'authors': document.get('authors', []),
                'year': document.get('year', ''),
                'source': document.get('source', ''),
                # Include any other relevant metadata
            }
        }
