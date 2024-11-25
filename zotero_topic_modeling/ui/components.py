import threading
import logging
from typing import Optional, Callable, List, Any

from zotero_topic_modeling.pdf_processor.extractor import PDFExtractor
from zotero_topic_modeling.pdf_processor.text_processor import TextProcessor
from zotero_topic_modeling.topic_modeling.model import TopicModel
from zotero_topic_modeling.utils.language_config import LanguageConfig

class TopicModelingThread(threading.Thread):
    def __init__(self, 
                 zotero_client, 
                 items: List[dict], 
                 callback: Callable, 
                 progress_callback: Callable,
                 language_config: LanguageConfig,
                 num_topics: int = 5):
        """
        Initialize the topic modeling thread
        
        Args:
            zotero_client: Initialized Zotero client
            items: List of Zotero items to process
            callback: Function to call when processing is complete
            progress_callback: Function to call to update progress
            language_config: Language configuration for text processing
            num_topics: Number of topics to generate
        """
        super().__init__()
        self.zotero_client = zotero_client
        self.items = items
        self.callback = callback
        self.progress_callback = progress_callback
        self.language_config = language_config
        self.num_topics = num_topics
        
    def run(self):
        try:
            texts = []
            titles = []
            failed_titles = []
            total_items = len(self.items)
            
            # Initialize text processor with language configuration
            text_processor = TextProcessor(self.language_config)
            
            # Process each document
            for i, item in enumerate(self.items):
                try:
                    progress = (i * 100) // total_items
                    title = item.get('data', {}).get('title', 'Unknown Title')
                    self.progress_callback(progress, f"Processing: {title}")
                    
                    # Get PDF content
                    pdf_content = self.zotero_client.get_item_pdfs(item)
                    if pdf_content:
                        # Extract text from PDF
                        text = PDFExtractor.extract_text_from_pdf(pdf_content)
                        if text and PDFExtractor.is_valid_text(text):
                            # Preprocess text with language-specific processing
                            processed_text = text_processor.preprocess_text(text)
                            if processed_text:  # Check if we got valid tokens
                                texts.append(processed_text)
                                titles.append(title)
                                logging.info(f"Successfully processed: {title}")
                            else:
                                failed_titles.append(f"{title} (no valid tokens after preprocessing)")
                                logging.warning(f"No valid tokens after preprocessing: {title}")
                        else:
                            failed_titles.append(f"{title} (no valid text extracted)")
                            logging.warning(f"No valid text extracted from: {title}")
                    else:
                        failed_titles.append(f"{title} (no PDF attachment)")
                        logging.warning(f"No PDF attachment found for: {title}")
                        
                except Exception as e:
                    error_msg = str(e)
                    logging.error(f"Error processing item {title}: {error_msg}")
                    failed_titles.append(f"{title} (error: {error_msg})")
                    continue
            
            if not texts:
                raise Exception("No PDF texts were successfully extracted and processed")
            
            # Create topic model
            self.progress_callback(90, "Performing topic modeling...")
            logging.info("Creating topic model")
            
            topic_model = TopicModel(
                num_topics=self.num_topics,
                language=self.language_config.code
            )
            
            # Train model
            try:
                lda_model, dictionary, corpus = topic_model.create_model(texts)
                
                # Log model information
                logging.info(f"Created topic model with {len(dictionary)} terms and {self.num_topics} topics")
                
                self.progress_callback(100, "Complete!")
                self.callback(lda_model, dictionary, corpus, texts, titles, failed_titles)
                
            except Exception as model_error:
                logging.error(f"Error in topic modeling: {str(model_error)}")
                self.callback(None, None, None, None, None, None, 
                            f"Topic modeling failed: {str(model_error)}")
            
        except Exception as e:
            logging.error(f"Processing failed: {str(e)}")
            self.callback(None, None, None, None, None, None, str(e))

    def update_progress(self, value: int, status_text: str = "") -> None:
        """Update progress through callback"""
        if self.progress_callback:
            self.progress_callback(value, status_text)