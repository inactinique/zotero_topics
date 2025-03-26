# Zotero Topic Modeling - Installation Guide

A Python application for analyzing your Zotero library using topic modeling and RAG (Retrieval-Augmented Generation) technology.

## Features

- **Topic Modeling**: Analyze your PDF documents to discover latent topics
- **Interactive Visualizations**: Explore topic distributions and trends
- **Speak with your PDFs**: Ask questions about your documents using RAG technology
- **Multiple Languages**: Support for English, French, German, and more
- **Secure Credentials**: Local secure storage of your API keys

## Prerequisites

1. Python 3.10 or higher
2. pip (Python package installer)
3. A Zotero account with API access enabled
4. (Optional) An Anthropic API key for enhanced PDF chat functionality
5. (Optional) Ollama for local language model support

## Installation

### Step 1: Set up a Python environment

```bash
# Install miniconda if you don't have it already
# Create a new environment with Python 3.10
conda create -n zotero-topic python=3.10
conda activate zotero-topic

# Or using venv
python -m venv zotero-topic
# On Windows
zotero-topic\Scripts\activate
# On macOS/Linux
source zotero-topic/bin/activate
```

### Step 2: Clone or download the repository

```bash
git clone [repository-url]
cd zotero_topic_modeling
```

### Step 3: Install dependencies

```bash
# Install dependencies
pip install -r requirements.txt
```

### Step 4: Download required NLTK data

```python
# Run Python and execute:
import nltk
nltk.download('punkt')
nltk.download('stopwords')
```

### Step 5: (Optional) Set up Ollama for local language models

If you want to use local language models instead of the Anthropic API:

1. Download and install Ollama from [ollama.com](https://ollama.com/)
2. Pull a model (we recommend starting with a smaller model):
   ```bash
   ollama pull llama3.2:3b
   ```
3. Make sure Ollama is running when you use the application

## Running the Application

```bash
# Make sure your virtual environment is activated
python -m zotero_topic_modeling.main
```

## Setting Up Zotero Access

1. Go to [zotero.org/settings/keys](https://www.zotero.org/settings/keys)
2. Click "Create new private key"
3. Give it a name (e.g., "Topic Modeling App")
4. Make sure to enable:
   - Allow library access (Required)
   - Allow notes access
   - Allow file access
5. Click "Save Key"
6. Note down both your library ID (found in Feeds/API) and the new API key
7. Enter these credentials when prompted by the application

## Using the Application

### Basic Workflow

1. Connect to your Zotero account using your credentials
2. Select a collection from the tree view
3. Choose analysis settings (language, number of topics)
4. Click "Process Selected Collection" to analyze the documents
5. Explore the topic modeling results when processing completes
6. Use "Speak with your PDFs" to ask questions about your documents

### Speak with your PDFs Feature

This feature allows you to have conversations with your documents using:

1. **Anthropic Claude API**: Higher quality responses (requires API key)
2. **Local Ollama models**: More privacy-focused option (requires Ollama installation)

For detailed instructions, see [SPEAK_WITH_PDFS.md](SPEAK_WITH_PDFS.md)

## Troubleshooting

### Connection Issues

- Verify your Zotero Library ID and API key
- Ensure your API key has the correct permissions
- Check your internet connection

### PDF Extraction Issues

- Make sure PDFs are accessible in your Zotero library
- Check that PDFs are text-based (not scanned images)
- Try with a smaller collection first

### Ollama Issues

- Make sure Ollama is running when using local models
- Try using a smaller model if you encounter memory issues
- Check that you have the model installed with `ollama list`

### Installation Problems

- Make sure you're using Python 3.10 or higher
- Check that all dependencies are installed correctly
- On Windows, you might need to install Visual C++ Build Tools

## System Requirements

- **Operating System**: Windows 10+, macOS 10.14+, or Linux
- **RAM**: 8GB minimum, 16GB recommended (especially for Ollama)
- **Disk Space**: At least 8GB free space (more if using Ollama models)
- **Processor**: Multi-core processor recommended
- **Internet**: Required for Zotero API access and Anthropic API

## Privacy Considerations

- All PDF processing happens locally on your machine
- When using Anthropic Claude API, document content is sent to Anthropic's servers
- When using Ollama, all processing stays on your local machine
- Credentials are stored securely using your system's keyring/keychain

## Support and Contributions

For issues or questions, please open an issue in the GitHub repository.
