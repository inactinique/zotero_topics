# Fichier: zotero_topic_modeling/rag/langchain_rag_manager.py

import logging
import threading
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional
import requests
import uuid
import time

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

class LangChainRAGManager:
    """
    Gestionnaire RAG utilisant LangChain et FAISS pour la recherche vectorielle.
    """
    
    def __init__(self, api_key=None, use_ollama=False, ollama_model="llama3.2:3b", 
                 embedding_model_name="all-MiniLM-L6-v2", persist_directory=None,
                 temperature=0.7, top_k=40, top_p=0.9):
        """
        Initialise le gestionnaire RAG avec LangChain.
        
        Args:
            api_key: Clé API Anthropic (optionnelle si Ollama est utilisé)
            use_ollama: Utiliser Ollama plutôt que l'API Anthropic
            ollama_model: Nom du modèle Ollama à utiliser
            embedding_model_name: Modèle d'embeddings à utiliser
            persist_directory: Répertoire où stocker l'index vectoriel
            temperature, top_k, top_p: Paramètres de génération
        """
        # Paramètres du modèle de génération
        self.api_key = api_key
        self.use_ollama = use_ollama
        self.ollama_model = ollama_model
        self.temperature = temperature
        self.top_k = top_k
        self.top_p = top_p
        
        # Paramètres de l'index vectoriel
        self.embedding_model_name = embedding_model_name
        self.persist_directory = persist_directory
        if persist_directory and not os.path.exists(persist_directory):
            os.makedirs(persist_directory)
        
        # Initialisation du modèle d'embeddings
        try:
            self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model_name)
            logging.info(f"Modèle d'embeddings '{embedding_model_name}' chargé avec succès")
        except Exception as e:
            logging.error(f"Erreur lors du chargement du modèle d'embeddings: {str(e)}")
            self.embeddings = None
        
        # Initialisation du diviseur de texte
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Base de données vectorielle
        self.vector_store = None
        
        # Sauvegarde des documents et métadonnées
        self.document_metadata = {}
        self.titles = []
        
        # État
        self.ready = False
        
        # Endpoints API
        self.anthropic_endpoint = "https://api.anthropic.com/v1/messages"
        self.ollama_endpoint = "http://localhost:11434/api/generate"
        
        # Chargement de l'index existant si disponible
        if self.persist_directory and os.path.exists(os.path.join(self.persist_directory, "index.faiss")):
            try:
                self.load_vector_store()
            except Exception as e:
                logging.error(f"Erreur lors du chargement de l'index vectoriel: {str(e)}")
        
        logging.info(f"LangChainRAGManager initialisé avec le modèle d'embeddings {embedding_model_name}")
    
    def load_vector_store(self):
        """Charger l'index vectoriel existant"""
        if not self.embeddings:
            logging.error("Impossible de charger l'index vectoriel: modèle d'embeddings non initialisé")
            return False
            
        try:
            self.vector_store = FAISS.load_local(self.persist_directory, self.embeddings)
            logging.info(f"Index vectoriel chargé depuis {self.persist_directory}")
            
            # Charger les métadonnées si disponibles
            metadata_path = os.path.join(self.persist_directory, "metadata.json")
            if os.path.exists(metadata_path):
                import json
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    saved_data = json.load(f)
                    self.document_metadata = saved_data.get('document_metadata', {})
                    self.titles = saved_data.get('titles', [])
                logging.info(f"Métadonnées chargées: {len(self.titles)} documents")
            
            self.ready = True
            return True
        except Exception as e:
            logging.error(f"Erreur lors du chargement de l'index vectoriel: {str(e)}")
            return False
    
    def save_metadata(self):
        """Sauvegarder les métadonnées des documents"""
        if not self.persist_directory:
            return
            
        try:
            import json
            metadata_path = os.path.join(self.persist_directory, "metadata.json")
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'document_metadata': self.document_metadata,
                    'titles': self.titles
                }, f, ensure_ascii=False, indent=2)
            logging.info(f"Métadonnées sauvegardées dans {metadata_path}")
        except Exception as e:
            logging.error(f"Erreur lors de la sauvegarde des métadonnées: {str(e)}")
    
    def process_documents(self, documents, on_complete=None):
        """
        Traiter les documents en arrière-plan
        
        Args:
            documents: Liste de dictionnaires de documents
            on_complete: Fonction de rappel à appeler lorsque le traitement est terminé
        """
        threading.Thread(
            target=self._process_documents_thread,
            args=(documents, on_complete),
            daemon=True
        ).start()
    
    def _process_documents_thread(self, documents, on_complete=None):
        """Traiter les documents et les indexer avec FAISS"""
        try:
            if not self.embeddings:
                raise ValueError("Le modèle d'embeddings n'est pas disponible")
                
            logging.info(f"Traitement de {len(documents)} documents")
            start_time = time.time()
            
            # Réinitialiser les listes pour un nouveau traitement
            self.titles = []
            self.document_metadata = {}
            
            # Préparation des documents pour LangChain
            langchain_docs = []
            
            for doc_idx, doc in enumerate(documents):
                title = doc.get('title', 'Document sans titre')
                text = doc.get('text', '')
                
                # Ajouter le titre à la liste
                self.titles.append(title)
                
                if not text:
                    logging.warning(f"Document '{title}' n'a pas de contenu textuel")
                    continue
                
                # Générer un ID unique pour ce document
                doc_id = f"doc_{doc_idx}_{uuid.uuid4().hex[:8]}"
                
                # Stocker les métadonnées
                self.document_metadata[doc_id] = {
                    'title': title,
                    'doc_index': doc_idx
                }
                
                # Diviser le document en segments
                try:
                    chunks = self.text_splitter.split_text(text)
                    logging.info(f"Document '{title}' divisé en {len(chunks)} segments")
                    
                    # Créer des documents LangChain
                    for i, chunk in enumerate(chunks):
                        langchain_docs.append({
                            "page_content": chunk,
                            "metadata": {
                                "title": title,
                                "doc_id": doc_id,
                                "chunk_id": i,
                                "source": f"{title} (Partie {i+1})"
                            }
                        })
                except Exception as e:
                    logging.error(f"Erreur lors de la division du document '{title}': {str(e)}")
            
            if langchain_docs:
                # Convertir en format attendu par FAISS
                from langchain_core.documents import Document
                docs = [Document(page_content=d["page_content"], metadata=d["metadata"]) for d in langchain_docs]
                
                # Créer un nouvel index vectoriel
                self.vector_store = FAISS.from_documents(
                    docs,
                    self.embeddings
                )
                
                # Sauvegarder l'index si un répertoire est spécifié
                if self.persist_directory:
                    self.vector_store.save_local(self.persist_directory)
                    self.save_metadata()
                    logging.info(f"Index vectoriel sauvegardé dans {self.persist_directory}")
            
            self.ready = True
            elapsed_time = time.time() - start_time
            logging.info(f"Indexation terminée en {elapsed_time:.2f}s. {len(langchain_docs)} segments indexés.")
            
            # Appeler le callback de complétion
            if on_complete:
                on_complete(True)
                
        except Exception as e:
            logging.error(f"Erreur de traitement des documents: {str(e)}")
            if on_complete:
                on_complete(False)
    
    def retrieve_relevant_documents(self, query, top_k=5):
        """
        Récupérer les documents les plus pertinents pour une requête
        en utilisant la recherche vectorielle.
        
        Args:
            query: Requête de l'utilisateur
            top_k: Nombre de documents à récupérer
            
        Returns:
            Liste de dictionnaires contenant les documents pertinents
        """
        if not self.ready or not self.vector_store:
            return []
        
        try:
            # Rechercher dans FAISS
            docs_with_scores = self.vector_store.similarity_search_with_score(query, k=top_k)
            
            # Formater les résultats
            relevant_docs = []
            for doc, score in docs_with_scores:
                # Convertir le score de distance en score de similarité (plus petit = plus similaire)
                similarity_score = 1.0 / (1.0 + score)
                
                relevant_docs.append({
                    'title': doc.metadata.get('source', 'Inconnu'),
                    'text': doc.page_content,
                    'score': similarity_score,
                    'doc_id': doc.metadata.get('doc_id', ''),
                    'doc_title': doc.metadata.get('title', 'Inconnu')
                })
            
            return relevant_docs
            
        except Exception as e:
            logging.error(f"Erreur lors de la recherche vectorielle: {str(e)}")
            return []
            
    def is_ready(self):
        """Vérifie si le système est prêt à traiter des requêtes"""
        return self.ready and self.vector_store is not None
    
    def estimate_tokens(self, text):
        """
        Estime le nombre de tokens dans un texte.
        
        Args:
            text: Texte à estimer
            
        Returns:
            Nombre estimé de tokens
        """
        if not text:
            return 0
            
        # Estimation simple basée sur le nombre de caractères (4 caractères par token en moyenne)
        char_per_token = 4.0
        return int(len(text) / char_per_token)
    
    def generate_response(self, query):
        """
        Génère une réponse à la requête de l'utilisateur en utilisant RAG.
        
        Args:
            query: Requête de l'utilisateur
            
        Returns:
            Réponse générée
        """
        if not self.is_ready():
            return "Je suis encore en train de traiter vos documents. Veuillez patienter un instant."
        
        try:
            # Récupérer les documents pertinents
            relevant_chunks = self.retrieve_relevant_documents(query, top_k=5)
            
            if not relevant_chunks:
                context = "Je ne semble pas avoir suffisamment d'informations pour répondre à cette question en me basant sur les documents."
            else:
                # Préparer le contexte à partir des chunks pertinents
                context = "Voici les informations des documents pertinents:\n\n"
                
                for i, chunk in enumerate(relevant_chunks):
                    context += f"Document {i+1}: {chunk['title']}\n{chunk['text']}\n\n"
                    
                # Limiter la longueur du contexte si nécessaire
                context_tokens = self.estimate_tokens(context)
                if context_tokens > 4000:  # Limite approximative
                    context = context[:16000]  # Environ 4000 tokens
                    context += "\n\n(Certaines informations ont été tronquées en raison des limites de contexte.)"
            
            # Générer la réponse en utilisant le modèle approprié
            if self.use_ollama:
                return self._generate_ollama_response(query, context)
            else:
                return self._generate_claude_response(query, context)
                
        except Exception as e:
            logging.error(f"Erreur lors de la génération de réponse: {str(e)}")
            return f"Je suis désolé, j'ai rencontré une erreur lors de la génération d'une réponse: {str(e)}"
    
    def _generate_claude_response(self, query, context):
        """
        Génère une réponse en utilisant l'API Claude.
        
        Args:
            query: Requête de l'utilisateur
            context: Contexte pour la génération de réponse
            
        Returns:
            Réponse générée
        """
        if not self.api_key:
            return "Aucune clé API Anthropic n'a été fournie. Veuillez configurer votre clé API ou passer à Ollama."
        
        try:
            # Préparer le prompt
            system_prompt = (
                "Tu es un assistant utile qui répond aux questions sur des documents scientifiques en français. "
                "Base tes réponses uniquement sur le contexte fourni. "
                "Si tu ne connais pas la réponse, indique-le clairement. "
                "Fournis des réponses détaillées et précises, en citant les documents pertinents."
            )
            
            user_message = f"Contexte:\n{context}\n\nQuestion: {query}\nRéponds à cette question en te basant sur le contexte fourni."
            
            # Préparer la requête API
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
            
            # Appel API
            response = requests.post(
                self.anthropic_endpoint,
                headers=headers,
                json=data,
                timeout=30
            )
            
            # Traiter la réponse
            if response.status_code == 200:
                result = response.json()
                return result.get("content", [{}])[0].get("text", "Pas de réponse de l'API")
            else:
                error_msg = f"Erreur API: {response.status_code} - {response.text}"
                logging.error(error_msg)
                return f"Erreur: {error_msg}"
                
        except Exception as e:
            logging.error(f"Erreur lors de l'appel à Claude API: {str(e)}")
            return f"J'ai rencontré une erreur: {str(e)}"
    
    def _generate_ollama_response(self, query, context):
        """
        Génère une réponse en utilisant le modèle Ollama local.
        
        Args:
            query: Requête de l'utilisateur
            context: Contexte pour la génération de réponse
            
        Returns:
            Réponse générée
        """
        try:
            # Préparer le prompt
            prompt = f"""Tu es un assistant utile qui répond aux questions sur des documents scientifiques en français.
Base tes réponses uniquement sur le contexte fourni.
Si tu ne connais pas la réponse, indique-le clairement.
Fournis des réponses détaillées et précises, en citant les documents pertinents.

Contexte:
{context}

Question: {query}

Réponds à cette question en te basant sur le contexte fourni.
"""
            
            # Préparer la requête API avec les paramètres personnalisables
            data = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": 1000,  # Nombre approximatif de tokens à générer
                    "temperature": self.temperature,
                    "top_k": self.top_k,
                    "top_p": self.top_p
                }
            }
            
            # Estimation des tokens
            prompt_tokens = self.estimate_tokens(prompt)
            logging.info(f"Requête Ollama: ~{prompt_tokens} tokens dans le prompt")
            
            # Appel API
            response = requests.post(
                self.ollama_endpoint,
                json=data,
                timeout=60  # Délai plus long pour les modèles locaux
            )
            
            # Traiter la réponse
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
            logging.error(f"Erreur lors de l'appel à Ollama API: {str(e)}")
            return f"J'ai rencontré une erreur: {str(e)}"