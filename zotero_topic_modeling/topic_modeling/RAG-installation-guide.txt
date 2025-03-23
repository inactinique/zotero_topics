# "Speak with your PDFs" Feature - Installation Guide

This guide explains how to install and use the new RAG (Retrieval-Augmented Generation) feature that allows you to ask questions about your PDF documents.

## Installation Steps

### 1. Update Dependencies

Make sure you have all the required dependencies installed:

```bash
pip install -r requirements.txt
```

The new RAG feature requires additional dependencies:
- sentence-transformers
- faiss-cpu

### 2. API Key Setup (Optional)

The RAG feature can work in two modes:
- **Basic mode**: Uses a simple keyword-based approach (no API key required)
- **Enhanced mode**: Uses the Anthropic Claude API for better responses

To use the enhanced mode, you need an Anthropic API key:

1. Get an API key from [Anthropic](https://www.anthropic.com/)
2. Set it as an environment variable:
   ```bash
   # On macOS/Linux
   export ANTHROPIC_API_KEY=your_api_key_here
   
   # On Windows (Command Prompt)
   set ANTHROPIC_API_KEY=your_api_key_here
   
   # On Windows (PowerShell)
   $env:ANTHROPIC_API_KEY="your_api_key_here"
   ```

Alternatively, you'll be able to enter the API key in the application settings (future feature).

## Using the Feature

1. Open the Zotero Topic Modeling application
2. Connect to your Zotero account
3. Select and process a collection as usual
4. After processing is complete, click the "Speak with your PDFs" button
5. A new chat window will open where you can ask questions about your PDFs

### Example Questions

Here are some example questions you can ask:
- "What are the main topics discussed in these documents?"
- "Are there any locations mentioned in the documents?"
- "What methodologies are discussed in these papers?"
- "Summarize the key findings from these documents."
- "Which authors are cited the most across these papers?"

## How It Works

The RAG (Retrieval-Augmented Generation) feature works in several steps:

1. **Document Processing**: PDFs are broken into smaller chunks
2. **Vector Embedding**: Each chunk is converted into a vector representation
3. **Similarity Search**: When you ask a question, the system finds the most relevant chunks
4. **Response Generation**: The system generates a response based on the retrieved information

This approach ensures that responses are grounded in the actual content of your documents.

## Troubleshooting

If you encounter issues:

1. **Processing takes too long**: 
   - This is normal for large collections. The system needs to process all PDFs before you can start chatting.

2. **Memory errors**:
   - Try processing a smaller collection
   - Restart the application

3. **Missing dependencies errors**:
   - Make sure you've installed all required packages
   - Check that you're using Python 3.8 or later

4. **No valid PDF content error**:
   - Ensure your PDFs contain actual text (not scanned images)
   - Check that the PDFs are properly attached in Zotero

## Future Improvements

The current version is a basic implementation. Future updates may include:
- Better handling of large documents
- Support for more languages
- Custom embedding models
- Document summarization
- Chat history export
- Support for more file types beyond PDFs
