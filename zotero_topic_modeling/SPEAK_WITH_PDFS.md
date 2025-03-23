# Speak with your PDFs

This document explains how to use the "Speak with your PDFs" feature in the Zotero Topic Modeling application.

## Overview

The "Speak with your PDFs" feature allows you to have a conversation with your Zotero PDFs using Retrieval-Augmented Generation (RAG) technology. After processing a collection of PDFs, you can ask questions about their content, and the system will retrieve relevant information and generate answers based on that information.

## Using the Feature

1. Connect to your Zotero account
2. Select a collection and click "Process Selected Collection"
3. After processing completes, click the "Speak with your PDFs" button
4. A new chat window will open
5. The system will process your documents for RAG (this may take a moment)
6. Once processing is complete, you can start asking questions about your PDFs

## Model Options

The system works with two different types of language models:

### 1. Anthropic Claude (Cloud API)

This option uses Anthropic's Claude API for high-quality responses:

- **Pros**: Higher quality responses, better understanding of context
- **Cons**: Requires an API key, sends data to Anthropic's servers

To use this mode:

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

### 2. Ollama (Local Model)

This option uses a local Ollama instance to run models on your own machine:

- **Pros**: Privacy (data stays on your machine), no API key required
- **Cons**: Requires Ollama installation, lower quality for smaller models

To use this mode:

1. Install Ollama:
   - Visit [Ollama's website](https://ollama.com/)
   - Download and install Ollama for your platform
   - Start the Ollama application

2. Pull the model you want to use:
   ```bash
   ollama pull llama3.2:3b
   ```

3. Make sure Ollama is running when you use the application

4. In the application:
   - Check the "Use local Ollama model" box
   - Select the model from the dropdown (default is llama3.2:3b)

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

If you're using Anthropic's API, it will use Claude to generate higher quality answers. If you're using Ollama, it will use your local model for generating responses.

## Troubleshooting

**Issue: Slow processing time**  
*Solution:* Processing time depends on the number and size of PDFs. Be patient with larger collections.

**Issue: Poor quality answers**  
*Solution:* Try using Anthropic API for better results or a larger Ollama model. Also, make your questions more specific.

**Issue: Missing information in answers**  
*Solution:* The system can only answer based on information in your PDFs. If information is missing, it might not be in your documents.

**Issue: Error regarding API key**  
*Solution:* Check that you've correctly set the environment variable with your API key.

**Issue: Can't connect to Ollama**  
*Solution:* Make sure Ollama is running and the model you selected is downloaded. You can pull models with `ollama pull model_name`.

**Issue: Ollama checkbox is disabled**  
*Solution:* The application couldn't connect to Ollama. Make sure Ollama is running at http://localhost:11434.

## Advanced Ollama Options

If you want to use different Ollama models:

1. Pull the model you want to use:
   ```bash
   ollama pull mistral:7b
   # Or any other model you prefer
   ```

2. Select the model from the dropdown in the application

For smaller computers, we recommend using smaller models like:
- llama3.2:3b
- gemma:2b
- gemma2:2b
- phi3:3b

For better quality responses on more capable hardware:
- llama3.1:8b
- mistral:7b
- phi3:14b

## For Developers

The RAG system is implemented in the `zotero_topic_modeling/rag` directory with these main components:

- `chunk_processor.py`: Handles breaking documents into chunks
- `embedder.py`: Creates and manages vector embeddings
- `generator.py`: Generates responses using retrieved context
- `rag_manager.py`: Coordinates the entire RAG pipeline
