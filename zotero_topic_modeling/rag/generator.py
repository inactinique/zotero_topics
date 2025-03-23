import logging
from typing import List, Dict, Any, Optional
import requests
import json
import os
from pathlib import Path
import re

class ResponseGenerator:
    """
    Generates responses to user questions based on retrieved document chunks.
    This is a simplified version that can work without external LLM APIs.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-haiku-20240307"):
        """
        Initialize response generator.
        
        Args:
            api_key: API key for the language model service (can be None if using local models)
            model: Model identifier to use
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model
        self.api_url = "https://api.anthropic.com/v1/messages"
        
        # Create a default system prompt
        self.system_prompt = (
            "You are a helpful research assistant. Your task is to answer questions based on the provided context from "
            "academic papers and documents. Stay factual and provide information that is supported by the context. "
            "If the context doesn't contain enough information to answer the question, say so clearly. "
            "When appropriate, cite the specific documents you're drawing information from."
        )
        
        logging.info(f"Initialized ResponseGenerator with model: {model}")
    
    def generate_response(self, query: str, chunks: List[Dict[str, Any]]) -> str:
        """
        Generate a response to a user query based on retrieved chunks.
        
        Args:
            query: User's question
            chunks: List of relevant text chunks from documents
            
        Returns:
            Generated response text
        """
        try:
            # Create context from chunks
            context = self._create_context_from_chunks(chunks)
            
            # Check if we have an API key for external services
            if self.api_key:
                return self._generate_with_api(query, context)
            else:
                return self._generate_fallback(query, context)
                
        except Exception as e:
            logging.error(f"Error generating response: {str(e)}")
            return f"I'm sorry, I couldn't generate a response due to an error: {str(e)}"
    
    def _create_context_from_chunks(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Create a context string from the retrieved chunks.
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            Context string for the response generation
        """
        if not chunks:
            return "No relevant information found."
            
        # Format each chunk with metadata
        formatted_chunks = []
        for i, chunk in enumerate(chunks):
            title = chunk.get('document_title', 'Untitled Document')
            year = chunk.get('metadata', {}).get('year', '')
            authors = ", ".join(chunk.get('metadata', {}).get('authors', []))
            
            header = f"[DOCUMENT {i+1}] {title}"
            if authors:
                header += f" by {authors}"
            if year:
                header += f" ({year})"
                
            formatted_chunks.append(f"{header}\n\n{chunk.get('text', '')}\n")
            
        return "\n\n".join(formatted_chunks)
    
    def _generate_with_api(self, query: str, context: str) -> str:
        """
        Generate a response using the Anthropic Claude API.
        
        Args:
            query: User's question
            context: Context information from chunks
            
        Returns:
            Generated response
        """
        try:
            # Create the prompt for the language model
            message_content = f"""Based on the following excerpts from academic papers and documents, please answer this question:
            
Question: {query}

Context:
{context}

Please provide a detailed answer based solely on the information in the context. If the information isn't in the context, please state that clearly.
"""
            
            # Prepare the API request with the latest Anthropic API format
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01"
            }
            
            data = {
                "model": self.model,
                "max_tokens": 1000,
                "system": self.system_prompt,
                "messages": [
                    {"role": "user", "content": message_content}
                ]
            }
            
            # Log request details for debugging (excluding API key)
            logging.info(f"Making API request to: {self.api_url}")
            logging.info(f"Using model: {self.model}")
            
            # Make the API request
            response = requests.post(self.api_url, headers=headers, data=json.dumps(data), timeout=30)
            
            # Log the response status
            logging.info(f"API response status: {response.status_code}")
            
            # Check for errors
            if response.status_code != 200:
                logging.error(f"API error: {response.status_code} {response.text}")
                return f"Error from API: {response.status_code}. Falling back to basic response generation."
            
            # Extract the generated text
            result = response.json()
            
            # The structure should be: {"content":[{"type":"text","text":"response text"}]}
            if "content" in result and isinstance(result["content"], list) and len(result["content"]) > 0:
                for content_item in result["content"]:
                    if content_item.get("type") == "text":
                        return content_item.get("text", "No response text found.")
            
            logging.warning(f"Unexpected API response structure: {result}")
            return "Unable to parse API response. Falling back to basic response generation."
            
        except requests.RequestException as e:
            logging.error(f"API request error: {str(e)}")
            return self._generate_fallback(query, context)
        except Exception as e:
            logging.error(f"Error in API response generation: {str(e)}")
            return self._generate_fallback(query, context)
    
    def _generate_fallback(self, query: str, context: str) -> str:
        """
        Generate a simple response without using an external API.
        Used as a fallback when the API isn't available.
        
        Args:
            query: User's question
            context: Context information from chunks
            
        Returns:
            A simple response based on the available context
        """
        # Extract query keywords
        query_lower = query.lower()
        query_keywords = set(re.findall(r'\b\w+\b', query_lower))
        
        # Filter out common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 
                     'in', 'on', 'at', 'to', 'for', 'with', 'by', 'about', 'like', 
                     'through', 'over', 'before', 'after', 'between', 'under', 'of', 
                     'from', 'up', 'down', 'do', 'does', 'did', 'have', 'has', 'had', 
                     'am', 'be', 'been', 'being', 'what', 'when', 'where', 'who', 
                     'why', 'how', 'which', 'there', 'can', 'could', 'should', 'would', 
                     'will', 'shall', 'may', 'might', 'must', 'that', 'these', 'those'}
        
        query_keywords = query_keywords - stop_words
        
        # Split context into paragraphs
        paragraphs = context.split('\n\n')
        relevant_paragraphs = []
        
        # Score each paragraph for relevance
        for paragraph in paragraphs:
            paragraph_lower = paragraph.lower()
            
            # Count matching keywords
            keyword_count = sum(1 for keyword in query_keywords if keyword in paragraph_lower)
            
            # Add paragraph if it contains at least one keyword
            if keyword_count > 0:
                relevant_paragraphs.append((paragraph, keyword_count))
        
        # Sort by relevance score (keyword count)
        relevant_paragraphs.sort(key=lambda x: x[1], reverse=True)
        
        # If no paragraphs are relevant, return a default message
        if not relevant_paragraphs:
            return f"I couldn't find specific information about '{query}' in the documents."
        
        # Create response
        response = f"Based on the documents I analyzed, here's what I found about '{query}':\n\n"
        
        # Take the top 3 most relevant paragraphs
        for paragraph, _ in relevant_paragraphs[:3]:
            # Extract the document title from the paragraph if available
            doc_match = re.search(r'\[DOCUMENT \d+\] (.+?)(?=\n|\()', paragraph)
            doc_title = doc_match.group(1).strip() if doc_match else "Document"
            
            # Extract a relevant snippet (up to 200 chars)
            snippet = paragraph.split('\n\n')[-1][:200] + "..."
            
            # Add to response
            response += f"• From {doc_title}: {snippet}\n\n"
        
        response += "These excerpts may address your question. If you need more specific information, please ask a more targeted question."
        
        return response
    
    def set_system_prompt(self, prompt: str) -> None:
        """
        Set a custom system prompt for the response generator.
        
        Args:
            prompt: Custom system prompt
        """
        self.system_prompt = prompt
        logging.info("Updated system prompt for response generator")
