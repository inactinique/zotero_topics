import json
import os
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ConfigManager:
    def __init__(self):
        # Get user's home directory
        self.home_dir = Path.home()
        # Create .zotero_topic_modeling directory if it doesn't exist
        self.config_dir = self.home_dir / '.zotero_topic_modeling'
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / 'config.json'
        
    def save_credentials(self, library_id, api_key):
        """Save Zotero credentials to config file"""
        config = {
            'library_id': library_id,
            'api_key': api_key
        }
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
            # Set file permissions to user read/write only
            os.chmod(self.config_file, 0o600)
            return True
        except Exception as e:
            logging.error(f"Error saving credentials: {str(e)}")
            return False
            
    def load_credentials(self):
        """Load Zotero credentials from config file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                return config.get('library_id'), config.get('api_key')
        except Exception as e:
            logging.error(f"Error loading credentials: {str(e)}")
        return None, None
