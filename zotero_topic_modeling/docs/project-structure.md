# Zotero Topic Modeling Project Structure

```
zotero_topic_modeling/
├── __init__.py                  # Package initialization
├── requirements.txt             # Project dependencies
├── main.py                      # Main entry point
├── SPEAK_WITH_PDFS.md           # Documentation for RAG feature
├── README.md                    # Project overview and installation guide
├── setup.py                     # Package setup script
│
├── pdf_processor/               # PDF processing modules
│   ├── __init__.py
│   ├── extractor.py             # PDF text extraction
│   └── text_processor.py        # Text cleaning and preprocessing
│
├── topic_modeling/              # Topic modeling modules
│   ├── __init__.py
│   ├── model.py                 # LDA model implementation
│   └── visualizer.py            # Topic visualization
│
├── ui/                          # User interface modules
│   ├── __init__.py
│   ├── app.py                   # Main application window
│   ├── chat_window.py           # RAG chat interface
│   ├── components.py            # Reusable UI components
│   ├── results_window.py        # Topic modeling results display
│   ├── theme.py                 # UI theming and styling
│   └── welcome_dialog.py        # First-run setup dialog
│
├── utils/                       # Utility modules
│   ├── __init__.py
│   ├── config_manager.py        # Configuration management
│   ├── credential_manager.py    # Secure credential storage
│   ├── language_config.py       # Language support configuration
│   └── zotero_client.py         # Zotero API client
│
└── rag/                         # Retrieval-Augmented Generation modules
    ├── __init__.py
    ├── chroma_rag_manager.py    # Main RAG implementation
    └── rag_manager.py           # Alternative RAG implementation
```

## Module Descriptions

### pdf_processor

Handles PDF document processing, including text extraction and preprocessing.

- **extractor.py**: Extracts text content from PDF files
- **text_processor.py**: Cleans and processes text for topic modeling

### topic_modeling

Implements topic modeling algorithms and visualizations.

- **model.py**: Implements Latent Dirichlet Allocation (LDA) for topic discovery
- **visualizer.py**: Creates visualizations of topic distributions

### ui

Contains the user interface components.

- **app.py**: Main application window and logic
- **chat_window.py**: Interface for conversing with PDFs using RAG
- **components.py**: Reusable UI components and background workers
- **results_window.py**: Topic visualization and exploration interface
- **theme.py**: Theme implementation (dark mode)
- **welcome_dialog.py**: First-run setup and credential configuration

### utils

Provides utility functions and services.

- **config_manager.py**: Manages application configuration
- **credential_manager.py**: Securely stores API keys and credentials
- **language_config.py**: Configures NLP for different languages
- **zotero_client.py**: Interfaces with the Zotero API

### rag

Implements Retrieval-Augmented Generation for document Q&A.

- **chroma_rag_manager.py**: Main RAG implementation using simple retrieval
- **rag_manager.py**: Alternative RAG implementation
