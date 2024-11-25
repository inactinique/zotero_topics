import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import logging
import os

from zotero_topic_modeling.utils.zotero_client import ZoteroClient
from zotero_topic_modeling.utils.config_manager import ConfigManager
from zotero_topic_modeling.ui.components import TopicModelingThread
from zotero_topic_modeling.topic_modeling.visualizer import TopicVisualizer
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
        self.config_manager = ConfigManager()
        self.language_manager = LanguageManager()
        self.zotero_client = None
        self.collections = None
        self.items = None  # Add this line to store collection items
        self.current_collection = None  # Add this to store current collection info
        
        # Setup UI after variables are initialized
        self.setup_ui()
        self.load_saved_credentials()
        
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

    def init_variables(self):
        """Initialize all tkinter variables"""
        self.library_id_var = tk.StringVar()
        self.api_key_var = tk.StringVar()
        self.save_credentials_var = tk.BooleanVar(value=True)
        self.status_var = tk.StringVar()
        self.progress_var = tk.DoubleVar()
        self.language_var = tk.StringVar(value="English")  # Default language
        self.num_topics_var = tk.IntVar(value=5)  # Default number of topics

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

        # Process button
        self.process_button = ttk.Button(collection_frame, text="Process Selected Collection", 
                                       command=self.process_pdfs,
                                       state='disabled')
        self.process_button.grid(row=2, column=0, columnspan=2, pady=10)
        
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
        
        # Visualization frame
        self.viz_frame = ttk.LabelFrame(self.main_frame, text="Topic Visualization", padding="5")
        self.viz_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        self.viz_frame.rowconfigure(0, weight=1)
        self.viz_frame.columnconfigure(0, weight=1)
        
        # Matplotlib figure
        self.figure = Figure(figsize=(10, 6), facecolor=self.colors['bg'])
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.viz_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure main frame row weights
        self.main_frame.rowconfigure(3, weight=1)  # Make visualization frame expandable
        
        # Bind tree selection event
        self.collection_tree.bind('<<TreeviewSelect>>', self.on_collection_select)
        
        logging.info("UI setup completed")

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
            # Show results window
            from zotero_topic_modeling.ui.results_window import TopicModelingResults
            results_window = TopicModelingResults(
                self.root,
                lda_model,
                dictionary,
                corpus,
                titles,
                self.items,  # Pass the original Zotero items
                self.colors
            )
            
            # Show summary
            summary = (f"Successfully processed {len(texts)} documents:\n"
                      f"- Found {len(dictionary)} unique terms\n"
                      f"- Generated {lda_model.num_topics} topics\n\n"
                      f"Failed items:\n"
                      f"{chr(10).join('- ' + title for title in failed_titles)}" if failed_titles else "None")
            
            logging.info(f"Processing complete. Processed {len(texts)} documents.")
            messagebox.showinfo("Processing Complete", summary)
            
        except Exception as e:
            logging.error(f"Error creating results visualization: {str(e)}")
            messagebox.showerror("Error", f"Error creating visualization: {str(e)}")