from pdfminer.high_level import extract_text_to_fp
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.layout import LAParams
from pdfminer.converter import TextConverter
from io import StringIO
import logging

class PDFExtractor:
    @staticmethod
    def extract_text_from_pdf(pdf_file):
        """
        Extract text from a PDF file using pdfminer
        pdf_file: BytesIO object containing PDF data
        """
        if not pdf_file:
            return ""
            
        try:
            # Reset buffer position
            pdf_file.seek(0)
            
            # Create text output buffer
            output_string = StringIO()
            
            # Set up parameters for text extraction
            laparams = LAParams(
                line_margin=0.5,
                word_margin=0.1,
                char_margin=2.0,
                boxes_flow=0.5,
                detect_vertical=True
            )
            
            # Extract text directly to the StringIO buffer
            extract_text_to_fp(
                pdf_file,
                output_string,
                laparams=laparams,
                output_type='text',
                codec='utf-8'
            )
            
            # Get the text from the buffer
            text = output_string.getvalue()
            output_string.close()
            
            # Clean up the text
            if text:
                # Remove multiple spaces and newlines
                text = ' '.join(text.split())
                return text
            
            return ""
            
        except Exception as e:
            logging.error(f"Error extracting PDF text: {str(e)}")
            return ""
        finally:
            # Make sure we reset the buffer position
            try:
                pdf_file.seek(0)
            except:
                pass

    @staticmethod
    def is_valid_text(text):
        """
        Check if extracted text is valid and usable
        """
        if not isinstance(text, str):
            return False
        
        # Remove whitespace and check if we have content
        cleaned_text = text.strip()
        if not cleaned_text:
            return False
        
        # Check if we have enough actual text (not just special characters)
        words = [w for w in cleaned_text.split() if len(w) > 1]
        return len(words) >= 5  # At least 5 words