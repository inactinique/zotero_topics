# Zotero Topic Modeling - Installation Guide

## Prerequisites

1. Python 3.10 or higher
2. pip (Python package installer)
3. A Zotero account with API access enabled
4. Anthropic account with API

## Step by step installation

1. **Create and activate a virtual environment** (recommended)
   ```bash
   # Install miniconda if you don't have it already
   # Create a new environment with all dependencies
   conda create -n zotero-rag-new python=3.10
   conda activate zotero-rag-new
   
   # Install core scientific packages via conda
   conda install -c conda-forge scipy numpy pandas matplotlib faiss-cpu
   conda install -c conda-forge gensim nltk
   
   # Install remaining packages via pip
   pip install pyzotero pdfminer.six requests sentence-transformers
   ```
   
2. **Clone or download the repository**
   ```bash
   git clone [repository-url]
   cd zotero_topics
   ```

3. **Install the package and dependencies**
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Install the package in development mode
   pip install -e .
   ```

4. **Download required NLTK data**
   ```python
   # Run Python and execute:
   import nltk
   nltk.download('punkt')
   nltk.download('stopwords')
   ```

5. **Get your Zotero credentials**
   1. Go to https://www.zotero.org/settings/keys
   2. Click "Create new private key"
   3. Give it a name (e.g., "Topic Modeling App")
   4. Make sure to enable:
      - Allow library access (Required)
      - Allow notes access
      - Allow file access
   5. Click "Save Key"
   6. Note down both your library ID (found in Feeds/API) and the new API key

## Running the Application

1. **From the terminal**
   ```bash
   # Make sure your virtual environment is activated
   python -m zotero_topic_modeling.main
   ```

2. **Using the Application**
   1. Enter your Zotero Library ID and API key
   2. Click "Connect to Zotero"
   3. Select a collection from the tree view
   4. Click "Process PDFs" to analyze the documents

## Troubleshooting

1. **PDF extraction issues**
   - Make sure PDFs are accessible in your Zotero library
   - Check that PDFs are text-based and not scanned images

2. **Connection issues**
   - Verify your Library ID and API key
   - Check your internet connection
   - Ensure your API key has proper permissions

3. **NLTK data errors**
   - Run the NLTK downloads again
   - Check your NLTK data directory (typically in your home folder)

## Features

- Topic modeling with visualization
- [Speak with your PDFs](SPEAK_WITH_PDFS.md) - Ask questions about your documents

## System Requirements

- Operating System: Windows 10+, macOS 10.14+, or Linux
- Memory: Minimum 4GB RAM recommended
- Disk Space: At least 1GB free space
- Internet connection for Zotero API access

## Support

For issues or questions, please open an issue in the GitHub repository.

