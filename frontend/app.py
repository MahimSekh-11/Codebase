import streamlit as st
import os
import requests
import time
import urllib.parse
from typing import List, Dict

API_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

def ensure_backend_running():
    """Auto-start FastAPI backend in a background process if not already running."""
    try:
        res = requests.get(f"{API_URL}/health", timeout=1)
        if res.status_code == 200:
            return
    except Exception:
        pass
    
    import subprocess
    import sys
    try:
        subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.main:app", "--port", "8000", "--host", "127.0.0.1"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(3)
    except Exception:
        pass

ensure_backend_running()

st.set_page_config(
    page_title="CodeBase RAG",
    page_icon="🔍",
    layout="wide"
)

def get_repositories() -> List[Dict]:
    try:
        res = requests.get(f"{API_URL}/repository/")
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
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
                requests.delete(f"{API_URL}/repository/{selected_repo_id}")
                st.rerun()

        st.divider()
        st.header("Ingest New Repository")
        
        repo_url = st.text_input("GitHub URL", placeholder="https://github.com/user/repo")
        if st.button("Index GitHub Repository", use_container_width=True) and repo_url:
            with st.spinner("Initializing indexing... (check backend console for progress)"):
                res = requests.post(f"{API_URL}/repository/index", json={"repo_url": repo_url})
                if res.status_code == 200:
                    st.success("Indexing started in background!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"Error: {res.text}")
            
        uploaded_file = st.file_uploader("Upload ZIP Repository", type=["zip"])
        if uploaded_file and st.button("Process ZIP", use_container_width=True):
            with st.spinner("Uploading and indexing..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/zip")}
                res = requests.post(f"{API_URL}/repository/upload", files=files)
                if res.status_code == 200:
                    st.success("Indexing started in background!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"Error: {res.text}")
                    
        st.divider()
        st.header("Repository Stats")
        if selected_repo_id:
            stats = next((r for r in repos if r["repository_id"] == selected_repo_id), None)
            if stats:
                st.metric("Files", stats["file_count"])
                st.metric("Chunks", stats["chunk_count"])
                st.metric("Size (KB)", stats["size_kb"])
                st.write("**Languages:**")
                for lang, count in stats["languages"].items():
                    st.caption(f"- {lang}: {count} files")

    # Main Chat Area
    if not selected_repo_id:
        st.info("👈 Please select or index a repository from the sidebar to begin.")
        return
        
    st.markdown(f"### Chatting with `{selected_repo_name}`")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Optional: allow user to clear chat
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

    for i, message in enumerate(st.session_state.messages):
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
        # Append user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("Searching codebase and generating answer..."):
                try:
                    payload = {
                        "repository_id": selected_repo_id,
                        "question": prompt,
                        "history_window": 5
                    }
                    res = requests.post(f"{API_URL}/chat/", json=payload)
                    
                    if res.status_code == 200:
                        data = res.json()
                        st.markdown(data["answer"])
                        
                        # Show sources expander
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
                    else:
                        st.error(f"Error {res.status_code}: {res.text}")
                except Exception as e:
                    st.error(f"Connection Error: {e}")

if __name__ == "__main__":
    main()
