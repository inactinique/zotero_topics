import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import logging
from typing import Optional, List, Dict, Any
import datetime
import os
from pathlib import Path
import threading
import requests

from zotero_topic_modeling.rag.rag_manager import RAGManager

class ChatMessage:
    """Represents a single message in the chat"""
    
    def __init__(self, text: str, is_user: bool, timestamp: Optional[datetime.datetime] = None):
        self.text = text
        self.is_user = is_user
        self.timestamp = timestamp or datetime.datetime.now()
    
    def format_time(self) -> str:
        """Format the timestamp for display"""
        return self.timestamp.strftime("%H:%M")
    
    def __str__(self) -> str:
        sender = "You" if self.is_user else "Assistant"
        return f"[{self.format_time()}] {sender}: {self.text}"

class ChatWindow(tk.Toplevel):
    """
    A chat interface window for the "Speak with your PDFs" feature.
    """
    
    def __init__(self, parent, documents: List[Dict[str, Any]], api_key: Optional[str] = None, 
                 use_ollama: bool = False, ollama_model: str = "llama3.2:3b",
                 theme_colors: Optional[Dict[str, str]] = None):
        """
        Initialize the chat window.
        
        Args:
            parent: Parent window
            documents: List of document dictionaries to use for RAG
            api_key: API key for the language model service (optional)
            use_ollama: Whether to use Ollama instead of Anthropic API
            ollama_model: Model to use with Ollama
            theme_colors: Dictionary of theme colors
        """
        super().__init__(parent)
        self.title("Speak with your PDFs")
        self.geometry("800x600")
        
        # Initialize colors with defaults that can be overridden
        self.colors = {
            'bg': '#2E2E2E',
            'fg': '#FFFFFF',
            'input_bg': '#3E3E3E',
            'user_msg_bg': '#2C5F8F',
            'assistant_msg_bg': '#3F3F3F',
            'button_bg': '#4A4A4A',
            'button_fg': '#FFFFFF'
        }
        
        # Update with theme colors if provided
        if theme_colors:
            self.colors.update({k: v for k, v in theme_colors.items() if k in self.colors})
            
            # Add any missing keys using existing colors as reference
            if 'button_fg' not in theme_colors and 'fg' in theme_colors:
                self.colors['button_fg'] = theme_colors['fg']
            
            if 'input_bg' not in theme_colors and 'bg' in theme_colors:
                # Create a slightly lighter version of bg for input_bg
                self.colors['input_bg'] = self._lighten_color(theme_colors['bg'])
                
            if 'user_msg_bg' not in theme_colors and 'bg' in theme_colors:
                self.colors['user_msg_bg'] = '#2C5F8F'  # Default blue for user messages
                
            if 'assistant_msg_bg' not in theme_colors and 'bg' in theme_colors:
                self.colors['assistant_msg_bg'] = self._lighten_color(theme_colors['bg'], 0.2)
        
        # Set window background
        self.configure(bg=self.colors['bg'])
        
        # Store model parameters
        self.use_ollama = use_ollama
        self.ollama_model = ollama_model
        self.api_key = api_key
        
        # Setup UI
        self.setup_ui()
        
        # Check if Ollama is running if we're supposed to use it
        if use_ollama:
            self.check_ollama_connection()
        
        # Initialize messages
        self.messages = []
        
        # Initialize RAG manager
        self.rag_manager = RAGManager(
            api_key=api_key,
            use_ollama=use_ollama,
            ollama_model=ollama_model
        )
        
        # Start document processing
        self.status_label.config(text="Processing documents... Please wait.")
        self.rag_manager.process_documents(documents, self.on_processing_complete)
        
        # Add initial welcome message
        if use_ollama:
            self.add_message(f"Welcome to the PDF Chat! I'm using the local Ollama model '{ollama_model}' to answer your questions. Processing your documents now, please wait...", False)
        else:
            self.add_message("Welcome to the PDF Chat! I'm processing your documents so you can ask questions about them. Please wait...", False)
        
        # Store references to parent windows
        self.parent = parent
        
        # Configure behavior when window is closed
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        logging.info("Chat window initialized")
    
    def check_ollama_connection(self):
        """Check if Ollama is running and the model is available"""
        try:
            # Make a request to the Ollama API to check if it's running
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            
            if response.status_code != 200:
                messagebox.showwarning(
                    "Ollama Connection Warning",
                    "Couldn't connect to Ollama. Please make sure Ollama is running."
                )
                return False
                
            # Check if the model is available
            models = response.json().get('models', [])
            model_names = [model.get('name') for model in models]
            
            if self.ollama_model not in model_names:
                messagebox.showwarning(
                    "Ollama Model Warning",
                    f"The model '{self.ollama_model}' is not available in Ollama. "
                    f"Please download it with 'ollama pull {self.ollama_model}' "
                    f"or choose one of the available models: {', '.join(model_names[:5])}..."
                )
                return False
                
            return True
            
        except requests.RequestException:
            messagebox.showwarning(
                "Ollama Connection Error",
                "Couldn't connect to Ollama. Please make sure Ollama is running at http://localhost:11434."
            )
            return False
    
    def _lighten_color(self, hex_color: str, factor: float = 0.1) -> str:
        """
        Create a lighter version of a hex color
        
        Args:
            hex_color: Hex color code (e.g., '#2E2E2E')
            factor: How much to lighten (0.0-1.0)
            
        Returns:
            Lightened hex color
        """
        try:
            # Remove # if present
            hex_color = hex_color.lstrip('#')
            
            # Convert hex to RGB
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            
            # Lighten
            r = min(int(r + (255 - r) * factor), 255)
            g = min(int(g + (255 - g) * factor), 255)
            b = min(int(b + (255 - b) * factor), 255)
            
            # Convert back to hex
            return f'#{r:02x}{g:02x}{b:02x}'
        except Exception:
            # Return a default light gray if conversion fails
            return '#3E3E3E'
    
    def setup_ui(self):
        """Set up the user interface"""
        # Main frame
        main_frame = ttk.Frame(self, style='Chat.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configure ttk styles
        self.setup_styles()
        
        # Status frame
        status_frame = ttk.Frame(main_frame, style='Chat.TFrame')
        status_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Model info label - shows which model is being used
        if self.use_ollama:
            model_text = f"Using Ollama: {self.ollama_model}"
        elif self.api_key:
            model_text = "Using Anthropic API"
        else:
            model_text = "Using basic mode (no API)"
            
        self.model_label = ttk.Label(status_frame, text=model_text, style='Chat.TLabel')
        self.model_label.pack(side=tk.LEFT)
        
        # Status label
        self.status_label = ttk.Label(status_frame, text="Initializing...", style='Chat.TLabel')
        self.status_label.pack(side=tk.RIGHT)
        
        # Chat history frame
        history_frame = ttk.Frame(main_frame, style='Chat.TFrame')
        history_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Chat display (with scrollbar)
        self.chat_display = scrolledtext.ScrolledText(
            history_frame,
            wrap=tk.WORD,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=('Arial', 11),
            padx=10,
            pady=10,
            state='disabled'  # Start in disabled state
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        # Input frame
        input_frame = ttk.Frame(main_frame, style='Chat.TFrame')
        input_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Message input
        self.message_input = tk.Text(
            input_frame,
            height=3,
            wrap=tk.WORD,
            bg=self.colors['input_bg'],
            fg=self.colors['fg'],
            insertbackground=self.colors['fg'],  # Cursor color
            font=('Arial', 11),
            padx=5,
            pady=5
        )
        self.message_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Bind Enter key to send message (Shift+Enter for new line)
        self.message_input.bind("<Return>", self.handle_return)
        
        # Send button
        self.send_button = ttk.Button(
            input_frame,
            text="Send",
            command=self.send_message,
            style='Chat.TButton'
        )
        self.send_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Set initial focus to the message input
        self.message_input.focus_set()
    
    def setup_styles(self):
        """Set up custom styles for ttk widgets"""
        style = ttk.Style()
        
        # Frame style
        style.configure('Chat.TFrame', background=self.colors['bg'])
        
        # Label style
        style.configure('Chat.TLabel', 
                       background=self.colors['bg'],
                       foreground=self.colors['fg'],
                       font=('Arial', 10))
        
        # Button style
        style.configure('Chat.TButton',
                       font=('Arial', 10),
                       background=self.colors['button_bg'],
                       foreground=self.colors['button_fg'])
    
    def handle_return(self, event):
        """Handle Return key in the message input"""
        # Send message on Enter, allow Shift+Enter for new line
        if not event.state & 0x0001:  # 0x0001 is the shift state
            self.send_message()
            return 'break'  # Prevent the default behavior
    
    def send_message(self):
        """Send the current message"""
        # Get the message text
        message_text = self.message_input.get("1.0", tk.END).strip()
        
        if not message_text:
            return
            
        # Clear the input
        self.message_input.delete("1.0", tk.END)
        
        # Add user message to the chat
        self.add_message(message_text, True)
        
        # Check if RAG is ready
        if not self.rag_manager.is_ready():
            self.add_message("I'm still processing your documents. Please wait a moment before asking questions.", False)
            return
            
        # Process the message in a separate thread to keep UI responsive
        threading.Thread(target=self.process_message, args=(message_text,), daemon=True).start()
    
    def process_message(self, message_text):
        """
        Process the user message and generate a response.
        
        Args:
            message_text: User's message
        """
        try:
            # Update UI to show we're generating a response
            self.status_label.config(text="Generating response...")
            
            # Generate response using RAG
            response = self.rag_manager.generate_response(message_text)
            
            # Add the response to the chat
            self.add_message(response, False)
            
            # Update status
            self.status_label.config(text="Ready")
            
        except Exception as e:
            logging.error(f"Error processing message: {str(e)}")
            self.add_message(f"I'm sorry, I encountered an error while processing your question: {str(e)}", False)
            self.status_label.config(text="Error occurred")
    
    def add_message(self, text: str, is_user: bool):
        """
        Add a message to the chat display.
        
        Args:
            text: Message text
            is_user: True if the message is from the user, False if from the assistant
        """
        # Create message object
        message = ChatMessage(text, is_user)
        self.messages.append(message)
        
        # Format for display
        self.chat_display.config(state='normal')
        
        # Add sender info with timestamp
        sender = "You" if is_user else "Assistant"
        time_str = message.format_time()
        
        # Configure tag for this message
        tag_name = f"message_{len(self.messages)}"
        bg_color = self.colors['user_msg_bg'] if is_user else self.colors['assistant_msg_bg']
        
        # Insert message with sender info
        self.chat_display.insert(tk.END, f"{sender} ({time_str}):\n", "sender")
        self.chat_display.insert(tk.END, f"{text}\n\n", tag_name)
        
        # Configure tag appearance
        self.chat_display.tag_config("sender", font=('Arial', 9, 'bold'))
        self.chat_display.tag_config(tag_name, background=bg_color, lmargin1=15, lmargin2=15, rmargin=15)
        
        # Scroll to the end
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)
    
    def on_processing_complete(self, success: bool):
        """
        Handle completion of document processing.
        
        Args:
            success: True if processing was successful, False otherwise
        """
        if success:
            self.status_label.config(text="Ready")
            self.add_message("Document processing complete! You can now ask questions about your PDFs.", False)
        else:
            self.status_label.config(text="Processing failed")
            self.add_message("There was an error processing your documents. Some features may not work correctly.", False)
    
    def on_close(self):
        """Handle window close event"""
        # Perform any cleanup if needed
        self.destroy()

    def save_chat_history(self, filename: Optional[str] = None):
        """
        Save the chat history to a file.
        
        Args:
            filename: Optional filename to save to. If None, a default name will be used.
        """
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(Path.home(), '.zotero_topic_modeling', f'chat_history_{timestamp}.txt')
            
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("ZOTERO PDF CHAT HISTORY\n")
                f.write("=======================\n\n")
                
                for message in self.messages:
                    f.write(f"{str(message)}\n\n")
                    
            logging.info(f"Chat history saved to {filename}")
            return True
            
        except Exception as e:
            logging.error(f"Error saving chat history: {str(e)}")
            return False
