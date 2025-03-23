# Speak with your PDFs

This document explains how to use the "Speak with your PDFs" feature in the Zotero Topic Modeling application.

## Overview

The "Speak with your PDFs" feature allows you to have a conversation with your Zotero PDFs using Retrieval-Augmented Generation (RAG) technology. After processing a collection of PDFs, you can ask questions about their content, and the system will retrieve relevant information and generate answers based on that information.

## Setting Up the API Key (Optional)

The system works in two modes:
- **Basic mode**: Uses a simple keyword-based approach (no API key required)
- **Enhanced mode**: Uses the Anthropic Claude API for higher quality responses

To use the enhanced mode:

1. Get an API key from Anthropic:
   - Visit [Anthropic's website](https://console.anthropic.com/)
   - Create an account or log in
   - Navigate to the API keys section
   - Create a new API key

2. Set the API key as an environment variable before running the application:

   **On macOS/Linux:**
   ```bash
   export ANTHROPIC_API_KEY=your_api_key_here
   ```

   **On Windows Command Prompt:**
   ```bash
   set ANTHROPIC_API_KEY=your_api_key_here
   ```

   **On Windows PowerShell:**
   ```bash
   $env:ANTHROPIC_API_KEY="your_api_key_here"
   ```

3. Run the application normally:
   ```bash
   python -m zotero_topic_modeling.main
   ```

## Using the Feature

1. Connect to your Zotero account
2. Select a collection and click "Process Selected Collection"
3. After processing completes, click the "Speak with your PDFs" button
4. A new chat window will open
5. The system will process your documents for RAG (this may take a moment)
6. Once processing is complete, you can start asking questions about your PDFs

## Tips for Effective Questions

For best results, try questions like:

- "What are the main topics discussed in these papers?"
- "What methodologies are used in these documents?"
- "Summarize the key findings related to [specific topic]"
- "Are there any disagreements between these papers about [specific issue]?"
- "Which authors are cited most frequently across these documents?"
- "What years are covered by these documents?"
- "What evidence is presented for [specific claim]?"

## How It Works

Behind the scenes, the system:

1. Breaks your PDFs into smaller chunks
2. Creates vector embeddings for each chunk
3. When you ask a question, it finds the most relevant chunks
4. It then uses these chunks to generate an answer

If you're using the enhanced mode with an API key, the system will use Anthropic's Claude AI model to generate higher quality answers based on the retrieved information.

## Troubleshooting

**Issue: Slow processing time**  
*Solution:* Processing time depends on the number and size of PDFs. Be patient with larger collections.

**Issue: Poor quality answers**  
*Solution:* Try using the enhanced mode with an API key for better results. Also, make your questions more specific.

**Issue: Missing information in answers**  
*Solution:* The system can only answer based on information in your PDFs. If information is missing, it might not be in your documents.

**Issue: Error regarding API key**  
*Solution:* Check that you've correctly set the environment variable with your API key.

## For Developers

The RAG system is implemented in the `zotero_topic_modeling/rag` directory with these main components:

- `chunk_processor.py`: Handles breaking documents into chunks
- `embedder.py`: Creates and manages vector embeddings
- `generator.py`: Generates responses using retrieved context
- `rag_manager.py`: Coordinates the entire RAG pipeline

The API key is used in `generator.py` to make requests to the Anthropic Claude API.
