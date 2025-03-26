import tkinter as tk
from tkinter import ttk, messagebox
import logging
import os

from zotero_topic_modeling.utils.zotero_client import ZoteroClient
from zotero_topic_modeling.utils.credential_manager import CredentialManager
from zotero_topic_modeling.ui.components import TopicModelingThread
from zotero_topic_modeling.ui.welcome_dialog import WelcomeDialog
from zotero_topic_modeling.ui.chat_window import ChatWindow
from zotero_topic_modeling.ui.theme import DarkTheme
from zotero_topic_modeling.utils.language_config import LanguageManager

class ZoteroTopicModelingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Zotero Topic Modeling")
        self.root.geometry("1000x800")
        
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
        self.credential_manager = CredentialManager()
        self.language_manager = LanguageManager()
        self.zotero_client = None
        self.collections = None
        self.items = None  # Store collection items
        self.current_collection = None  # Store current collection info
        
        # Topic modeling results
        self.lda_model = None
        self.dictionary = None
        self.corpus = None
        self.processed_texts = None
        self.processed_titles = None
        
        # Setup UI after variables are initialized
        self.setup_ui()
        
        # Show welcome dialog if not initialized
        if not self.credential_manager.initialized:
            self.show_welcome_dialog()
        else:
            # If initialized, connect automatically
            self.connect_to_zotero()
        
        logging.info("Application initialized")

    def init_variables(self):
        """Initialize all tkinter variables"""
        self.status_var = tk.StringVar()
        self.progress_var = tk.DoubleVar()
        self.language_var = tk.StringVar(value="English")  # Default language
        self.num_topics_var = tk.IntVar(value=5)  # Default number of topics
        self.use_ollama_var = tk.BooleanVar(value=False)  # Whether to use Ollama
        self.ollama_model_var = tk.StringVar(value="llama3.2:3b")  # Default Ollama model

    def setup_ui(self):
        """Setup the user interface"""
        # Header frame with connection status and manage credentials button
        header_frame = ttk.Frame(self.main_frame)
        header_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Connection status
        self.connection_status = ttk.Label(
            header_frame, 
            text="Not connected to Zotero", 
            foreground="orange"
        )
        self.connection_status.pack(side=tk.LEFT, padx=5)
        
        # Create a frame for the buttons on the right
        buttons_frame = ttk.Frame(header_frame)
        buttons_frame.pack(side=tk.RIGHT, padx=5)
        
        # Manage credentials button
        self.manage_creds_button = ttk.Button(
            buttons_frame,
            text="Manage Credentials",
            command=self.show_welcome_dialog
        )
        self.manage_creds_button.pack(side=tk.RIGHT, padx=5)
        
        # Reconnect button
        self.reconnect_button = ttk.Button(
            buttons_frame,
            text="Reconnect",
            command=self.connect_to_zotero
        )
        self.reconnect_button.pack(side=tk.RIGHT, padx=5)
        
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
        
        # Add a second row for chat options
        chat_settings_frame = ttk.Frame(settings_frame)
        chat_settings_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Use Ollama checkbox
        self.use_ollama_checkbox = ttk.Checkbutton(
            chat_settings_frame,
            text="Use local Ollama model",
            variable=self.use_ollama_var,
            command=self.toggle_ollama_options
        )
        self.use_ollama_checkbox.pack(side=tk.LEFT, padx=5)
        
        # Ollama model selection
        ttk.Label(chat_settings_frame, text="Model:").pack(side=tk.LEFT, padx=(15, 0))
        self.ollama_model_combobox = ttk.Combobox(
            chat_settings_frame,
            textvariable=self.ollama_model_var,
            values=["llama3.2:3b", "llama3.2:8b", "llama3.2:70b", "gemma:2b", "gemma:7b", "phi3:3.8b"],
            state='readonly',
            width=15
        )
        self.ollama_model_combobox.pack(side=tk.LEFT, padx=5)
        
        # Initially disable Ollama model selection if not using Ollama
        if not self.use_ollama_var.get():
            self.ollama_model_combobox.config(state='disabled')

        # Buttons frame for processing actions
        action_buttons_frame = ttk.Frame(collection_frame)
        action_buttons_frame.grid(row=2, column=0, columnspan=2, pady=10)

        # Process button
        self.process_button = ttk.Button(
            action_buttons_frame, 
            text="Process Selected Collection", 
            command=self.process_pdfs,
            state='disabled'
        )
        self.process_button.pack(side=tk.LEFT, padx=5)
        
        # View Results button
        self.view_results_button = ttk.Button(
            action_buttons_frame,
            text="View Topic Modeling Results",
            command=self.view_topic_modeling_results,
            state='disabled'
        )
        self.view_results_button.pack(side=tk.LEFT, padx=5)
        
        # Speak with PDFs button
        self.speak_pdfs_button = ttk.Button(
            action_buttons_frame,
            text="Speak with your PDFs",
            command=self.speak_with_pdfs,
            state='disabled'
        )
        self.speak_pdfs_button.pack(side=tk.LEFT, padx=5)
        
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
    
    def toggle_ollama_options(self):
        """Toggle the state of Ollama-related options"""
        if self.use_ollama_var.get():
            self.ollama_model_combobox.config(state='readonly')
        else:
            self.ollama_model_combobox.config(state='disabled')

    def show_welcome_dialog(self):
        """Show the welcome dialog for credential management"""
        welcome = WelcomeDialog(
            self.root, 
            self.credential_manager, 
            self.colors,
            on_complete=self.connect_to_zotero
        )
    
    def clear_credentials(self):
        """Clear saved credentials"""
        if messagebox.askyesno(
            "Confirm Credential Deletion",
            "Are you sure you want to delete all saved credentials? "
            "You will need to enter them again to use the application."
        ):
            try:
                success = self.credential_manager.clear_all_credentials()
                
                # Reset UI state
                self.collection_tree.delete(*self.collection_tree.get_children())
                self.process_button['state'] = 'disabled'
                self.view_results_button['state'] = 'disabled'
                self.speak_pdfs_button['state'] = 'disabled'
                self.connection_status.config(text="Not connected to Zotero", foreground="orange")
                
                # Clear collections
                self.collections = None
                self.zotero_client = None

                # Clear items
                self.clear_items()
                
                if success:
                    logging.info("Credentials cleared successfully")
                    messagebox.showinfo("Success", "Credentials have been cleared")
                    
                    # Show welcome dialog for re-entry
                    self.show_welcome_dialog()
                else:
                    messagebox.showwarning(
                        "Warning", 
                        "Some credentials may not have been completely removed."
                    )
                
            except Exception as e:
                logging.error(f"Error clearing credentials: {str(e)}")
                messagebox.showerror("Error", "Failed to clear credentials")

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
        try:
            logging.info("Attempting to connect to Zotero")
            
            # Get credentials
            library_id, api_key, _ = self.credential_manager.get_all_credentials()
            
            if not library_id or not api_key:
                logging.warning("Missing credentials")
                messagebox.showerror(
                    "Error", 
                    "Credentials are missing. Please enter your Zotero Library ID and API Key."
                )
                self.show_welcome_dialog()
                return
            
            # Initialize Zotero client
            self.zotero_client = ZoteroClient(library_id, api_key)
            
            # Test the connection by getting collections
            self.collections = self.zotero_client.get_collections()
            
            # Populate collection tree
            self.populate_collection_tree()
            
            # Update connection status
            self.connection_status.config(
                text=f"Connected to Zotero (Library ID: {library_id[:4]}...)", 
                foreground="green"
            )
            
            logging.info("Successfully connected to Zotero")
            
        except Exception as e:
            error_msg = str(e)
            if "Forbidden" in error_msg:
                error_msg = ("Connection failed. Please verify:\n\n"
                           "1. Your Library ID is correct\n"
                           "2. Your API key is correct\n"
                           "3. You have enabled API access in Zotero settings")
            logging.error(f"Connection failed: {error_msg}")
            messagebox.showerror("Error", error_msg)
            
            # Update connection status
            self.connection_status.config(
                text="Failed to connect to Zotero", 
                foreground="red"
            )
            
            # Show welcome dialog for re-entry
            self.show_welcome_dialog()

    def update_progress(self, value, status_text=""):
        """Update progress bar and status text"""
        self.progress_var.set(value)
        self.status_var.set(status_text)

    def clear_items(self):
        """Clear current items and collection data"""
        self.items = None
        self.current_collection = None
        
        # Clear results
        self.lda_model = None
        self.dictionary = None
        self.corpus = None
        self.processed_texts = None
        self.processed_titles = None
        
        # Disable results buttons when items are cleared
        self.view_results_button['state'] = 'disabled'
        self.speak_pdfs_button['state'] = 'disabled'

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

    def view_topic_modeling_results(self):
        """Open the topic modeling results window"""
        if not all([self.lda_model, self.dictionary, self.corpus, self.processed_titles]):
            messagebox.showwarning(
                "No Results Available",
                "Please process a collection before viewing results."
            )
            return
            
        try:
            # Show results window
            from zotero_topic_modeling.ui.results_window import TopicModelingResults
            results_window = TopicModelingResults(
                self.root,
                self.lda_model,
                self.dictionary,
                self.corpus,
                self.processed_titles,
                self.items,  # Pass the original Zotero items
                self.colors
            )
        except Exception as e:
            logging.error(f"Error showing results: {str(e)}")
            messagebox.showerror("Error", f"Could not display results: {str(e)}")

    def speak_with_pdfs(self):
        """Open the interface to speak with PDFs"""
        # Check if we have processed data
        if not all([self.processed_texts, self.processed_titles]):
            messagebox.showwarning(
                "No Data Available",
                "Please process a collection before using the chat feature."
            )
            return
        
        try:
            # Prepare document information for the chat
            documents = []
            for i, (title, text_tokens) in enumerate(zip(self.processed_titles, self.processed_texts)):
                # Convert text tokens back to string if needed
                if isinstance(text_tokens, list):
                    text = " ".join(text_tokens)
                else:
                    text = text_tokens
                    
                # Create document entry
                doc = {
                    'title': title,
                    'text': text,
                }
                
                # Add topic model information to the first document
                if i == 0 and self.lda_model:
                    doc['topic_model'] = {
                        'num_topics': self.lda_model.num_topics,
                        'topics': [
                            [word for word, _ in self.lda_model.show_topic(topic_idx, 10)]
                            for topic_idx in range(self.lda_model.num_topics)
                        ]
                    }
                    
                documents.append(doc)
            
            # Get Claude API key if not using Ollama
            claude_api_key = None
            if not self.use_ollama_var.get():
                _, _, claude_api_key = self.credential_manager.get_all_credentials()
                
                if not claude_api_key:
                    if messagebox.askyesno(
                        "Claude API Key Required",
                        "No Claude API key found. Would you like to add one now?\n\n"
                        "Alternatively, you can use the local Ollama option instead."
                    ):
                        self.show_welcome_dialog()
                        return
            
            # Create chat window
            chat_window = ChatWindow(
                self.root,
                documents,
                api_key=claude_api_key,
                use_ollama=self.use_ollama_var.get(),
                ollama_model=self.ollama_model_var.get(),
                theme_colors=self.colors
            )
            
        except Exception as e:
            logging.error(f"Error opening chat window: {str(e)}")
            messagebox.showerror("Error", f"Could not open chat interface: {str(e)}")

    def on_processing_complete(self, lda_model, dictionary, corpus, texts, titles, failed_titles, error=None):
        """Handle completion of PDF processing and topic modeling"""
        if error:
            logging.error(f"Processing failed: {error}")
            messagebox.showerror("Error", f"Processing failed: {error}")
            self.process_button['state'] = 'normal'
            self.collection_tree.bind('<<TreeviewSelect>>', self.on_collection_select)
            return
            
        # Re-enable UI elements
        self.process_button['state'] = 'normal'
        self.collection_tree.bind('<<TreeviewSelect>>', self.on_collection_select)
        
        try:
            # Store results for later use
            self.lda_model = lda_model
            self.dictionary = dictionary
            self.corpus = corpus
            self.processed_texts = texts
            self.processed_titles = titles
            
            # Enable result buttons
            self.view_results_button['state'] = 'normal'
            self.speak_pdfs_button['state'] = 'normal'
            
            # Show summary
            summary = (f"Successfully processed {len(texts)} documents:\n"
                      f"- Found {len(dictionary)} unique terms\n"
                      f"- Generated {lda_model.num_topics} topics\n\n"
                      f"Failed items:\n"
                      f"{chr(10).join('- ' + title for title in failed_titles)}" if failed_titles else "None")
            
            logging.info(f"Processing complete. Processed {len(texts)} documents.")
            messagebox.showinfo("Processing Complete", summary)
            
            # Automatically show results
            self.view_topic_modeling_results()
            
        except Exception as e:
            logging.error(f"Error handling processing results: {str(e)}")
            messagebox.showerror("Error", f"Error handling results: {str(e)}")
