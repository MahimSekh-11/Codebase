import os
import sys
import time
import threading
from pathlib import Path
from typing import List, Dict

# Ensure project root is in sys.path for cloud deployment environment
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st

# Direct Python backend imports for robust deployment (works locally AND on live cloud URLs)
from backend.storage.metadata_store import MetadataStore
from backend.retrieval.retriever import Retriever
from backend.retrieval.vector_store import VectorStore
from backend.ingestion.github_loader import GithubLoader
from backend.ingestion.zip_loader import ZipLoader
from backend.ingestion.file_filter import is_source_file
from backend.api.repository import process_repository
from backend.utils.security import is_valid_github_url
from backend.utils.config import settings

# Initialize services directly
metadata_store = MetadataStore()
retriever = Retriever()

st.set_page_config(
    page_title="CodeBase RAG",
    page_icon="🔍",
    layout="wide"
)

def get_repositories() -> List[Dict]:
    try:
        repos = metadata_store.list_repositories()
        return [r.model_dump() if hasattr(r, 'model_dump') else r.dict() for r in repos]
    except Exception:
        return []

def main():
    st.title("🔍 CodeBase RAG")
    st.subheader("AI-Powered GitHub Repository Understanding Assistant")

    # Sidebar: Ingestion & Repo Selection
    with st.sidebar:
        st.header("Repositories")
        
        repos = get_repositories()
        repo_options = {repo["repository_name"]: repo["repository_id"] for repo in repos}
        
        selected_repo_name = st.selectbox("Select Repository", options=list(repo_options.keys()))
        selected_repo_id = repo_options.get(selected_repo_name) if selected_repo_name else None
        
        if selected_repo_id:
            if st.button("Delete Repository", type="primary"):
                try:
                    metadata_store.delete_repository(selected_repo_id)
                    VectorStore.delete_index(selected_repo_id)
                    st.success("Deleted successfully!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Deletion failed: {e}")

        st.divider()
        st.header("Ingest New Repository")
        
        repo_url = st.text_input("GitHub URL", placeholder="https://github.com/user/repo")
        if st.button("Index GitHub Repository", use_container_width=True) and repo_url:
            if not is_valid_github_url(repo_url):
                st.error("Invalid GitHub URL format")
            else:
                with st.spinner("Cloning repository..."):
                    try:
                        loader = GithubLoader()
                        repo_data = loader.clone_repository(repo_url)
                        repo_id = repo_data["repository_id"]
                        
                        # Process repository in background thread
                        t = threading.Thread(
                            target=process_repository,
                            args=(repo_data["local_path"], repo_id, repo_data["name"])
                        )
                        t.start()
                        
                        st.success("Indexing started! Processing repository files in background...")
                        time.sleep(2)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to ingest GitHub repository: {e}")
            
        uploaded_file = st.file_uploader("Upload ZIP Repository", type=["zip"])
        if uploaded_file and st.button("Process ZIP", use_container_width=True):
            with st.spinner("Extracting uploaded ZIP..."):
                try:
                    temp_zip = Path(settings.data_dir) / f"temp_{uploaded_file.name}"
                    os.makedirs(settings.data_dir, exist_ok=True)
                    with open(temp_zip, "wb") as f:
                        f.write(uploaded_file.getvalue())
                        
                    loader = ZipLoader()
                    repo_data = loader.extract_zip(str(temp_zip), uploaded_file.name.replace('.zip', ''))
                    if temp_zip.exists():
                        os.remove(temp_zip)
                        
                    repo_id = repo_data["repository_id"]
                    t = threading.Thread(
                        target=process_repository,
                        args=(repo_data["local_path"], repo_id, repo_data["name"])
                    )
                    t.start()
                    
                    st.success("ZIP extraction complete! Indexing files in background...")
                    time.sleep(2)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to process ZIP file: {e}")
                    
        st.divider()
        st.header("Repository Stats")
        if selected_repo_id:
            stats = next((r for r in repos if r["repository_id"] == selected_repo_id), None)
            if stats:
                st.metric("Files", stats["file_count"])
                st.metric("Chunks", stats["chunk_count"])
                st.metric("Size (KB)", stats["size_kb"])
                st.write("**Languages:**")
                for lang, count in stats.get("languages", {}).items():
                    st.caption(f"- {lang}: {count} files")

    # Main Chat Area
    if not selected_repo_id:
        st.info("👈 Please select or index a repository from the sidebar to begin.")
        return
        
    st.markdown(f"### Chatting with `{selected_repo_name}`")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and "sources" in message:
                with st.expander("View Retrieved Context"):
                    st.caption(f"Retrieval Time: {message['retrieval_time']:.2f}s | Generation Time: {message['generation_time']:.2f}s")
                    for idx, src in enumerate(message["sources"]):
                        st.markdown(f"**[{idx+1}] {src.get('file', 'Unknown')}** (Score: {src.get('score', 0):.2f})")
                        st.text(f"Lines {src.get('start_line', '?')}-{src.get('end_line', '?')} | Symbol: {src.get('symbol', '?')}")
                        st.code(src.get('content_snippet', ''), language="text")

    if prompt := st.chat_input("Ask a question about the codebase..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("Searching codebase and generating answer..."):
                try:
                    res = retriever.answer_question(selected_repo_id, prompt)
                    data = res.model_dump() if hasattr(res, 'model_dump') else res.dict()
                    
                    st.markdown(data["answer"])
                    
                    if data.get("sources"):
                        with st.expander("View Retrieved Context"):
                            st.caption(f"Retrieval Time: {data.get('retrieval_time', 0):.2f}s | Generation Time: {data.get('generation_time', 0):.2f}s")
                            for idx, src in enumerate(data["sources"]):
                                st.markdown(f"**[{idx+1}] {src.get('file', 'Unknown')}** (Score: {src.get('score', 0):.2f})")
                                st.text(f"Lines {src.get('start_line', '?')}-{src.get('end_line', '?')} | Symbol: {src.get('symbol', '?')}")
                                st.code(src.get('content_snippet', ''), language="text")
                                
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": data["answer"],
                        "sources": data.get("sources", []),
                        "retrieval_time": data.get("retrieval_time", 0),
                        "generation_time": data.get("generation_time", 0)
                    })
                except Exception as e:
                    st.error(f"Generation Error: {e}")

if __name__ == "__main__":
    main()
