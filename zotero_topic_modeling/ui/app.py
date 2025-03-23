import tkinter as tk
from tkinter import ttk, messagebox, StringVar, BooleanVar
import logging
import os
import requests

from zotero_topic_modeling.utils.zotero_client import ZoteroClient
from zotero_topic_modeling.utils.config_manager import ConfigManager
from zotero_topic_modeling.ui.components import TopicModelingThread
from zotero_topic_modeling.ui.theme import DarkTheme
from zotero_topic_modeling.utils.language_config import LanguageManager
from zotero_topic_modeling.ui.chat_window import ChatWindow
from zotero_topic_modeling.pdf_processor.extractor import PDFExtractor

class ZoteroTopicModelingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Zotero Topic Modeling")
        self.root.geometry("1000x600")  # Reduced height since we're removing visualization
        
        # Initialize variables before creating UI
        self.init_variables()
        
        # Apply theme
        self.theme = DarkTheme()
        self.colors = self.theme.apply(root)
        
        self.main_frame = ttk.Frame(root, padding="10", style='Main.TFrame')
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        
        # Initialize managers and data containers
        self.config_manager = ConfigManager()
        self.language_manager = LanguageManager()
        self.zotero_client = None
        self.collections = None
        self.items = None  # Store collection items
        self.current_collection = None  # Store current collection info
        self.chat_window = None  # Will store chat window reference
        
        # Variables to store model results
        self.lda_model = None
        self.dictionary = None
        self.corpus = None
        self.processed_texts = None
        self.document_titles = None
        
        # Setup UI after variables are initialized
        self.setup_ui()
        self.load_saved_credentials()
        self.check_ollama_availability()
        
        logging.info("Application initialized")

    def init_variables(self):
        """Initialize all tkinter variables"""
        self.library_id_var = tk.StringVar()
        self.api_key_var = tk.StringVar()
        self.save_credentials_var = tk.BooleanVar(value=True)
        self.status_var = tk.StringVar()
        self.progress_var = tk.DoubleVar()
        self.language_var = tk.StringVar(value="English")  # Default language
        self.num_topics_var = tk.IntVar(value=5)  # Default number of topics
        
        # Ollama variables
        self.use_ollama_var = tk.BooleanVar(value=False)
        self.ollama_available = False
        self.ollama_model_var = tk.StringVar(value="llama3.2:3b")
        self.available_ollama_models = []

    def check_ollama_availability(self):
        """Check if Ollama is available and get available models"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            
            if response.status_code == 200:
                self.ollama_available = True
                models = response.json().get('models', [])
                self.available_ollama_models = [model.get('name') for model in models]
                
                # Update the UI
                if hasattr(self, 'ollama_checkbox'):
                    self.ollama_checkbox.config(state='normal')
                    
                    # If we have models, update the combobox
                    if hasattr(self, 'ollama_model_combo') and self.available_ollama_models:
                        self.ollama_model_combo['values'] = self.available_ollama_models
                        
                logging.info(f"Ollama available with models: {self.available_ollama_models}")
            else:
                self.ollama_available = False
                logging.warning(f"Ollama check failed with status code: {response.status_code}")
        except requests.RequestException:
            self.ollama_available = False
            logging.info("Ollama not available")

    def setup_ui(self):
        """Setup the user interface"""
        # Credentials Frame
        cred_frame = ttk.LabelFrame(self.main_frame, text="Zotero Credentials", padding="5")
        cred_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Library ID input
        ttk.Label(cred_frame, text="Library ID:").grid(row=0, column=0, sticky=tk.W)
        self.library_id_entry = ttk.Entry(cred_frame, textvariable=self.library_id_var, width=40)
        self.library_id_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Label(cred_frame, text="(Find this in Settings → Feeds/API)").grid(row=0, column=2, sticky=tk.W)
        
        # API Key input
        ttk.Label(cred_frame, text="API Key:").grid(row=1, column=0, sticky=tk.W)
        self.api_key_entry = ttk.Entry(cred_frame, textvariable=self.api_key_var, width=40)
        self.api_key_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Label(cred_frame, text="(Find this in Settings → Feeds/API)").grid(row=1, column=2, sticky=tk.W)
        
        # Save credentials checkbox
        ttk.Checkbutton(cred_frame, text="Save credentials", 
                       variable=self.save_credentials_var,
                       style='TCheckbutton').grid(row=2, column=1, sticky=tk.W)
        
        # Buttons frame
        button_frame = ttk.Frame(cred_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=10)
        
        # Clear credentials button
        self.clear_button = ttk.Button(button_frame, text="Clear Saved Credentials", 
                                     command=self.clear_credentials)
        self.clear_button.pack(side=tk.LEFT, padx=5)
        
        # Connect button
        self.connect_button = ttk.Button(button_frame, text="Connect to Zotero", 
                                       command=self.connect_to_zotero)
        self.connect_button.pack(side=tk.LEFT, padx=5)
        
        # Collection selection frame with tree
        collection_frame = ttk.LabelFrame(self.main_frame, text="Collection Selection", padding="5")
        collection_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        collection_frame.columnconfigure(0, weight=1)
        collection_frame.rowconfigure(0, weight=1)

        # Create tree view for collections
        self.collection_tree = ttk.Treeview(collection_frame, show='tree', selectmode='browse', height=8)
        self.collection_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)

        # Add scrollbar for tree
        tree_scroll = ttk.Scrollbar(collection_frame, orient="vertical", command=self.collection_tree.yview)
        tree_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.collection_tree.configure(yscrollcommand=tree_scroll.set)

        # Analysis settings frame
        settings_frame = ttk.LabelFrame(collection_frame, text="Analysis Settings", padding="5")
        settings_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # Language selection
        ttk.Label(settings_frame, text="Document Language:").grid(row=0, column=0, sticky=tk.W)
        self.language_combobox = ttk.Combobox(
            settings_frame,
            textvariable=self.language_var,
            values=self.language_manager.get_language_names(),
            state='readonly',
            width=20
        )
        self.language_combobox.grid(row=0, column=1, padx=5)

        # Number of topics
        ttk.Label(settings_frame, text="Number of Topics:").grid(row=0, column=2, sticky=tk.W, padx=(20,0))
        topics_spinbox = ttk.Spinbox(
            settings_frame,
            from_=2,
            to=20,
            textvariable=self.num_topics_var,
            width=5
        )
        topics_spinbox.grid(row=0, column=3, padx=5)

        # Chat settings frame
        chat_settings_frame = ttk.LabelFrame(collection_frame, text="Chat Settings", padding="5")
        chat_settings_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # Ollama checkbox
        self.ollama_checkbox = ttk.Checkbutton(
            chat_settings_frame, 
            text="Use local Ollama model", 
            variable=self.use_ollama_var,
            command=self.toggle_ollama,
            state='disabled' if not self.ollama_available else 'normal'
        )
        self.ollama_checkbox.grid(row=0, column=0, sticky=tk.W, padx=5)

        # Ollama model selection
        ttk.Label(chat_settings_frame, text="Model:").grid(row=0, column=1, sticky=tk.W, padx=(20,0))
        self.ollama_model_combo = ttk.Combobox(
            chat_settings_frame,
            textvariable=self.ollama_model_var,
            values=self.available_ollama_models if self.available_ollama_models else ["llama3.2:3b"],
            state='disabled',
            width=20
        )
        self.ollama_model_combo.grid(row=0, column=2, padx=5)

        # Buttons frame for process and visualization
        action_frame = ttk.Frame(collection_frame)
        action_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        # Process button
        self.process_button = ttk.Button(action_frame, text="Process Selected Collection", 
                                       command=self.process_pdfs,
                                       state='disabled')
        self.process_button.pack(side=tk.LEFT, padx=5)
        
        # View Topics button
        self.vis_button = ttk.Button(action_frame, text="View Topic Visualization", 
                                   command=self.show_topic_visualization,
                                   state='disabled')
        self.vis_button.pack(side=tk.LEFT, padx=5)
        
        # Chat button
        self.chat_button = ttk.Button(action_frame, text="Speak with your PDFs", 
                                    command=self.open_chat_window,
                                    state='disabled')
        self.chat_button.pack(side=tk.LEFT, padx=5)
        
        # Progress frame
        progress_frame = ttk.LabelFrame(self.main_frame, text="Progress", padding="5")
        progress_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Status label
        self.status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        self.status_label.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=2)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(progress_frame, 
                                          variable=self.progress_var,
                                          maximum=100,
                                          mode='determinate')
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Configure main frame row weights
        self.main_frame.rowconfigure(1, weight=1)  # Make collection frame expandable
        
        # Bind tree selection event
        self.collection_tree.bind('<<TreeviewSelect>>', self.on_collection_select)
        
        logging.info("UI setup completed")

    def toggle_ollama(self):
        """Handle toggling Ollama checkbox"""
        if self.use_ollama_var.get():
            # Check if Ollama is running
            if not self.ollama_available:
                try:
                    response = requests.get("http://localhost:11434/api/tags", timeout=5)
                    if response.status_code == 200:
                        self.ollama_available = True
                        models = response.json().get('models', [])
                        self.available_ollama_models = [model.get('name') for model in models]
                        
                        # Update combobox values
                        self.ollama_model_combo['values'] = self.available_ollama_models
                        
                        # Enable combobox
                        self.ollama_model_combo.config(state='readonly')
                    else:
                        messagebox.showwarning(
                            "Ollama Not Available", 
                            "Could not connect to Ollama. Make sure Ollama is running."
                        )
                        self.use_ollama_var.set(False)
                except requests.RequestException:
                    messagebox.showwarning(
                        "Ollama Not Available", 
                        "Could not connect to Ollama. Make sure Ollama is running at http://localhost:11434."
                    )
                    self.use_ollama_var.set(False)
            else:
                # Enable combobox
                self.ollama_model_combo.config(state='readonly')
        else:
            # Disable combobox
            self.ollama_model_combo.config(state='disabled')

    def clear_credentials(self):
        """Clear saved credentials and current entries"""
        try:
            # Remove saved credentials file
            if hasattr(self.config_manager, 'config_file'):
                if self.config_manager.config_file.exists():
                    os.remove(self.config_manager.config_file)
            
            # Clear entry fields
            self.library_id_var.set("")
            self.api_key_var.set("")
            
            # Reset UI state
            self.collection_tree.delete(*self.collection_tree.get_children())
            self.process_button['state'] = 'disabled'
            self.chat_button['state'] = 'disabled'
            self.vis_button['state'] = 'disabled'
            
            # Clear collections
            self.collections = None
            self.zotero_client = None

            # Clear items
            self.clear_items()
            
            logging.info("Credentials cleared successfully")
            messagebox.showinfo("Success", "Saved credentials have been cleared")
            
        except Exception as e:
            logging.error(f"Error clearing credentials: {str(e)}")
            messagebox.showerror("Error", "Failed to clear credentials")

    def load_saved_credentials(self):
        """Load saved credentials if they exist"""
        library_id, api_key = self.config_manager.load_credentials()
        if library_id and api_key:
            self.library_id_var.set(library_id)
            self.api_key_var.set(api_key)
            logging.info("Saved credentials loaded")

    def populate_collection_tree(self):
        """Populate the collection tree with hierarchical data"""
        # Clear existing items
        for item in self.collection_tree.get_children():
            self.collection_tree.delete(item)

        if not self.collections:
            return

        # Create a dictionary to store parent-child relationships
        collection_dict = {}
        for collection in self.collections:
            key = collection['key']
            parent = collection.get('data', {}).get('parentCollection', '')
            name = collection.get('data', {}).get('name', '')
            collection_dict[key] = {
                'name': name,
                'parent': parent,
                'data': collection
            }

        # Function to recursively add items
        def add_collection(key, parent=''):
            collection = collection_dict.get(key)
            if collection:
                # Insert the item with full collection data stored in values
                tree_id = self.collection_tree.insert(
                    parent if parent else '', 
                    'end',
                    text=collection['name'],
                    values=(key,)  # Store collection key in values
                )
                
                # Find and add children
                children = [k for k, v in collection_dict.items() 
                          if v['parent'] == key]
                for child in sorted(children, key=lambda k: collection_dict[k]['name']):
                    add_collection(child, tree_id)

        # Add all top-level collections first
        root_collections = [(k, v) for k, v in collection_dict.items() 
                          if not v['parent']]
        # Sort root collections by name
        root_collections.sort(key=lambda x: x[1]['name'])
        for key, _ in root_collections:
            add_collection(key)

    def on_collection_select(self, event):
        """Handle collection selection"""
        selection = self.collection_tree.selection()
        if selection:
            # Enable process button when a collection is selected
            self.process_button['state'] = 'normal'
        else:
            self.process_button['state'] = 'disabled'

    def connect_to_zotero(self):
        """Connect to Zotero API and load collections"""
        library_id = self.library_id_var.get().strip()
        api_key = self.api_key_var.get().strip()
        
        if not library_id or not api_key:
            logging.warning("Missing credentials")
            messagebox.showerror("Error", "Please enter both Library ID and API Key")
            return
            
        try:
            logging.info("Attempting to connect to Zotero")
            self.zotero_client = ZoteroClient(library_id, api_key)
            
            # Test the connection by getting collections
            self.collections = self.zotero_client.get_collections()
            
            # Save credentials if checkbox is checked
            if self.save_credentials_var.get():
                if self.config_manager.save_credentials(library_id, api_key):
                    logging.info("Credentials saved successfully")
                else:
                    logging.warning("Failed to save credentials")
            
            # Populate collection tree
            self.populate_collection_tree()
            
            logging.info("Successfully connected to Zotero")
            messagebox.showinfo("Success", "Connected to Zotero successfully!")
            
        except Exception as e:
            error_msg = str(e)
            if "Forbidden" in error_msg:
                error_msg = ("Connection failed. Please verify:\n\n"
                           "1. Your Library ID is correct\n"
                           "2. Your API key is correct\n"
                           "3. You have enabled API access in Zotero settings")
            logging.error(f"Connection failed: {error_msg}")
            messagebox.showerror("Error", error_msg)

    def update_progress(self, value, status_text=""):
        """Update progress bar and status text"""
        self.progress_var.set(value)
        self.status_var.set(status_text)

    def clear_items(self):
        """Clear current items and collection data"""
        self.items = None
        self.current_collection = None
        
        # Clear model data
        self.lda_model = None
        self.dictionary = None
        self.corpus = None
        self.processed_texts = None
        self.document_titles = None

    def process_pdfs(self):
        """Process PDFs from selected collection"""
        if not self.zotero_client:
            return
            
        selection = self.collection_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a collection")
            return
            
        try:
            # Get collection key from tree item values
            collection_key = self.collection_tree.item(selection[0])['values'][0]
            self.current_collection = next((c for c in self.collections if c['key'] == collection_key), None)
            
            if not self.current_collection:
                return
                
            collection_name = self.current_collection.get('data', {}).get('name', 'Unknown Collection')
            logging.info(f"Getting items from collection: {collection_name}")
            
            # Store items as instance variable
            self.items = self.zotero_client.get_collection_items(collection_key)
            
            if not self.items:
                logging.warning("No items found in collection")
                messagebox.showwarning("Warning", "No items found in this collection")
                return
            
            # Get selected language configuration
            selected_language = self.language_var.get()
            language_config = self.language_manager.get_language_by_name(selected_language)
            
            # Disable UI elements
            self.process_button['state'] = 'disabled'
            self.chat_button['state'] = 'disabled'
            self.vis_button['state'] = 'disabled'
            self.collection_tree.unbind('<<TreeviewSelect>>')
            
            # Start processing thread
            self.progress_var.set(0)
            self.status_var.set("Starting processing...")
            
            logging.info(f"Starting processing of {len(self.items)} items")
            
            thread = TopicModelingThread(
                self.zotero_client, 
                self.items,
                self.on_processing_complete, 
                self.update_progress,
                language_config,
                self.num_topics_var.get()
            )
            thread.start()
            
        except Exception as e:
            logging.error(f"Failed to get collection items: {str(e)}")
            messagebox.showerror("Error", f"Failed to get collection items: {str(e)}")
            
            # Re-enable UI elements
            self.process_button['state'] = 'normal'
            self.collection_tree.bind('<<TreeviewSelect>>', self.on_collection_select)

    def on_processing_complete(self, lda_model, dictionary, corpus, texts, titles, failed_titles, error=None):
        """Handle completion of PDF processing and topic modeling"""
        if error:
            logging.error(f"Processing failed: {error}")
            messagebox.showerror("Error", f"Processing failed: {error}")
            self.process_button['state'] = 'normal'
            self.collection_tree.bind('<<TreeviewSelect>>', self.on_collection_select)
            return
            
        # Store the model results
        self.lda_model = lda_model
        self.dictionary = dictionary
        self.corpus = corpus
        self.processed_texts = texts
        self.document_titles = titles
        
        # Re-enable UI elements
        self.process_button['state'] = 'normal'
        self.chat_button['state'] = 'normal'  # Enable chat button after processing
        self.vis_button['state'] = 'normal'   # Enable visualization button after processing
        self.collection_tree.bind('<<TreeviewSelect>>', self.on_collection_select)
        
        try:
            # Show summary
            summary = (f"Successfully processed {len(texts)} documents:\n"
                      f"- Found {len(dictionary)} unique terms\n"
                      f"- Generated {lda_model.num_topics} topics\n\n"
                      f"Failed items:\n"
                      f"{chr(10).join('- ' + title for title in failed_titles)}" if failed_titles else "None")
            
            logging.info(f"Processing complete. Processed {len(texts)} documents.")
            messagebox.showinfo("Processing Complete", summary)
            
        except Exception as e:
            logging.error(f"Error in processing completion: {str(e)}")
            messagebox.showerror("Error", f"Error: {str(e)}")

    def show_topic_visualization(self):
        """Show the topic modeling visualization in a separate window"""
        if not all([self.lda_model, self.dictionary, self.corpus, self.document_titles]):
            messagebox.showwarning("Warning", "Please process a collection first")
            return
            
        try:
            # Import results window here to avoid circular imports
            from zotero_topic_modeling.ui.results_window import TopicModelingResults
            
            # Create and show the results window
            results_window = TopicModelingResults(
                self.root,
                self.lda_model,
                self.dictionary,
                self.corpus,
                self.document_titles,
                self.items,
                self.colors
            )
            
        except Exception as e:
            logging.error(f"Error showing visualization: {str(e)}")
            messagebox.showerror("Error", f"Error showing visualization: {str(e)}")

    def open_chat_window(self):
        """Open the chat window for RAG-based conversation with PDFs"""
        if not hasattr(self, 'items') or not self.items:
            messagebox.showwarning("Warning", "Please process a collection first")
            return
            
        try:
            # Convert processed PDFs into the format needed for RAG
            documents = []
            for i, item in enumerate(self.items):
                title = item.get('data', {}).get('title', f'Document {i+1}')
                # Get PDF content
                pdf_content = self.zotero_client.get_item_pdfs(item)
                if pdf_content:
                    # Extract text
                    text = PDFExtractor.extract_text_from_pdf(pdf_content)
                    
                    if text and PDFExtractor.is_valid_text(text):
                        # Get metadata
                        data = item.get('data', {})
                        year = data.get('date', '')[:4] if data.get('date') else ''
                        
                        # Get authors
                        authors = []
                        creators = data.get('creators', [])
                        for creator in creators:
                            if creator.get('creatorType') == 'author':
                                first_name = creator.get('firstName', '')
                                last_name = creator.get('lastName', '')
                                if first_name and last_name:
                                    authors.append(f"{first_name} {last_name}")
                                elif last_name:
                                    authors.append(last_name)
                        
                        # Add document
                        documents.append({
                            'id': item.get('key', ''),
                            'title': title,
                            'text': text,
                            'authors': authors,
                            'year': year,
                            'source': 'Zotero Library'
                        })
            
            if not documents:
                messagebox.showwarning("Warning", "No valid PDF content found in the processed collection")
                return
                
            # Show informational message
            messagebox.showinfo("Chat Window", 
                              "Opening chat window. The system will first process your documents, "
                              "which may take a few moments depending on the number and size of PDFs.")
            
            # Check if we should use Ollama
            use_ollama = self.use_ollama_var.get()
            ollama_model = self.ollama_model_var.get()
            
            # Get API key if not using Ollama
            api_key = None if use_ollama else (self.api_key_var.get() or os.environ.get("ANTHROPIC_API_KEY"))
            
            # Open the chat window
            self.chat_window = ChatWindow(
                self.root, 
                documents, 
                api_key=api_key, 
                use_ollama=use_ollama,
                ollama_model=ollama_model,
                theme_colors=self.colors
            )
            
        except Exception as e:
            logging.error(f"Error opening chat window: {str(e)}")
            messagebox.showerror("Error", f"Error opening chat window: {str(e)}")
