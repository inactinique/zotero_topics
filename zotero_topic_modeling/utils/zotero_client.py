from pyzotero import zotero
import requests
from io import BytesIO
import logging

logging.basicConfig(level=logging.INFO)

class ZoteroClient:
    def __init__(self, library_id, api_key):
        self.zot = zotero.Zotero(library_id, 'user', api_key)
    
    def get_collections(self):
        return self.zot.collections()
    
    def get_collection_items(self, collection_key):
        return self.zot.collection_items(collection_key)
    
    def get_item_pdfs(self, item):
        """
        Get PDF content as BytesIO object instead of saving to file
        """
        try:
            # Get child items (attachments)
            attachments = self.zot.children(item['key'])
            title = item.get('data', {}).get('title', 'Unknown')
            
            # Filter for PDF attachments
            pdf_attachments = []
            for attachment in attachments:
                data = attachment.get('data', {})
                content_type = data.get('contentType', '')
                filename = data.get('filename', '')
                
                if content_type == 'application/pdf' or (filename and filename.lower().endswith('.pdf')):
                    pdf_attachments.append(attachment)
            
            if not pdf_attachments:
                logging.warning(f"No PDF attachment found for: {title}")
                return None
            
            # Get the first PDF attachment
            pdf = pdf_attachments[0]
            
            try:
                # Get PDF download link using raw API call to avoid potential encoding issues
                pdf_key = pdf['key']
                headers = {'Authorization': f'Bearer {self.zot.api_key}'}
                download_url = f'https://api.zotero.org/{self.zot.library_type}/{self.zot.library_id}/items/{pdf_key}/file'
                
                response = requests.get(download_url, headers=headers)
                
                if response.status_code == 200:
                    # Return BytesIO object containing PDF data
                    return BytesIO(response.content)
                else:
                    logging.error(f"Failed to download PDF for {title}. Status code: {response.status_code}")
                    return None
                    
            except Exception as download_error:
                logging.error(f"Error downloading PDF for {title}: {str(download_error)}")
                return None
                
        except Exception as e:
            logging.error(f"Error getting PDF attachments: {str(e)}")
            return None
