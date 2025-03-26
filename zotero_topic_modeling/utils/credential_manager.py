import keyring
import logging
import json
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class CredentialManager:
    """
    Secure credential manager using the system's keyring/keychain
    """
    # Service name for keyring
    SERVICE_NAME = "zotero_topic_modeling"
    
    # Credential keys
    ZOTERO_LIBRARY_ID = "zotero_library_id"
    ZOTERO_API_KEY = "zotero_api_key"
    CLAUDE_API_KEY = "claude_api_key"
    
    def __init__(self):
        """Initialize credential manager"""
        # Create config directory for non-sensitive settings
        self.home_dir = Path.home()
        self.config_dir = self.home_dir / '.zotero_topic_modeling'
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / 'config.json'
        
        # Check if we've gone through initial setup
        self.initialized = self._is_initialized()
        
    def _is_initialized(self):
        """Check if credentials have been set up"""
        try:
            # Check if we have at least the Zotero library ID
            library_id = self.get_credential(self.ZOTERO_LIBRARY_ID)
            return library_id is not None and library_id != ""
        except Exception:
            return False
    
    def save_credential(self, credential_name, value):
        """
        Save a credential to the system's keyring
        
        Args:
            credential_name (str): Name of the credential
            value (str): Value to store
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            keyring.set_password(self.SERVICE_NAME, credential_name, value)
            logging.info(f"Saved credential: {credential_name}")
            return True
        except Exception as e:
            logging.error(f"Error saving credential {credential_name}: {str(e)}")
            return False
    
    def get_credential(self, credential_name):
        """
        Get a credential from the system's keyring
        
        Args:
            credential_name (str): Name of the credential
        
        Returns:
            str: The credential value or None if not found
        """
        try:
            return keyring.get_password(self.SERVICE_NAME, credential_name)
        except Exception as e:
            logging.error(f"Error retrieving credential {credential_name}: {str(e)}")
            return None
    
    def delete_credential(self, credential_name):
        """
        Delete a credential from the system's keyring
        
        Args:
            credential_name (str): Name of the credential
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            keyring.delete_password(self.SERVICE_NAME, credential_name)
            logging.info(f"Deleted credential: {credential_name}")
            return True
        except Exception as e:
            logging.error(f"Error deleting credential {credential_name}: {str(e)}")
            return False
    
    def save_all_credentials(self, zotero_library_id, zotero_api_key, claude_api_key=None):
        """
        Save all credentials at once
        
        Args:
            zotero_library_id (str): Zotero library ID
            zotero_api_key (str): Zotero API key
            claude_api_key (str, optional): Claude API key
        
        Returns:
            bool: True if all credentials were saved successfully
        """
        success = True
        success &= self.save_credential(self.ZOTERO_LIBRARY_ID, zotero_library_id)
        success &= self.save_credential(self.ZOTERO_API_KEY, zotero_api_key)
        
        if claude_api_key:
            success &= self.save_credential(self.CLAUDE_API_KEY, claude_api_key)
        
        if success:
            # Mark as initialized
            self.initialized = True
            # Save a marker file to indicate initialization
            self._save_config({"initialized": True})
            
        return success
    
    def get_all_credentials(self):
        """
        Get all credentials
        
        Returns:
            tuple: (zotero_library_id, zotero_api_key, claude_api_key)
        """
        zotero_library_id = self.get_credential(self.ZOTERO_LIBRARY_ID)
        zotero_api_key = self.get_credential(self.ZOTERO_API_KEY)
        claude_api_key = self.get_credential(self.CLAUDE_API_KEY)
        
        return zotero_library_id, zotero_api_key, claude_api_key
    
    def clear_all_credentials(self):
        """
        Clear all stored credentials
        
        Returns:
            bool: True if all credentials were cleared successfully
        """
        success = True
        success &= self.delete_credential(self.ZOTERO_LIBRARY_ID)
        success &= self.delete_credential(self.ZOTERO_API_KEY)
        
        # Claude API key might not exist, so don't consider it for success
        self.delete_credential(self.CLAUDE_API_KEY)
        
        if success:
            # Mark as not initialized
            self.initialized = False
            # Remove config file
            if self.config_file.exists():
                try:
                    os.remove(self.config_file)
                except Exception as e:
                    logging.error(f"Error removing config file: {str(e)}")
                    success = False
        
        return success
    
    def _save_config(self, config_data):
        """Save non-sensitive configuration data"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f)
            # Set file permissions to user read/write only
            os.chmod(self.config_file, 0o600)
            return True
        except Exception as e:
            logging.error(f"Error saving config: {str(e)}")
            return False
    
    def _load_config(self):
        """Load non-sensitive configuration data"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logging.error(f"Error loading config: {str(e)}")
        return {}
