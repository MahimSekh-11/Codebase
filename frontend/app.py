import subprocess
import sys
import os
import signal
import time
import urllib.parse
from typing import List, Dict

import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

_STAMP_FILE = "/tmp/backend_deploy_stamp"
_PID_FILE = "/tmp/backend_pid"

def _get_deploy_stamp():
    """Use the modification time of this script as a unique deploy ID."""
    try:
        return str(os.path.getmtime(__file__))
    except Exception:
        return "unknown"

def _kill_old_backend():
    """Kill previously spawned backend if PID file exists."""
    try:
        if os.path.exists(_PID_FILE):
            with open(_PID_FILE) as f:
                old_pid = int(f.read().strip())
            try:
                os.kill(old_pid, signal.SIGTERM)
                time.sleep(1)
            except Exception:
                pass
            os.remove(_PID_FILE)
    except Exception:
        pass

def ensure_backend_running():
    """Start (or restart) the FastAPI backend, always using the latest deployed code."""
    import subprocess, sys, os

    current_stamp = _get_deploy_stamp()
    last_stamp = ""
    try:
        if os.path.exists(_STAMP_FILE):
            with open(_STAMP_FILE) as f:
                last_stamp = f.read().strip()
    except Exception:
        pass

    # If this is a fresh deployment (stamp changed) or backend is not responding, restart it
    backend_alive = False
    try:
        res = requests.get(f"{API_URL}/health", timeout=2)
        backend_alive = res.status_code == 200
    except Exception:
        pass

    needs_restart = (not backend_alive) or (current_stamp != last_stamp)

    if not needs_restart:
        return  # Backend is healthy and code hasn't changed

    # Kill old backend if running
    _kill_old_backend()

    # Build environment with secrets baked in
    env = os.environ.copy()
    try:
        for k, v in st.secrets.items():
            if isinstance(v, str):
                env[k] = v
        if "LLM_API_KEY" in st.secrets:
            env["LLM_API_KEY"] = st.secrets["LLM_API_KEY"]
        if "GEMINI_API_KEY" in st.secrets:
            env["LLM_API_KEY"] = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

    # Find repo root (where backend/ package lives)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)  # go up from frontend/ to root

    try:
        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.main:app",
             "--port", "8000", "--host", "127.0.0.1"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
            cwd=repo_root  # ensure backend package is importable
        )
        # Save PID for future restarts
        with open(_PID_FILE, "w") as f:
            f.write(str(proc.pid))
        # Save stamp so we don't restart again on next rerun
        with open(_STAMP_FILE, "w") as f:
            f.write(current_stamp)
        time.sleep(4)  # wait for uvicorn to boot
    except Exception as e:
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

def push_api_key_to_backend(api_key: str):
    """Push the API key directly into the running backend's memory."""
    if not api_key or not api_key.strip():
        return
    try:
        requests.post(
            f"{API_URL}/settings/api-key",
            json={"api_key": api_key.strip()},
            timeout=3
        )
    except Exception:
        pass

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
        st.header("Settings")
        # Using key= makes Streamlit auto-sync this widget into st.session_state["user_api_key"]
        st.text_input(
            "Gemini API Key",
            type="password",
            key="user_api_key",
            placeholder="AIza...",
            help="Paste your Gemini API key. This is saved for your session."
        )

        # Resolve the best available API key
        resolved_key = st.session_state.get("user_api_key", "").strip()
        if not resolved_key:
            try:
                resolved_key = st.secrets["LLM_API_KEY"]
            except Exception:
                pass
        if not resolved_key:
            try:
                resolved_key = st.secrets["GEMINI_API_KEY"]
            except Exception:
                pass

        # Push resolved key to backend on EVERY page render (survives backend restarts)
        if resolved_key:
            push_api_key_to_backend(resolved_key)
            st.success("✅ API Key is set", icon="🔑")
        else:
            st.warning("⚠️ No API key entered", icon="🔑")

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
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/zip")}
                    res = requests.post(f"{API_URL}/repository/upload", files=files)
                    if res.status_code == 200:
                        st.success("Indexing started in background!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"Error from server: {res.text}")
                except Exception as e:
                    st.error(f"Failed to send file to server. Error: {e}")
                    
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
                    # st.session_state["user_api_key"] is auto-synced by Streamlit widget key binding
                    api_key = st.session_state.get("user_api_key", "").strip()
                    # Fall back to Streamlit Cloud secrets if no key typed manually
                    if not api_key:
                        try:
                            api_key = st.secrets["LLM_API_KEY"]
                        except Exception:
                            pass
                    if not api_key:
                        try:
                            api_key = st.secrets["GEMINI_API_KEY"]
                        except Exception:
                            pass
                    if not api_key:
                        st.error("❌ No API key found! Please enter your Gemini API key in the Settings sidebar.")
                        st.stop()
                        
                    payload = {
                        "repository_id": selected_repo_id,
                        "question": prompt,
                        "history_window": 5,
                        "llm_api_key": api_key
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
