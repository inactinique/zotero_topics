import logging
import threading
import re
from typing import List, Dict, Any, Callable, Optional, Tuple
import requests
import json
from functools import lru_cache

class RAGManager:
    """
    Manages the RAG (Retrieval-Augmented Generation) process for document Q&A.
    
    This class handles document indexing, retrieval, and response generation
    with support for both Anthropic Claude API and local Ollama models.
    """
    
    def __init__(self, api_key: Optional[str] = None, use_ollama: bool = False, 
                 ollama_model: str = "llama3.2:3b", max_context_tokens: int = 4000,
                 temperature: float = 0.7, top_k: int = 40, top_p: float = 0.9):
        """
        Initialize the RAG manager.
        
        Args:
            api_key: Anthropic API key (optional if using Ollama)
            use_ollama: Whether to use Ollama instead of Anthropic API
            ollama_model: Model name to use with Ollama
            max_context_tokens: Maximum number of tokens for context window
            temperature: Model temperature (0.0-1.0) - higher values make output more random
            top_k: Limits token selection to the top K options at each step (Ollama)
            top_p: Nucleus sampling probability threshold (0.0-1.0)
        """
        self.api_key = api_key
        self.use_ollama = use_ollama
        self.ollama_model = ollama_model
        self.max_context_tokens = max_context_tokens
        self.temperature = temperature
        self.top_k = top_k
        self.top_p = top_p
        self.ready = False
        self.document_index = []
        self.document_texts = []
        self.document_titles = []
        self.topic_info = None
        self.available_ollama_models = []
        
        # Model context limits (approximate)
        self.model_context_limits = {
            "claude-3-haiku-20240307": 200000,  # Claude 3 Haiku
            "claude-3-sonnet-20240229": 200000, # Claude 3 Sonnet
            "claude-3-opus-20240229": 200000,   # Claude 3 Opus
            "default": 4000           # Default safe value for unknown models
        }
        
        # Anthropic API endpoint
        self.anthropic_endpoint = "https://api.anthropic.com/v1/messages"
        
        # Ollama API endpoint
        self.ollama_endpoint = "http://localhost:11434/api/generate"
        
        # Try to fetch available Ollama models
        if use_ollama:
            self.fetch_available_ollama_models()
            
        logging.info(f"RAG Manager initialized (using_ollama={use_ollama}, model={ollama_model if use_ollama else 'Claude'}, max_context_tokens={max_context_tokens})")
    
    def is_ready(self) -> bool:
        """
        Check if the RAG system is ready to process queries.
        
        Returns:
            bool: True if ready, False otherwise
        """
        return self.ready
    
    def fetch_available_ollama_models(self) -> List[str]:
        """
        Fetch and store the list of available models from Ollama.
        
        Returns:
            List of model names available in Ollama
        """
        try:
            # Make a request to the Ollama API
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            
            if response.status_code == 200:
                # Extract model names from response
                models = response.json().get('models', [])
                self.available_ollama_models = [model.get('name') for model in models]
                
                # Update context limits for models
                for model_name in self.available_ollama_models:
                    # Set default context limit if we don't already have one
                    if model_name not in self.model_context_limits:
                        # Try to guess context window by model name
                        if "3.2" in model_name or "llama" in model_name:
                            self.model_context_limits[model_name] = 8000  # Llama models
                        elif "gemma" in model_name:
                            self.model_context_limits[model_name] = 8000  # Gemma models
                        elif "mistral" in model_name:
                            self.model_context_limits[model_name] = 8000  # Mistral models
                        elif "phi" in model_name:
                            self.model_context_limits[model_name] = 4000  # Phi models
                        else:
                            self.model_context_limits[model_name] = 4000  # Safe default
                
                logging.info(f"Found {len(self.available_ollama_models)} Ollama models: {', '.join(self.available_ollama_models[:5])}" + 
                           (f"... and {len(self.available_ollama_models)-5} more" if len(self.available_ollama_models) > 5 else ""))
                return self.available_ollama_models
            else:
                logging.warning(f"Failed to fetch Ollama models: {response.status_code} - {response.text}")
                return []
                
        except requests.RequestException as e:
            logging.warning(f"Ollama connection error: {str(e)}")
            return []
    
    def get_available_ollama_models(self) -> List[str]:
        """
        Get the list of available Ollama models.
        If the list is empty, try to fetch it again.
        
        Returns:
            List of model names available in Ollama
        """
        if not self.available_ollama_models:
            return self.fetch_available_ollama_models()
        return self.available_ollama_models
    
    def check_ollama_connection(self, show_warnings: bool = True) -> bool:
        """
        Check if Ollama is running and the model is available.
        
        Args:
            show_warnings: Whether to show warning dialog boxes
            
        Returns:
            True if connection and model are available, False otherwise
        """
        try:
            # Make a request to the Ollama API to check if it's running
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            
            if response.status_code != 200:
                if show_warnings:
                    from tkinter import messagebox
                    messagebox.showwarning(
                        "Ollama Connection Warning",
                        "Impossible de se connecter à Ollama. Veuillez vous assurer qu'Ollama est en cours d'exécution."
                    )
                return False
                
            # Update available models
            models = response.json().get('models', [])
            self.available_ollama_models = [model.get('name') for model in models]
            
            # Check if the model is available
            if self.ollama_model not in self.available_ollama_models:
                if show_warnings:
                    from tkinter import messagebox
                    messagebox.showwarning(
                        "Avertissement sur le modèle Ollama",
                        f"Le modèle '{self.ollama_model}' n'est pas disponible dans Ollama. "
                        f"Veuillez le télécharger avec 'ollama pull {self.ollama_model}' "
                        f"ou choisir l'un des modèles disponibles : {', '.join(self.available_ollama_models[:5])}"
                        f"{' et plus...' if len(self.available_ollama_models) > 5 else ''}"
                    )
                return False
                
            return True
            
        except requests.RequestException:
            if show_warnings:
                from tkinter import messagebox
                messagebox.showwarning(
                    "Erreur de connexion Ollama",
                    "Impossible de se connecter à Ollama. Veuillez vous assurer qu'Ollama est en cours d'exécution sur http://localhost:11434."
                )
            return False
    
    def process_documents(self, documents: List[Dict[str, Any]], 
                         on_complete: Optional[Callable[[bool], None]] = None):
        """
        Process documents for RAG.
        
        Args:
            documents: List of document dictionaries
            on_complete: Callback for when processing completes
        """
        # Process in a background thread to keep UI responsive
        threading.Thread(
            target=self._process_documents_thread,
            args=(documents, on_complete),
            daemon=True
        ).start()
    
    def _process_documents_thread(self, documents: List[Dict[str, Any]], 
                                 on_complete: Optional[Callable[[bool], None]] = None):
        """
        Background thread for document processing.
        
        Args:
            documents: List of document dictionaries
            on_complete: Callback for when processing completes
        """
        try:
            logging.info(f"Processing {len(documents)} documents")
            
            # Extract titles and texts
            for doc in documents:
                title = doc.get('title', 'Untitled Document')
                text = doc.get('text', '')
                
                if not text:
                    logging.warning(f"Document '{title}' has no text content")
                    continue
                
                # Store document in index
                self.document_titles.append(title)
                self.document_texts.append(text)
                
                # Create document index entry with metadata
                token_estimate = self.estimate_tokens(text)
                self.document_index.append({
                    'title': title,
                    'text': text[:1000],  # Store a preview of the text
                    'length': len(text),
                    'token_estimate': token_estimate,
                    'chunks': self._chunk_document(text, title)
                })
            
            # Create document embeddings (in a real implementation, this would use 
            # a text embedding model - for simplicity, we're skipping this step)
            
            # Prepare topic information (if available)
            if documents and 'topic_model' in documents[0]:
                self.topic_info = documents[0].get('topic_model')
            
            # Mark as ready
            self.ready = True
            logging.info(f"Document processing complete: {len(self.document_index)} documents indexed")
            
            # Call completion callback
            if on_complete:
                on_complete(True)
                
        except Exception as e:
            logging.error(f"Error processing documents: {str(e)}")
            if on_complete:
                on_complete(False)
    
    def _chunk_document(self, text: str, title: str, chunk_size: int = 1000, 
                       overlap: int = 200) -> List[Dict[str, Any]]:
        """
        Split a document into overlapping chunks for better retrieval.
        
        Args:
            text: Document text
            title: Document title
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks in characters
            
        Returns:
            List of chunk dictionaries
        """
        chunks = []
        
        # Check if text is long enough to chunk
        if len(text) <= chunk_size:
            return [{
                'text': text,
                'title': title,
                'chunk_id': 0,
                'token_estimate': self.estimate_tokens(text)
            }]
        
        # Split into chunks with overlap
        for i in range(0, len(text), chunk_size - overlap):
            chunk_text = text[i:i + chunk_size]
            
            # Ensure we're not cutting in the middle of a sentence if possible
            if i > 0 and i + chunk_size < len(text):
                # Find the first sentence end after the start of this chunk
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
                'chunk_id': chunk_id,
                'token_estimate': self.estimate_tokens(chunk_text)
            })
        
        return chunks
    
    @lru_cache(maxsize=10)
    def retrieve_relevant_documents(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve the most relevant documents for a query.
        
        In a real implementation, this would use vector similarity search.
        Here we're using a simple keyword-based approach for demonstration.
        
        Args:
            query: User's question
            top_k: Number of documents to retrieve
        
        Returns:
            List of relevant document dictionaries
        """
        if not self.ready or not self.document_texts:
            return []
        
        # Simple keyword matching (just for demonstration)
        # In a real application, use embeddings and vector search
        query_words = set(query.lower().split())
        
        # Score all chunks across all documents
        all_chunks = []
        for doc_idx, doc in enumerate(self.document_index):
            for chunk in doc['chunks']:
                # Count matching words
                chunk_text = chunk['text'].lower()
                score = sum(1 for word in query_words if word in chunk_text)
                
                if score > 0:
                    all_chunks.append({
                        'doc_idx': doc_idx,
                        'title': chunk['title'],
                        'text': chunk['text'],
                        'score': score,
                        'token_estimate': chunk['token_estimate']
                    })
        
        # Sort by score (descending) and take top k
        all_chunks.sort(key=lambda x: x['score'], reverse=True)
        return all_chunks[:top_k]
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in a text.
        
        This is a simple approximation. For Claude and Llama models,
        a rough estimate is ~4 characters per token for English text.
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated number of tokens
        """
        if not text:
            return 0
            
        # Simple estimation based on character count
        # A more accurate tokenizer would be model-specific
        char_per_token = 4.0
        return int(len(text) / char_per_token)
    
    def find_safe_truncation(self, text: str, max_tokens: int) -> int:
        """
        Find a safe point to truncate text without cutting words.
        
        Args:
            text: Text to truncate
            max_tokens: Maximum number of tokens to keep
            
        Returns:
            Index for safe truncation
        """
        # Estimate character position based on tokens
        char_pos = max_tokens * 4  # Using the 4 chars per token approximation
        
        # Don't exceed text length
        char_pos = min(char_pos, len(text))
        
        # Find the last sentence end before the character position
        last_part = text[:char_pos]
        match = re.search(r'[.!?]\s+[A-Z]', last_part[::-1])
        
        if match:
            # Return truncation point at the sentence end
            return char_pos - match.start()
        
        # If no sentence end found, find the last space
        last_space = last_part.rfind(' ')
        if last_space > 0:
            return last_space
            
        # Fallback to the exact character position
        return char_pos
    
    def get_model_context_limit(self) -> int:
        """
        Get the context limit for the current model.
        
        Returns:
            Maximum context size in tokens
        """
        if self.use_ollama:
            # Get limit for the specific Ollama model
            return self.model_context_limits.get(
                self.ollama_model, 
                self.model_context_limits['default']
            )
        else:
            # Claude model
            return self.model_context_limits.get(
                "claude-3-haiku-20240307", 
                self.model_context_limits['default']
            )
    
    def generate_response(self, query: str) -> str:
        """
        Generate a response to the user's query using RAG.
        
        Args:
            query: User's question
        
        Returns:
            Generated response text
        """
        if not self.ready:
            return "Je suis encore en train de traiter vos documents. Veuillez patienter un instant."
        
        try:
            # Retrieve relevant document chunks
            relevant_chunks = self.retrieve_relevant_documents(query)
            
            if not relevant_chunks:
                context = "Je ne semble pas avoir suffisamment d'informations pour répondre à cette question en me basant sur les documents."
            else:
                # Calculate available context tokens
                # Reserve tokens for the query, system prompt, and response
                model_context_limit = self.get_model_context_limit()
                query_tokens = self.estimate_tokens(query)
                system_prompt_tokens = 150  # Approximation
                response_tokens = 1000  # Reserve tokens for response
                
                # Tokens available for document context
                available_context_tokens = min(
                    self.max_context_tokens,  # User-defined limit
                    model_context_limit - query_tokens - system_prompt_tokens - response_tokens
                )
                
                # Prepare context from relevant chunks with token tracking
                context = "Voici les informations des documents pertinents:\n\n"
                current_tokens = self.estimate_tokens(context)
                
                # Add chunks until we approach the token limit
                for i, chunk in enumerate(relevant_chunks):
                    chunk_text = f"Document {i+1}: {chunk['title']}\n{chunk['text']}\n\n"
                    chunk_tokens = self.estimate_tokens(chunk_text)
                    
                    # Check if adding this chunk would exceed our limit
                    if current_tokens + chunk_tokens > available_context_tokens:
                        # Calculate how many tokens we can still add
                        remaining_tokens = available_context_tokens - current_tokens - 20  # Buffer
                        
                        if remaining_tokens > 100:  # Only add partial chunk if worth it
                            # Find a safe truncation point
                            truncation_char_pos = self.find_safe_truncation(chunk['text'], remaining_tokens)
                            truncated_text = chunk['text'][:truncation_char_pos] + "... [tronqué]"
                            
                            # Add the truncated chunk
                            context += f"Document {i+1}: {chunk['title']}\n{truncated_text}\n\n"
                        
                        # Add note about truncation
                        context += "(Certaines informations ont été tronquées en raison des limites de contexte.)"
                        break
                    
                    # Add the full chunk
                    context += chunk_text
                    current_tokens += chunk_tokens
                
                # Log context usage statistics
                context_tokens = self.estimate_tokens(context)
                logging.info(f"Context usage: {context_tokens} tokens out of {available_context_tokens} available")
            
            # Generate response
            if self.use_ollama:
                return self._generate_ollama_response(query, context)
            else:
                return self._generate_claude_response(query, context)
                
        except Exception as e:
            logging.error(f"Error generating response: {str(e)}")
            return f"Je suis désolé, j'ai rencontré une erreur lors de la génération d'une réponse: {str(e)}"
    
    def _generate_claude_response(self, query: str, context: str) -> str:
        """
        Generate a response using the Anthropic Claude API.
        
        Args:
            query: User's question
            context: Context from relevant documents
        
        Returns:
            Generated response
        """
        if not self.api_key:
            return "Aucune clé API Anthropic n'a été fournie. Veuillez configurer votre clé API ou passer à Ollama."
        
        try:
            # Prepare the prompt
            system_prompt = (
                "Tu es un assistant utile qui répond aux questions sur des documents scientifiques en français. "
                "Base tes réponses uniquement sur le contexte fourni. "
                "Si tu ne connais pas la réponse, indique-le clairement. "
                "Fournis des réponses détaillées et précises, en citant les documents pertinents."
            )
            
            user_message = f"Contexte:\n{context}\n\nQuestion: {query}\nRéponds à cette question en te basant sur le contexte fourni."
            
            # Prepare the API request
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
            
            # Make the API call
            response = requests.post(
                self.anthropic_endpoint,
                headers=headers,
                json=data,
                timeout=30
            )
            
            # Process the response
            if response.status_code == 200:
                result = response.json()
                return result.get("content", [{}])[0].get("text", "Pas de réponse de l'API")
            else:
                error_msg = f"Erreur API: {response.status_code} - {response.text}"
                logging.error(error_msg)
                return f"Erreur: {error_msg}"
                
        except Exception as e:
            logging.error(f"Error calling Claude API: {str(e)}")
            return f"J'ai rencontré une erreur: {str(e)}"
    
    def _generate_ollama_response(self, query: str, context: str) -> str:
        """
        Generate a response using the local Ollama model.
        
        Args:
            query: User's question
            context: Context from relevant documents
        
        Returns:
            Generated response
        """
        try:
            # Prepare the prompt
            prompt = f"""Tu es un assistant utile qui répond aux questions sur des documents scientifiques en français.
Base tes réponses uniquement sur le contexte fourni.
Si tu ne connais pas la réponse, indique-le clairement.
Fournis des réponses détaillées et précises, en citant les documents pertinents.

Contexte:
{context}

Question: {query}

Réponds à cette question en te basant sur le contexte fourni.
"""
            
            # Prepare the API request with customizable parameters
            data = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": 1000,  # Approximate max tokens to generate
                    "temperature": self.temperature,
                    "top_k": self.top_k,
                    "top_p": self.top_p
                }
            }
            
            # Log token usage estimate
            prompt_tokens = self.estimate_tokens(prompt)
            logging.info(f"Ollama request: ~{prompt_tokens} tokens in prompt")
            
            # Make the API call
            response = requests.post(
                self.ollama_endpoint,
                json=data,
                timeout=60  # Longer timeout for local models
            )
            
            # Process the response
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "Pas de réponse d'Ollama")
            else:
                error_msg = f"Erreur API Ollama: {response.status_code} - {response.text}"
                logging.error(error_msg)
                return f"Erreur: {error_msg}"
                
        except requests.exceptions.ConnectionError:
            return "Impossible de se connecter à Ollama. Veuillez vous assurer qu'Ollama est en cours d'exécution à l'adresse http://localhost:11434."
        except Exception as e:
            logging.error(f"Error calling Ollama API: {str(e)}")
            return f"J'ai rencontré une erreur: {str(e)}"
