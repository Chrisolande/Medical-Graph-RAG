# Medical Graph RAG: A Comprehensive RAG Pipeline for Knowledge Discovery
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/chrisolande/finalrag/blob/main/LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

Medical Graph RAG is a Python-based project that implements a Retrieval Augmented Generation (RAG) pipeline. It's designed to process documents, build a knowledge graph, and utilize this graph along with vector search and reranking to answer queries based on the ingested information. The primary goal is to provide a robust and extensible framework for knowledge discovery from a corpus of documents.

## Features

- **Document Processing:** Ingests and processes documents (e.g., from PubMed Central).
- **Knowledge Graph Construction:** Builds a knowledge graph from processed documents to represent relationships and entities.
- **Vector Store Integration:** Utilizes FAISS for efficient similarity search over document embeddings.
- **Reranking:** Employs rerankers (e.g., Jina AI, FlashRank) to improve the relevance of retrieved documents.
- **Retrieval Augmented Generation (RAG):** Combines retrieved information with Large Language Models (LLMs) to generate comprehensive answers to queries.
- **Semantic Caching:** Caches LLM responses to speed up repeated queries and reduce API costs.
- **Modular Design:** Organized into distinct modules for data processing, knowledge graph management, NLP tasks, and core functionalities.
- **Configurable Pipeline:** Allows easy configuration of models, paths, and other parameters.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/Medical-Graph-RAG.git
    cd Medical-Graph-RAG
    ```

2.  **Create a virtual environment and activate it:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    The project uses Poetry for dependency management. If you don't have Poetry installed, please follow the instructions on the [official Poetry website](https://python-poetry.org/docs/#installation).
    ```bash
    pip install poetry  # Or use the recommended installer from Poetry's website
    poetry install
    ```
    Alternatively, if you prefer to use pip with a `requirements.txt` file (you would need to generate this from `pyproject.toml` using Poetry: `poetry export -f requirements.txt --output requirements.txt --without-hashes`):
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    Create a `.env` file in the root directory and add any necessary API keys or configurations. For example:
    ```env
    OPENROUTER_API_KEY="your_openrouter_api_key"
    # Add other environment variables as needed
    ```
    Refer to `src/medical_graph_rag/core/config.py` for potential environment variables to set.

## Usage

The primary way to interact with this project is through the Streamlit web application.

**Running the Application:**

1.  Ensure you have completed the [Installation](#installation) steps.
2.  Navigate to the root directory of the project.
3.  Run the Streamlit application:
    ```bash
    streamlit run app.py
    ```
    This will start the web server and open the application in your default web browser.

**Application Workflow:**

1.  **Initialize Pipeline:**
    -   In the sidebar, click the "Initialize Pipeline" button. This sets up the backend components, including the knowledge graph and query engine.
2.  **Load Documents:**
    -   **Default Data:** Click "Load pmc_chunks.json" in the sidebar to process a pre-defined dataset (`data/output/processed_pmc_data/pmc_chunks.json`). This file can be pre-chunked or raw JSON data from PMC.
    -   **Custom Data:** Alternatively, use the "Upload Custom JSON" file uploader in the sidebar to process your own JSON document. The application supports:
        -   Pre-chunked JSON files (a dictionary with a "documents" key, where each document has "content" and "metadata").
        -   Raw JSON files (a list of documents, each typically containing an "abstract").
    -   The application will process the documents, build the knowledge graph, and populate the vector store. Progress will be displayed.
3.  **Query the Knowledge Graph:**
    -   Once documents are processed, use the text input field in the main area to enter your query (e.g., "What are the effects of the Gaza war on children?").
    -   The system will:
        -   Retrieve relevant information using a combination of vector search and knowledge graph traversal.
        -   Generate a comprehensive answer using a Large Language Model (LLM), augmented with the retrieved context.
        -   Display the answer, the traversal path through the graph, and snippets of the relevant content.
        -   Show statistics about the knowledge graph.
        -   Optionally, visualize the graph traversal path.
4.  **Conversation History:**
    -   Recent queries and their responses are stored and can be viewed in the "Conversation History" expander. You can also clear this history.

## Configuration

The project's behavior can be customized through environment variables and configuration settings defined primarily in `src/medical_graph_rag/core/config.py`.

Key configurable aspects include:

-   **API Keys:**
    -   `OPENROUTER_API_KEY`: For accessing LLMs via OpenRouter.
-   **Model Names:**
    -   `EMBEDDING_MODEL_NAME`: Sentence transformer model for embeddings.
    -   `RERANKER_MODEL_NAME`: Model for reranking search results.
    -   `LLM_MODEL_NAME`: The primary Large Language Model for generation.
    -   `FLASHRANK_MODEL_NAME`: Model for FlashRank reranker.
-   **Paths and Directories:**
    -   `PERSIST_DIRECTORY`: Where the FAISS index is stored.
    -   `FLASHRANK_CACHE_DIR`: Cache directory for FlashRank models.
    -   `DEFAULT_DATABASE_PATH`: Path for the Langchain SQLite cache.
    -   `DEFAULT_FAISS_INDEX_PATH`: Path for the semantic cache's FAISS index.
-   **Processing Parameters:**
    -   `RERANKER_TOP_N`: Number of documents to keep after reranking.
    -   `BATCH_SIZE`: Batch size for document processing into the vector store.
    -   `PMC_BATCH_SIZE`: Batch size for processing PubMed Central documents.
-   **Semantic Cache:**
    -   `DEFAULT_SIMILARITY_THRESHOLD`: Similarity threshold for cache hits.
    -   `DEFAULT_MAX_CACHE_SIZE`: Maximum items in the cache.
-   **Query Engine Settings:**
    -   `MIN_NODES_TO_TRAVERSE`, `MAX_NODES_TO_TRAVERSE`: For graph traversal during querying.
    -   `LLM_MAX_CONTEXT_LENGTH`: Maximum context length for the LLM.

To modify these settings for the core backend pipeline:

1.  **Environment Variables:** Set environment variables (e.g., in a `.env` file) for API keys and other sensitive or environment-specific data. These are loaded by `src/medical_graph_rag/core/config.py`.
2.  **`src/medical_graph_rag/core/config.py`:** For more persistent or default changes to the backend pipeline, you can modify the values directly in this file. However, using environment variables is generally recommended for flexibility.

Note: The Streamlit application (`app.py`) also manages some paths internally for UI operations and temporary file storage, such as a cache directory for uploaded files and processing outputs.

## Project Structure

The project is organized into the following main directories:

-   `src/medical_graph_rag/`: Contains the core source code.
    -   `core/`: Core application logic, configuration (`config.py`), and the main pipeline class (`main.py`) used by the Streamlit app.
    -   `data_processing/`: Modules for downloading, parsing, and processing documents (e.g., `pubmed_downloader.py`, `document_processor.py`).
    -   `knowledge_graph/`: Code related to building, managing, and visualizing the knowledge graph (e.g., `knowledge_graph.py`, `graph_viz.py`).
    -   `nlp/`: Natural Language Processing components, including vector store management (`vectorstore.py`), RAG chain implementation (`rag_chain.py`), and semantic caching (`prompt_caching.py`).
-   `data/`: Holds input and output data.
    -   `input/`: Directory for raw input documents.
    -   `output/`: Directory for processed data, such as knowledge graph serializations or intermediate files.
-   `notebooks/`: Jupyter notebooks for experimentation, exploration, and visualization (e.g., `notebook.ipynb`, `playground.ipynb`).
-   `tests/`: Contains unit and integration tests for the project.
-   `app.py`: The Streamlit web application entry point.
-   `pyproject.toml`: Project metadata and dependency management using Poetry.
-   `.gitignore`: Specifies intentionally untracked files that Git should ignore.
-   `README.md`: This file.

## Contributing

Contributions are welcome! If you'd like to contribute, please follow these general guidelines:

1.  **Fork the repository.**
2.  **Create a new branch** for your feature or bug fix:
    ```bash
    git checkout -b feature/your-feature-name  # For new features
    git checkout -b fix/your-bug-fix-name    # For bug fixes
    ```
3.  **Make your changes.**
    -   Ensure your code follows the project's coding style (e.g., run `black` and `isort`).
    -   Write unit tests for new functionality or bug fixes.
    -   Update documentation if necessary.
4.  **Test your changes thoroughly.**
    -   Run all tests: `poetry run pytest` (or `pytest` if your virtual environment is activated and Poetry added the scripts to PATH).
5.  **Commit your changes** with a clear and descriptive commit message.
6.  **Push your branch** to your forked repository.
7.  **Open a pull request** to the main repository's `main` branch (or the appropriate development branch).

Please ensure your pull request describes the changes made and references any relevant issues.

### Development Setup

For development, it's recommended to install the `dev` and `test` dependencies:

```bash
poetry install --with dev,test
```

This will install tools like `pytest`, `black`, `isort`, and `mypy`.

Consider setting up pre-commit hooks to automatically format and lint your code before committing:

```bash
poetry run pre-commit install
```
(The project includes a `.pre-commit-config.yaml` file.)

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.


