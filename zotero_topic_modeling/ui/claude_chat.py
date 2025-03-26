import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import logging
import requests
import json
from datetime import datetime

class ClaudeChatWindow(tk.Toplevel):
    """Window for interacting with Claude API to chat about the analyzed PDFs"""
    
    def __init__(self, parent, claude_api_key, texts, titles, lda_model, dictionary, corpus, theme_colors):
        super().__init__(parent)
        self.title("Speak with your PDFs via Claude")
        self.geometry("900x700")
        
        # Store references
        self.parent = parent
        self.claude_api_key = claude_api_key
        self.texts = texts
        self.titles = titles
        self.lda_model = lda_model
        self.dictionary = dictionary
        self.corpus = corpus
        self.colors = theme_colors
        
        # Claude API endpoint
        self.api_endpoint = "https://api.anthropic.com/v1/messages"
        
        # Configure the window
        self.configure(bg=self.colors['bg'])
        
        # Setup chat history and context
        self.chat_history = []
        self.prepare_context()
        
        # Setup UI
        self.setup_ui()
        
        # Center the window
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        # Add initial system message
        self.add_system_message("Welcome to the PDF Chat. You can ask questions about the documents that have been analyzed.")
        
        # Prepare Claude with context
        threading.Thread(target=self.initialize_claude, daemon=True).start()
    
    def prepare_context(self):
        """Prepare the context from the analyzed documents"""
        # Create a summary of the topics
        self.topic_summary = []
        for topic_id in range(self.lda_model.num_topics):
            topic_words = self.lda_model.show_topic(topic_id, topn=10)
            words_str = ", ".join(f"{word} ({weight:.3f})" for word, weight in topic_words)
            self.topic_summary.append(f"Topic {topic_id + 1}: {words_str}")
        
        # Prepare document summaries
        self.document_summaries = []
        for i, (title, doc) in enumerate(zip(self.titles, self.corpus)):
            # Get the top 3 topics for this document
            doc_topics = self.lda_model.get_document_topics(doc)
            doc_topics = sorted(doc_topics, key=lambda x: x[1], reverse=True)[:3]
            
            topics_str = ", ".join([f"Topic {t+1} ({w:.2f})" for t, w in doc_topics])
            summary = f"Document: {title}\nMain topics: {topics_str}\n"
            
            # Add a sample of the text (first 200 characters)
            if i < len(self.texts) and self.texts[i]:
                text_sample = " ".join(self.texts[i][:50])  # Join the first 50 tokens
                summary += f"Sample: {text_sample}...\n"
                
            self.document_summaries.append(summary)
    
    def setup_ui(self):
        """Setup the chat interface"""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Chat history area
        history_frame = ttk.LabelFrame(main_frame, text="Chat History", padding="5")
        history_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Chat display with scroll
        self.chat_display = scrolledtext.ScrolledText(
            history_frame,
            wrap=tk.WORD,
            width=80,
            height=20,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=("Helvetica", 10)
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.chat_display.config(state=tk.DISABLED)
        
        # Input area
        input_frame = ttk.Frame(main_frame, padding="5")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Message entry
        self.message_entry = ttk.Entry(
            input_frame,
            width=70
        )
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.message_entry.bind("<Return>", lambda e: self.send_message())
        
        # Send button
        self.send_button = ttk.Button(
            input_frame,
            text="Send",
            command=self.send_message
        )
        self.send_button.pack(side=tk.RIGHT, padx=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Initializing...")
        self.status_bar = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            anchor=tk.W
        )
        self.status_bar.pack(fill=tk.X, padx=5, pady=2)
    
    def add_message_to_display(self, message, sender, color=None):
        """Add a message to the chat display"""
        self.chat_display.config(state=tk.NORMAL)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.chat_display.insert(tk.END, f"[{timestamp}] ", "timestamp")
        
        # Add sender and message
        if color:
            self.chat_display.tag_configure(sender, foreground=color)
            
        self.chat_display.insert(tk.END, f"{sender}: ", sender)
        self.chat_display.insert(tk.END, f"{message}\n\n")
        
        # Scroll to the end
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def add_system_message(self, message):
        """Add a system message to the chat"""
        self.add_message_to_display(message, "System", "orange")
    
    def add_user_message(self, message):
        """Add a user message to the chat"""
        self.add_message_to_display(message, "You", self.colors['accent'])
        # Also add to history
        self.chat_history.append({"role": "user", "content": message})
    
    def add_assistant_message(self, message):
        """Add an assistant message to the chat"""
        self.add_message_to_display(message, "Claude", "green")
        # Also add to history
        self.chat_history.append({"role": "assistant", "content": message})
    
    def initialize_claude(self):
        """Initialize Claude with the context"""
        try:
            self.status_var.set("Preparing context for Claude...")
            
            # Create system prompt with document context
            system_prompt = "You are a helpful assistant that answers questions about a collection of academic documents. "
            system_prompt += "The following documents have been analyzed using topic modeling:\n\n"
            
            # Add document summaries (limit to first 10 for brevity)
            for summary in self.document_summaries[:10]:
                system_prompt += summary + "\n"
            
            # Add topic summary
            system_prompt += "\nThe topic modeling revealed these topics:\n"
            for topic in self.topic_summary:
                system_prompt += topic + "\n"
            
            # Add instructions
            system_prompt += "\nHelp the user understand these documents and topics. "
            system_prompt += "You can provide insights about relationships between documents, trends in the topics, "
            system_prompt += "and answer specific questions about the content."
            
            # Initial message to Claude
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Make API call
            response = self.call_claude_api(messages)
            
            if response:
                self.status_var.set("Ready")
                self.add_assistant_message(response)
            else:
                self.status_var.set("Failed to initialize Claude")
                self.add_system_message("Failed to connect to Claude. Please try again later.")
                
        except Exception as e:
            logging.error(f"Error initializing Claude: {str(e)}")
            self.status_var.set("Error initializing Claude")
            self.add_system_message(f"Error initializing: {str(e)}")
    
    def send_message(self):
        """Send a message to Claude"""
        message = self.message_entry.get().strip()
        if not message:
            return
            
        # Clear entry
        self.message_entry.delete(0, tk.END)
        
        # Add to display
        self.add_user_message(message)
        
        # Disable input while processing
        self.message_entry.config(state=tk.DISABLED)
        self.send_button.config(state=tk.DISABLED)
        self.status_var.set("Claude is thinking...")
        
        # Send to Claude in a thread
        threading.Thread(target=self.process_message, args=(message,), daemon=True).start()
    
    def process_message(self, message):
        """Process a message and get response from Claude"""
        try:
            response = self.call_claude_api(self.chat_history)
            
            if response:
                self.add_assistant_message(response)
            else:
                self.add_system_message("Failed to get a response from Claude. Please try again.")
        
        except Exception as e:
            logging.error(f"Error processing message: {str(e)}")
            self.add_system_message(f"Error: {str(e)}")
        
        finally:
            # Re-enable input
            self.message_entry.config(state=tk.NORMAL)
            self.send_button.config(state=tk.NORMAL)
            self.status_var.set("Ready")
            self.message_entry.focus_set()
    
    def call_claude_api(self, messages):
        """Call the Claude API with the given messages"""
        try:
            headers = {
                "x-api-key": self.claude_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            
            data = {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 1000,
                "messages": messages
            }
            
            response = requests.post(
                self.api_endpoint,
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("content", [{}])[0].get("text", "")
            else:
                logging.error(f"API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logging.error(f"Error calling Claude API: {str(e)}")
            return None
