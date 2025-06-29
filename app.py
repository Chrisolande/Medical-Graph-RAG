import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime

import streamlit as st
from langchain_core.documents import Document

from medical_graph_rag.core.main import Main
from medical_graph_rag.data_processing.batch_processor import PMCBatchProcessor
from medical_graph_rag.data_processing.document_processor import DocumentProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ConversationEntry:
    query: str
    response: str
    timestamp: datetime
    traversal_path: list | None = None
    filtered_content: dict | None = None


@dataclass
class AppState:
    main: Main | None = None
    documents_processed: bool = False
    cache_dir: str = "/home/olande/Desktop/FinalRAG/my_cache"
    default_data_path: str = "data/output/processed_pmc_data/pmc_chunks.json"
    conversation_history: list[ConversationEntry] = field(default_factory=list)


class FileProcessor:
    """Handles file validation and processing operations."""

    @staticmethod
    def validate_json_file(file_path):
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            # Check for pre-chunked structure: "documents" key with "content" and "metadata"
            if (
                isinstance(data, dict)
                and "documents" in data
                and isinstance(data["documents"], list)
            ):
                if all(
                    isinstance(doc, dict) and "content" in doc and "metadata" in doc
                    for doc in data["documents"]
                ):
                    return (
                        True,
                        True,
                        data.get("processing_info", {}),
                        data.get("summary", {}),
                    )

            # Check for raw PMC data structure
            if isinstance(data, list) and all(
                isinstance(doc, dict) and "abstract" in doc for doc in data
            ):
                return True, False, {}, {}

        except Exception as e:
            logger.error(f"Error validating JSON file: {str(e)}")
            return False, False, {}, {}

    @staticmethod
    async def process_file(file_path: str, progress_bar, app_state: AppState):
        try:
            is_valid, is_chunked, processing_info, summary = (
                FileProcessor.validate_json_file(file_path)
            )
            if not is_valid:
                st.error(
                    f"Invalid JSON file structure at {file_path}. Expected a 'documents' key with a list of objects containing 'content' and 'metadata' or a list of objects with 'abstract'."
                )
                return
            if is_chunked:
                processed_docs = FileProcessor._load_chunked_data(
                    file_path, progress_bar
                )
                if processing_info or summary:
                    FileProcessor._display_processing_info(processing_info, summary)
            else:
                processed_docs = await FileProcessor._process_raw_data(
                    file_path, progress_bar, app_state.cache_dir
                )

            await app_state.main.process_documents(processed_docs)
            app_state.documents_processed = True
            st.success(f"Processed {len(processed_docs)} document chunks successfully!")

        except Exception as e:
            st.error(f"Error while processing the json file: {str(e)}")
            logger.error(f"Error while processing the json file: {str(e)}")

    @staticmethod
    async def _process_raw_data(
        file_path: str, progress_bar, cache_dir: str, app_state
    ) -> list[Document]:
        """Process raw PMC data."""
        document_processor = DocumentProcessor()
        batch_processor = PMCBatchProcessor(document_processor=document_processor)

        # Progress callback
        def progress_callback(completed, total, result):
            progress = completed / total
            progress_bar.progress(
                progress, text=f"Processing batch {completed}/{total}"
            )
            if result["success"]:
                st.write(
                    f"Batch {result['batch_num']}: {result['chunk_count']} chunks from {result['original_count']} documents"
                )
            else:
                st.error(f"Batch {result['batch_num']} failed: {result['error']}")

        # Process the file
        results = await batch_processor.process_pmc_file_async(
            file_path=file_path, progress_callback=progress_callback
        )

        # Save results
        os.makedirs(app_state.cache_dir, exist_ok=True)
        batch_processor.save_results(results, app_state.cache_dir)
        st.write("### Processing Summary")
        st.json(results["processing_summary"])
        return results["all_documents"]

    @staticmethod
    def _load_chunked_data(file_path, progress_bar):
        # Load pre-chunked data
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        processed_docs = [
            Document(page_content=doc["content"], metadata=doc["metadata"])
            for doc in data["documents"]
            if doc["content"].strip()
        ]

        st.write(f"Loaded {len(processed_docs)} pre-chunked documents from {file_path}")
        progress_bar.progress(1.0, text="Loaded pre-chunked documents")
        return processed_docs

    @staticmethod
    def _display_processing_info(processing_info: dict, summary: dict):
        # Display processing info and summary
        if processing_info or summary:
            st.write("### File Processing Info")
            if processing_info:
                st.json(processing_info)
            if summary:
                st.json(summary)


class QueryHandler:
    @staticmethod
    async def handle_query(query: str, app_state: AppState):
        try:
            response, traversal_path, filtered_content = await app_state.main.query(
                query
            )

            conversation_entry = ConversationEntry(
                query=query,
                response=(
                    response.content if hasattr(response, "content") else str(response)
                ),
                timestamp=datetime.now(),
                traversal_path=traversal_path,
                filtered_content=filtered_content,
            )

            app_state.conversation_history.append(conversation_entry)
            return response, traversal_path, filtered_content
        except Exception as e:
            st.error(f"Error during query processing: {str(e)}")
            logger.error(f"Error during query processing: {str(e)}")
            return None, None, None


class UIComponents:
    @staticmethod
    def render_sidebar(app_state: AppState):
        """Render sidebar with configuration and file loading options."""
        with st.sidebar:
            UIComponents._render_configuration(app_state)
            UIComponents._render_file_loading(app_state)
            UIComponents._render_custom_upload(app_state)

    @staticmethod
    def render_main_content(app_state: AppState):
        """Render main content area."""
        if app_state.main:
            st.header("Query the Knowledge Graph")
            UIComponents._render_conversation_history(app_state)
            UIComponents._render_query_interface(app_state)
        else:
            st.info("Please initialize the pipeline from the sidebar.")

    @staticmethod
    def _render_configuration(app_state: AppState):
        st.header("Configuration")
        if st.button("Initialize Pipeline"):
            UIComponents._initialize_pipeline(app_state)

    @staticmethod
    def _render_file_loading(app_state: AppState):
        """Render default file loading section."""
        st.header("Load documents")
        # Button to load default file
        if st.button("Load pmc_chunks.json"):
            if app_state.main:
                if os.path.exists(app_state.default_data_path):
                    progress_bar = st.progress(0, text="Starting processing...")
                    with st.spinner(f"Processing {app_state.default_data_path}..."):
                        asyncio.run(
                            FileProcessor.process_file(
                                app_state.default_data_path, progress_bar, app_state
                            )
                        )
                    progress_bar.empty()
                else:
                    st.error(f"File not found: {app_state.default_data_path}")
            else:
                st.warning("Please initialize the pipeline first.")

    @staticmethod
    def _render_custom_upload(app_state: AppState):
        # File uploader for other JSON files
        st.header("Upload Custom JSON")
        uploaded_file = st.file_uploader(
            "Upload JSON file with medical documents", type=["json"]
        )
        if uploaded_file and app_state.main:
            temp_file_path = os.path.join(app_state.cache_dir, uploaded_file.name)
            os.makedirs(app_state.cache_dir, exist_ok=True)
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.read())

            progress_bar = st.progress(0, text="Starting processing...")
            with st.spinner("Processing uploaded file..."):
                asyncio.run(
                    FileProcessor.process_file(temp_file_path, progress_bar, app_state)
                )
            progress_bar.empty()
            os.remove(temp_file_path)

    @staticmethod
    def _initialize_pipeline(app_state: AppState):
        """Initialize the main pipeline."""
        try:
            app_state.main = Main(cache_dir=app_state.cache_dir)
            st.success("Pipeline initialized successfully!")
        except Exception as e:
            st.error(f"Failed to initialize pipeline: {str(e)}")

    @staticmethod
    def _render_conversation_history(app_state: AppState):
        """Render conversation history with improved layout."""
        if app_state.conversation_history:
            with st.expander("Conversation History", expanded=False):
                for i, conv in enumerate(reversed(app_state.conversation_history[-5:])):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(
                            f"**Q{len(app_state.conversation_history)-i}:** {conv.query}"
                        )
                        st.write(f"**A:** {conv.response[:200]}...")
                    with col2:
                        st.caption(conv.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
                    st.divider()

                if st.button("Clear History"):
                    app_state.conversation_history = []
                    st.rerun()

    @staticmethod
    def _render_query_interface(app_state: AppState):
        """Render query input and response interface."""
        query = st.text_input(
            "Enter your query:",
            placeholder="e.g., What are the effects of the Gaza war on children?",
        )

        if query and app_state.documents_processed:
            with st.spinner("Processing query..."):
                response, traversal_path, filtered_content = asyncio.run(
                    QueryHandler.handle_query(query, app_state)
                )

                if response:
                    UIComponents._render_query_results(
                        response, traversal_path, filtered_content, app_state
                    )
                else:
                    st.warning(
                        "No response generated. Please check the query or document processing."
                    )
        elif query and not app_state.documents_processed:
            st.warning("Please load or upload and process documents before querying.")

    @staticmethod
    def _render_query_results(
        response, traversal_path, filtered_content, app_state: AppState
    ):
        """Render query results with improved layout."""
        st.subheader("Query Response")
        st.write(response.content if hasattr(response, "content") else str(response))

        if traversal_path:
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Traversal Path")
                st.write(f"Nodes traversed: {traversal_path}")

                st.subheader("Knowledge Graph Statistics")
                stats = app_state.main.knowledge_graph.get_stats()
                st.json(stats)

            with col2:
                st.subheader("Relevant Content")
                for node_id, content in filtered_content.items():
                    with st.expander(f"Node {node_id}"):
                        st.write(
                            content[:400] + "..." if len(content) > 400 else content
                        )

            UIComponents._render_graph_visualization(traversal_path, app_state)

    @staticmethod
    def _render_graph_visualization(traversal_path, app_state: AppState):
        """Render graph visualization."""
        st.subheader("Graph Visualization")
        try:
            graph_image_buffer = app_state.main.visualizer.visualize_traversal(
                app_state.main.knowledge_graph.graph, traversal_path
            )

            if graph_image_buffer:
                st.image(graph_image_buffer, caption="Knowledge Graph Traversal")
            else:
                st.warning("No visualization generated.")

        except Exception as e:
            st.error(f"Failed to visualize graph: {str(e)}")
            logger.error(f"Failed to visualize graph: {str(e)}")


class MedicalRAGApp:
    """Main application class."""

    def __init__(self):
        st.set_page_config(page_title="Medical RAG Knowledge Graph", layout="wide")
        self.app_state = self._initialize_session_state()

    def _initialize_session_state(self) -> AppState:
        """Initialize or retrieve session state."""
        if "app_state" not in st.session_state:
            st.session_state.app_state = AppState()
        return st.session_state.app_state

    def run(self):
        """Run the main application."""
        st.title("Medical RAG Knowledge Graph Explorer")
        UIComponents.render_sidebar(self.app_state)
        UIComponents.render_main_content(self.app_state)


def main():
    app = MedicalRAGApp()
    app.run()


if __name__ == "__main__":
    main()
