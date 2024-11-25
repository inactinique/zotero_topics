import re
from typing import List
import logging
from nltk.tokenize import word_tokenize
from nltk.stem import SnowballStemmer
from zotero_topic_modeling.utils.language_config import LanguageManager

class TextProcessor:
    def __init__(self, language_config):
        """
        Initialize text processor with specific language configuration
        
        Args:
            language_config (LanguageConfig): Configuration for specific language
        """
        self.language_config = language_config
        # Ensure required NLTK resources are available
        self.language_config.ensure_resources()
        self.language_manager = LanguageManager()
        
        # Initialize stemmer if available for the language
        try:
            self.stemmer = SnowballStemmer(self.language_config.code)
        except ValueError:
            self.stemmer = None
            logging.warning(f"Stemmer not available for language {self.language_config.code}")

    def clean_text(self, text: str) -> str:
        """
        Clean text by removing unwanted characters and normalizing whitespace
        
        Args:
            text (str): Input text to clean
            
        Returns:
            str: Cleaned text
        """
        if not text:
            return ""
            
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # Remove email addresses
        text = re.sub(r'\S*@\S*\s?', '', text)
        
        # Remove special characters while preserving language-specific characters
        text = re.sub(r'[^a-zA-ZàáâäãåąčćęèéêëėįìíîïłńòóôöõøùúûüųūÿýżźñçčšžÀÁÂÄÃÅĄĆČĖĘÈÉÊËÌÍÎÏĮŁŃÒÓÔÖÕØÙÚÛÜŲŪŸÝŻŹÑßÇŒÆČŠŽ∂ð\s]',
                     ' ', text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text.strip()

    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize text using language-specific tokenizer
        
        Args:
            text (str): Text to tokenize
            
        Returns:
            List[str]: List of tokens
        """
        try:
            return word_tokenize(text, language=self.language_config.code)
        except Exception as e:
            logging.warning(f"Error using language-specific tokenizer: {str(e)}. Falling back to basic splitting.")
            return text.split()

    def remove_stopwords(self, tokens: List[str]) -> List[str]:
        """
        Remove stopwords for the specific language
        
        Args:
            tokens (List[str]): List of tokens
            
        Returns:
            List[str]: Tokens with stopwords removed
        """
        stop_words = self.language_manager.get_stopwords(self.language_config.code)
        return [token for token in tokens if token.lower() not in stop_words]

    def stem_words(self, tokens: List[str]) -> List[str]:
        """
        Apply stemming if available for the language
        
        Args:
            tokens (List[str]): List of tokens
            
        Returns:
            List[str]: Stemmed tokens
        """
        if self.stemmer:
            return [self.stemmer.stem(token) for token in tokens]
        return tokens

    def preprocess_text(self, text: str) -> List[str]:
        """
        Complete preprocessing pipeline for text
        
        Args:
            text (str): Raw input text
            
        Returns:
            List[str]: Preprocessed tokens
        """
        try:
            # Clean the text
            cleaned_text = self.clean_text(text)
            
            # Tokenize
            tokens = self.tokenize(cleaned_text)
            
            # Remove stopwords
            tokens = self.remove_stopwords(tokens)
            
            # Remove short tokens
            tokens = [token for token in tokens if len(token) > 3]
            
            # Apply stemming
            tokens = self.stem_words(tokens)
            
            return tokens
            
        except Exception as e:
            logging.error(f"Error in text preprocessing: {str(e)}")
            raise

    @staticmethod
    def is_valid_text(text: str, min_words: int = 5) -> bool:
        """
        Check if text is valid and long enough to process
        
        Args:
            text (str): Text to validate
            min_words (int): Minimum number of words required
            
        Returns:
            bool: True if text is valid, False otherwise
        """
        if not isinstance(text, str):
            return False
        
        # Remove whitespace and check if we have content
        cleaned_text = text.strip()
        if not cleaned_text:
            return False
        
        # Check if we have enough actual text (not just special characters)
        words = [w for w in cleaned_text.split() if len(w) > 1]
        return len(words) >= min_words

    def get_language_info(self) -> dict:
        """
        Get information about current language configuration
        
        Returns:
            dict: Dictionary containing language information
        """
        return {
            'code': self.language_config.code,
            'name': self.language_config.name,
            'has_stemmer': self.stemmer is not None,
            'stopwords_count': len(self.language_manager.get_stopwords(self.language_config.code))
        }