import tkinter as tk
from tkinter import ttk
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from datetime import datetime
import logging
from typing import List, Dict, Any

class TopicModelingResults(tk.Toplevel):
    def __init__(self, parent, lda_model, dictionary, corpus, titles, items, theme_colors):
        super().__init__(parent)
        self.title("Topic Modeling Results")
        self.geometry("1200x800")
        
        # Store the analysis results
        self.lda_model = lda_model
        self.dictionary = dictionary
        self.corpus = corpus
        self.titles = titles
        self.items = items
        self.colors = theme_colors
        
        # Process dates and topics
        self.dates = self.extract_dates()
        self.topic_distributions = self.get_topic_distributions()
        
        # Setup UI
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        # Visualization selector
        ttk.Label(main_frame, text="Select Visualization:").grid(row=0, column=0, sticky=tk.W)
        self.viz_var = tk.StringVar(value="Topics Overview")
        self.viz_combo = ttk.Combobox(
            main_frame, 
            textvariable=self.viz_var,
            values=["Topics Overview", "Topics Over Time"],
            state='readonly'
        )
        self.viz_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        self.viz_combo.bind('<<ComboboxSelected>>', self.on_visualization_change)
        
        # Content frame
        self.content_frame = ttk.Frame(main_frame)
        self.content_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.rowconfigure(1, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Initialize with topics overview
        self.show_topics_overview()
        
    def extract_dates(self) -> pd.Series:
        """Extract and standardize dates from Zotero items"""
        dates = []
        for item in self.items:
            try:
                date_str = item.get('data', {}).get('date', '')
                if not date_str:
                    dates.append(None)
                    continue
                
                # Try different date formats
                for fmt in ['%Y-%m-%d', '%Y-%m', '%Y']:
                    try:
                        date = datetime.strptime(date_str, fmt)
                        dates.append(date)
                        break
                    except ValueError:
                        continue
                else:
                    # If no format matches, try to extract year
                    year_match = re.search(r'\d{4}', date_str)
                    if year_match:
                        date = datetime.strptime(year_match.group(), '%Y')
                        dates.append(date)
                    else:
                        dates.append(None)
                        
            except Exception as e:
                logging.warning(f"Error processing date for item: {str(e)}")
                dates.append(None)
                
        return pd.Series(dates)
        
    def get_topic_distributions(self) -> np.ndarray:
        """Get topic distributions for all documents"""
        num_topics = self.lda_model.num_topics
        num_docs = len(self.corpus)
        distributions = np.zeros((num_docs, num_topics))
        
        for i, doc in enumerate(self.corpus):
            doc_topics = self.lda_model.get_document_topics(doc)
            for topic_id, weight in doc_topics:
                distributions[i, topic_id] = weight
                
        return distributions
        
    def show_topics_overview(self):
        """Display the topics overview"""
        # Clear current content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        # Create text display for topics
        text_frame = ttk.Frame(self.content_frame)
        text_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create text widget
        text_widget = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set,
                            bg=self.colors['bg'], fg=self.colors['fg'])
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)
        
        # Display topics
        text_widget.insert(tk.END, "Topic Overview\n\n")
        for topic_id in range(self.lda_model.num_topics):
            topic_words = self.lda_model.show_topic(topic_id, topn=10)
            words_str = ", ".join(f"{word} ({weight:.3f})" for word, weight in topic_words)
            text_widget.insert(tk.END, f"Topic {topic_id + 1}:\n{words_str}\n\n")
            
        text_widget.config(state=tk.DISABLED)
        
    def show_topics_over_time(self):
        """Display the streamgraph of topics over time"""
        # Clear current content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        try:
            # Create figure
            fig = Figure(figsize=(10, 6), facecolor=self.colors['bg'])
            ax = fig.add_subplot(111)
            
            # Create dataframe with dates and topic distributions
            df = pd.DataFrame(self.topic_distributions)
            df['date'] = self.dates
            
            # Drop rows with missing dates
            df = df.dropna(subset=['date'])
            
            # Sort by date
            df = df.sort_values('date')
            
            # Group by year and month
            df['year'] = df['date'].dt.year
            df['month'] = df['date'].dt.month
            df['year_month'] = df['date'].dt.to_period('M')
            
            # Calculate mean topic distributions for each month
            topic_cols = list(range(self.lda_model.num_topics))
            monthly_means = df.groupby('year_month')[topic_cols].mean()
            
            # Create x-axis points (convert periods to ordinal numbers for plotting)
            x = np.arange(len(monthly_means))
            
            # Create streamgraph
            ax.stackplot(x, monthly_means.T,
                        labels=[f'Topic {i+1}' for i in range(self.lda_model.num_topics)],
                        baseline='wiggle')  # 'wiggle' creates the streamgraph effect
            
            # Customize appearance
            ax.set_facecolor(self.colors['bg'])
            fig.patch.set_facecolor(self.colors['bg'])
            ax.tick_params(colors=self.colors['fg'])
            ax.spines['bottom'].set_color(self.colors['fg'])
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_visible(False)
            
            # Set x-axis labels
            x_labels = [str(period) for period in monthly_means.index]
            num_ticks = min(10, len(x_labels))  # Show at most 10 ticks
            tick_indices = np.linspace(0, len(x_labels)-1, num_ticks, dtype=int)
            
            ax.set_xticks(tick_indices)
            ax.set_xticklabels([x_labels[i] for i in tick_indices], rotation=45, ha='right')
            
            # Add legend with better placement and style
            legend = ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left',
                             facecolor=self.colors['bg'],
                             labelcolor=self.colors['fg'])
            
            # Adjust layout to prevent label cutoff
            fig.tight_layout()
            
            # Create canvas
            canvas = FigureCanvasTkAgg(fig, master=self.content_frame)
            canvas.draw()
            canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            self.content_frame.columnconfigure(0, weight=1)
            self.content_frame.rowconfigure(0, weight=1)
            
        except Exception as e:
            logging.error(f"Error creating time visualization: {str(e)}")
            messagebox.showerror("Error", "Failed to create time visualization")
            # Fall back to topics overview
            self.show_topics_overview()

    def extract_dates(self):
        """Extract and standardize dates from Zotero items"""
        dates = []
        for item in self.items:
            try:
                date_str = item.get('data', {}).get('date', '')
                if not date_str:
                    dates.append(None)
                    continue
                
                # Try different date formats
                for fmt in ['%Y-%m-%d', '%Y-%m', '%Y']:
                    try:
                        date = pd.to_datetime(date_str, format=fmt)
                        dates.append(date)
                        break
                    except ValueError:
                        continue
                else:
                    # If no format matches, try to extract year
                    import re
                    year_match = re.search(r'\d{4}', date_str)
                    if year_match:
                        date = pd.to_datetime(f"{year_match.group()}-01-01")
                        dates.append(date)
                    else:
                        dates.append(None)
                        
            except Exception as e:
                logging.warning(f"Error processing date for item: {str(e)}")
                dates.append(None)
                
        return pd.Series(dates)

        
    def on_visualization_change(self, event):
        """Handle visualization selection change"""
        selection = self.viz_var.get()
        if selection == "Topics Overview":
            self.show_topics_overview()
        elif selection == "Topics Over Time":
            self.show_topics_over_time()
