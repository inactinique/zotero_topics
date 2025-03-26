import tkinter as tk
from tkinter import ttk, messagebox
import logging

class WelcomeDialog(tk.Toplevel):
    """
    Welcome dialog for first-time setup or credential updates
    """
    def __init__(self, parent, credential_manager, theme_colors, on_complete=None):
        super().__init__(parent)
        self.title("Welcome to Zotero Topic Modeling")
        self.geometry("550x500")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # Save references
        self.parent = parent
        self.credential_manager = credential_manager
        self.colors = theme_colors
        self.on_complete = on_complete
        
        # Configure the dialog window
        self.configure(bg=self.colors['bg'])
        
        # Setup variables
        self.zotero_library_id_var = tk.StringVar()
        self.zotero_api_key_var = tk.StringVar()
        self.claude_api_key_var = tk.StringVar()
        
        # Load existing credentials if available
        self._load_existing_credentials()
        
        # Setup UI
        self._setup_ui()
        
        # Set focus on first empty field
        self._set_initial_focus()
        
        # Center the dialog
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    
    def _load_existing_credentials(self):
        """Load existing credentials if available"""
        try:
            zotero_library_id, zotero_api_key, claude_api_key = self.credential_manager.get_all_credentials()
            if zotero_library_id:
                self.zotero_library_id_var.set(zotero_library_id)
            if zotero_api_key:
                self.zotero_api_key_var.set(zotero_api_key)
            if claude_api_key:
                self.claude_api_key_var.set(claude_api_key)
        except Exception as e:
            logging.error(f"Error loading existing credentials: {str(e)}")
    
    def _setup_ui(self):
        """Setup the dialog UI components"""
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Welcome heading
        heading_label = ttk.Label(
            main_frame, 
            text="Welcome to Zotero Topic Modeling",
            font=("Helvetica", 16, "bold")
        )
        heading_label.pack(pady=(0, 20))
        
        # Instructions
        instructions = ttk.Label(
            main_frame,
            text="Please enter your API credentials below to get started. These will be\n"
                 "stored securely in your system's credential manager and won't be\n"
                 "visible in the application after this setup.",
            justify=tk.CENTER
        )
        instructions.pack(pady=(0, 20))
        
        # Zotero credentials frame
        zotero_frame = ttk.LabelFrame(main_frame, text="Zotero Credentials (Required)", padding=10)
        zotero_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Library ID
        lib_id_frame = ttk.Frame(zotero_frame)
        lib_id_frame.pack(fill=tk.X, pady=5)
        
        lib_id_label = ttk.Label(lib_id_frame, text="Library ID:", width=15, anchor=tk.W)
        lib_id_label.pack(side=tk.LEFT)
        
        lib_id_entry = ttk.Entry(lib_id_frame, textvariable=self.zotero_library_id_var, width=40)
        lib_id_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Help text for Library ID
        lib_id_help = ttk.Label(
            zotero_frame, 
            text="Find this in Zotero website: Settings → Feeds/API",
            font=("Helvetica", 9, "italic")
        )
        lib_id_help.pack(anchor=tk.W, padx=15, pady=(0, 5))
        
        # API Key
        api_key_frame = ttk.Frame(zotero_frame)
        api_key_frame.pack(fill=tk.X, pady=5)
        
        api_key_label = ttk.Label(api_key_frame, text="API Key:", width=15, anchor=tk.W)
        api_key_label.pack(side=tk.LEFT)
        
        api_key_entry = ttk.Entry(api_key_frame, textvariable=self.zotero_api_key_var, width=40, show="•")
        api_key_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Help text for API Key
        api_key_help = ttk.Label(
            zotero_frame, 
            text="Create this in Zotero website: Settings → Feeds/API → Create new private key\n"
                 "Make sure to enable 'Allow library access' and 'Allow file access'",
            font=("Helvetica", 9, "italic")
        )
        api_key_help.pack(anchor=tk.W, padx=15, pady=(0, 5))
        
        # Claude API Key (optional)
        claude_frame = ttk.LabelFrame(main_frame, text="Claude API Key (Optional)", padding=10)
        claude_frame.pack(fill=tk.X, padx=5, pady=10)
        
        claude_key_frame = ttk.Frame(claude_frame)
        claude_key_frame.pack(fill=tk.X, pady=5)
        
        claude_key_label = ttk.Label(claude_key_frame, text="API Key:", width=15, anchor=tk.W)
        claude_key_label.pack(side=tk.LEFT)
        
        claude_key_entry = ttk.Entry(claude_key_frame, textvariable=self.claude_api_key_var, width=40, show="•")
        claude_key_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Help text for Claude API
        claude_key_help = ttk.Label(
            claude_frame, 
            text="Optional: For future integration with Claude API",
            font=("Helvetica", 9, "italic")
        )
        claude_key_help.pack(anchor=tk.W, padx=15, pady=(0, 5))
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=20)
        
        # Cancel button
        cancel_button = ttk.Button(
            buttons_frame,
            text="Cancel",
            command=self._cancel
        )
        cancel_button.pack(side=tk.LEFT, padx=5)
        
        # Save button
        save_button = ttk.Button(
            buttons_frame,
            text="Save & Continue",
            command=self._save_credentials
        )
        save_button.pack(side=tk.RIGHT, padx=5)
        
        # Store references to the entries for focus management
        self.entries = {
            'library_id': lib_id_entry,
            'api_key': api_key_entry,
            'claude_key': claude_key_entry
        }
    
    def _set_initial_focus(self):
        """Set focus on the first empty field"""
        if not self.zotero_library_id_var.get():
            self.entries['library_id'].focus_set()
        elif not self.zotero_api_key_var.get():
            self.entries['api_key'].focus_set()
        elif not self.claude_api_key_var.get():
            self.entries['claude_key'].focus_set()
        else:
            self.entries['library_id'].focus_set()
    
    def _save_credentials(self):
        """Save the entered credentials"""
        library_id = self.zotero_library_id_var.get().strip()
        api_key = self.zotero_api_key_var.get().strip()
        claude_key = self.claude_api_key_var.get().strip()
        
        # Validate Zotero credentials (required)
        if not library_id or not api_key:
            messagebox.showerror(
                "Missing Information",
                "Zotero Library ID and API Key are required fields."
            )
            return
        
        # Save credentials
        success = self.credential_manager.save_all_credentials(
            library_id, api_key, claude_key if claude_key else None
        )
        
        if success:
            logging.info("Credentials saved successfully")
            self.destroy()
            if self.on_complete:
                self.on_complete()
        else:
            messagebox.showerror(
                "Error",
                "Failed to save credentials. Please check your system's keyring access."
            )
    
    def _cancel(self):
        """Cancel the dialog and exit if required credentials aren't set"""
        if not self.credential_manager.initialized:
            if messagebox.askyesno(
                "Exit Application?",
                "Zotero credentials are required to use this application. "
                "Do you want to exit the application?"
            ):
                self.parent.destroy()  # Close the main application
            else:
                return  # Go back to the dialog
        self.destroy()
