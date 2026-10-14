import html
import re
import time
from datetime import datetime

import requests
import streamlit as st

st.set_page_config(page_title="AskPDF", layout="wide", initial_sidebar_state="expanded")

try:
    API_BASE_URL = st.secrets["API_BASE_URL"]
except Exception:
    API_BASE_URL = "http://localhost:8000"
HEALTH_CHECK_INTERVAL = 30

http = requests.Session()
http.trust_env = False

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

html, body, .stApp, p, label, li, input, textarea, button, [data-testid="stMarkdownContainer"] {
    font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif !important;
}
.stApp { background: #212121; color: #ececec; }
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }
header[data-testid="stHeader"] { background: transparent; }
.block-container { max-width: 760px; padding: 2.5rem 1.5rem 7rem; }

[data-testid="stSidebar"] { background: #171717; border-right: none; }
[data-testid="stSidebar"] > div:first-child { padding-top: 0.25rem; }
.brand { font-size: 1.15rem; font-weight: 600; color: #f5f5f5; letter-spacing: -0.02em; padding: 4px 2px 14px; }
.brand span { color: #10a37f; }
.side-label { font-size: 0.7rem; font-weight: 500; color: #8e8e8e; margin: 22px 0 8px 2px; letter-spacing: 0.04em; }
.doc-row { display: flex; align-items: center; gap: 10px; padding: 8px 8px; border-radius: 10px; }
.doc-row:hover { background: #212121; }
.doc-badge {
    min-width: 34px; text-align: center; font-size: 0.6rem; font-weight: 600; letter-spacing: 0.04em;
    color: #10a37f; background: rgba(16,163,127,0.12); border-radius: 6px; padding: 4px 0;
}
.doc-name { font-size: 0.84rem; color: #e3e3e3; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.doc-meta { font-size: 0.68rem; color: #8e8e8e; }
.muted { font-size: 0.82rem; color: #8e8e8e; padding: 0 4px; }
.ready { display: flex; align-items: center; gap: 8px; font-size: 0.78rem; color: #b4b4b4; padding: 0 4px; }
.ready i { width: 7px; height: 7px; border-radius: 50%; display: inline-block; }
.ready i.on { background: #10a37f; }
.ready i.off { background: #ef4444; }

[data-testid="stSidebar"] .stButton > button {
    width: 100%; justify-content: flex-start; background: transparent; color: #ececec;
    border: 1px solid transparent; border-radius: 10px; padding: 0.55rem 0.75rem;
    font-size: 0.88rem; font-weight: 500; transition: background 0.15s;
}
[data-testid="stSidebar"] .stButton > button:hover { background: #262626; border-color: transparent; color: #fff; }
[data-testid="stSidebar"] .stButton > button[kind="primary"],
[data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"] {
    background: #ececec; color: #171717; justify-content: center; font-weight: 600; border-radius: 999px;
}
[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover,
[data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"]:hover { background: #ffffff; color: #000; }

[data-testid="stSidebar"] .stTextInput input {
    background: #212121 !important; color: #ececec !important;
    border: 1px solid #2f2f2f !important; border-radius: 10px !important; font-size: 0.86rem;
}
[data-testid="stSidebar"] .stTextInput input:focus { border-color: #10a37f !important; box-shadow: none !important; }
[data-testid="stSidebar"] .stTextInput label { display: none; }
[data-testid="stFileUploaderDropzone"] {
    background: #212121; border: 1px dashed #3a3a3a; border-radius: 12px; padding: 16px;
}
[data-testid="stFileUploaderDropzone"] * { color: #9b9b9b !important; font-size: 0.8rem; }
[data-testid="stFileUploaderDropzone"] button {
    background: #2f2f2f !important; border: none !important; color: #ececec !important; border-radius: 8px !important;
}
[data-testid="stFileUploaderFile"] * { color: #d4d4d4 !important; }
[data-testid="stSidebar"] [data-testid="stFileUploader"] label { display: none; }

.hero { text-align: center; padding: 14vh 0 28px; }
.hero h1 { font-size: 2rem; font-weight: 600; color: #f5f5f5; letter-spacing: -0.03em; margin: 0 0 10px; }
.hero p { color: #9b9b9b; font-size: 0.95rem; margin: 0; }

section.main .stButton > button, [data-testid="stMain"] .stButton > button {
    background: transparent; color: #d4d4d4; border: 1px solid #343434; border-radius: 16px;
    padding: 0.9rem 1rem; font-size: 0.84rem; font-weight: 400; text-align: left; line-height: 1.4;
    height: 100%; min-height: 76px; transition: background 0.15s;
}
section.main .stButton > button:hover, [data-testid="stMain"] .stButton > button:hover {
    background: #2a2a2a; border-color: #444; color: #fff;
}

[data-testid="stChatMessage"] { background: transparent; padding: 0.7rem 0; gap: 0; }
[data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"] { display: none !important; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) { flex-direction: row-reverse; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
    background: #2f2f2f; border-radius: 22px; padding: 10px 18px; width: fit-content; max-width: 80%; flex: 0 1 auto;
}
[data-testid="stChatMessageContent"] p { font-size: 0.97rem; line-height: 1.75; color: #ececec; }
.stSpinner { color: #9b9b9b; }

[data-testid="stBottom"], [data-testid="stBottom"] > div { background: #212121 !important; }
[data-testid="stBottom"] > div { padding-bottom: 1.4rem; }
[data-testid="stChatInput"] {
    background: #303030 !important; border: 1px solid #3c3c3c !important;
    border-radius: 28px !important; box-shadow: 0 2px 14px rgba(0,0,0,0.25);
}
[data-testid="stChatInput"] > div { background: transparent !important; border: none !important; }
[data-testid="stChatInput"] textarea { color: #ececec !important; font-size: 0.97rem; caret-color: #fff; }
[data-testid="stChatInput"] textarea::placeholder { color: #8e8e8e !important; }
[data-testid="stChatInputSubmitButton"] {
    background: #ececec !important; color: #171717 !important; border-radius: 50% !important;
    width: 34px; height: 34px; transition: transform 0.15s;
}
[data-testid="stChatInputSubmitButton"]:hover { background: #ffffff !important; transform: scale(1.06); }
[data-testid="stChatInputSubmitButton"]:disabled { background: #4a4a4a !important; color: #8e8e8e !important; }

.note { border: 1px solid #343434; background: #262626; border-radius: 12px; padding: 12px 16px; font-size: 0.86rem; color: #b4b4b4; margin: 10px 0; }
.note.err { border-color: rgba(239,68,68,0.4); color: #f0a0a0; background: rgba(239,68,68,0.06); }
</style>
""",
    unsafe_allow_html=True,
)

for k, v in {
    "user_id": "",
    "api_status": "offline",
    "last_health_check": 0.0,
    "messages": [],
    "uploaded_documents": [],
    "pending": None,
    "up_key": 0,
    "chats": {},
    "chat_id": None,
}.items():
    st.session_state.setdefault(k, v)


def esc(t) -> str:
    return html.escape(str(t))


def note(text: str, err: bool = False):
    st.markdown(f'<div class="note{" err" if err else ""}">{esc(text)}</div>', unsafe_allow_html=True)


def get_api_status() -> str:
    now = time.time()
    if now - st.session_state.last_health_check > HEALTH_CHECK_INTERVAL:
        try:
            ok = http.get(f"{API_BASE_URL}/health", timeout=60).status_code == 200
        except Exception:
            ok = False
        st.session_state.api_status = "online" if ok else "offline"
        st.session_state.last_health_check = now
    return st.session_state.api_status


def supported_formats():
    try:
        r = http.get(f"{API_BASE_URL}/supported-formats", timeout=5)
        if r.status_code == 200:
            return r.json()["formats"]
    except Exception:
        pass
    return ["pdf", "docx"]


def upload_document(file, user_id):
    try:
        r = http.post(
            f"{API_BASE_URL}/upload",
            params={"user_id": user_id},
            files={"file": (file.name, file.getvalue(), file.type)},
            timeout=180,
        )
        if r.status_code == 200:
            d = r.json()
            st.session_state.uploaded_documents.append(
                {
                    "filename": d["filename"],
                    "chunks": d["total_chunks"],
                    "timestamp": datetime.now().strftime("%d %b, %H:%M"),
                }
            )
            return True, f"{d['filename']} added ({d['total_chunks']} chunks)"
        try:
            detail = r.json().get("detail", r.text)
        except Exception:
            detail = r.text
        return False, f"Upload failed: {detail}"
    except requests.exceptions.Timeout:
        return False, "Upload timed out. The file may be too large."
    except Exception as e:
        return False, f"Error: {e}"


def query_documents(question, user_id):
    try:
        r = http.post(
            f"{API_BASE_URL}/query",
            params={"user_id": user_id},
            json={"question": question},
            timeout=90,
        )
        if r.status_code == 200:
            answer = r.json()["answer"]
            answer = re.sub(r"\s*\[Sources?:.*?\]", "", answer, flags=re.DOTALL).strip()
            return True, answer
        try:
            detail = r.json().get("detail", r.text)
        except Exception:
            detail = r.text
        return False, f"Request failed: {detail}"
    except requests.exceptions.Timeout:
        return False, "The request timed out. Try a more specific question."
    except Exception as e:
        return False, f"Error: {e}"


def stream_text(text: str):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.018)


def save_chat() -> bool:
    msgs = st.session_state.messages
    if not msgs:
        return False
    is_new = st.session_state.chat_id is None
    cid = st.session_state.chat_id or str(time.time())
    st.session_state.chat_id = cid
    st.session_state.chats[cid] = {"title": msgs[0]["content"][:34], "messages": list(msgs)}
    return is_new


status = get_api_status()
with st.sidebar:
    st.markdown('<div class="brand">Ask<span>PDF</span></div>', unsafe_allow_html=True)

    if st.button("New chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.chat_id = None
        st.rerun()

    st.markdown('<div class="side-label">ACCOUNT</div>', unsafe_allow_html=True)
    uid = st.text_input("User ID", value=st.session_state.user_id, placeholder="Email or username")
    if uid.strip() != st.session_state.user_id:
        st.session_state.user_id = uid.strip()
        st.session_state.messages = []
        st.session_state.uploaded_documents = []
        st.session_state.chats = {}
        st.session_state.chat_id = None
        st.rerun()

    st.markdown('<div class="side-label">ADD A DOCUMENT</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Upload",
        type=supported_formats(),
        key=f"uploader_{st.session_state.up_key}",
        label_visibility="collapsed",
    )
    if uploaded and st.session_state.user_id:
        if st.button("Add to library", type="primary", use_container_width=True):
            with st.spinner("Reading and indexing"):
                ok, msg = upload_document(uploaded, st.session_state.user_id)
            if ok:
                st.session_state.up_key += 1
                st.toast(msg)
                st.rerun()
            else:
                note(msg, err=True)
    elif uploaded:
        st.markdown('<div class="muted">Enter a User ID first.</div>', unsafe_allow_html=True)

    st.markdown('<div class="side-label">LIBRARY</div>', unsafe_allow_html=True)
    if st.session_state.uploaded_documents:
        for d in st.session_state.uploaded_documents:
            ext = d["filename"].rsplit(".", 1)[-1].upper() if "." in d["filename"] else "FILE"
            st.markdown(
                f'<div class="doc-row"><div class="doc-badge">{esc(ext)}</div>'
                f'<div style="min-width:0"><div class="doc-name">{esc(d["filename"])}</div>'
                f'<div class="doc-meta">{d["chunks"]} chunks &middot; {esc(d["timestamp"])}</div></div></div>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown('<div class="muted">Nothing here yet.</div>', unsafe_allow_html=True)

    if st.session_state.chats:
        st.markdown('<div class="side-label">RECENT CHATS</div>', unsafe_allow_html=True)
        for cid, c in reversed(list(st.session_state.chats.items())):
            if st.button(c["title"], key=f"chat_{cid}", use_container_width=True):
                st.session_state.messages = list(c["messages"])
                st.session_state.chat_id = cid
                st.rerun()

    st.markdown('<div style="height:28px"></div>', unsafe_allow_html=True)
    dot, label = ("on", "Assistant ready") if status == "online" else ("off", "Assistant unavailable")
    st.markdown(f'<div class="ready"><i class="{dot}"></i>{label}</div>', unsafe_allow_html=True)

if not st.session_state.user_id:
    st.markdown(
        '<div class="hero"><h1>Welcome to AskPDF</h1>'
        "<p>Enter a User ID in the sidebar to begin.</p></div>",
        unsafe_allow_html=True,
    )
    st.stop()

if status != "online":
    note("The assistant is unavailable right now. Start the backend and press New chat to retry.", err=True)
    st.stop()

typed = st.chat_input("Ask anything about your documents")
prompt = typed or st.session_state.pop("pending", None)

if not st.session_state.messages and not prompt:
    if st.session_state.uploaded_documents:
        st.markdown(
            '<div class="hero"><h1>What would you like to know?</h1>'
            "<p>Ask a question, or start with one of these.</p></div>",
            unsafe_allow_html=True,
        )
        suggestions = [
            "Summarize this document",
            "What are the key findings?",
            "List the main topics covered",
        ]
        cols = st.columns(3)
        for col, s in zip(cols, suggestions):
            with col:
                if st.button(s, key=f"sg_{s}", use_container_width=True):
                    st.session_state.pending = s
                    st.rerun()
    else:
        st.markdown(
            '<div class="hero"><h1>Chat with your documents</h1>'
            "<p>Add a PDF or DOCX from the sidebar, then ask anything about it.</p></div>",
            unsafe_allow_html=True,
        )

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking"):
            ok, answer = query_documents(prompt, st.session_state.user_id)
        if ok:
            placeholder = st.empty()
            shown = ""
            for chunk in stream_text(answer):
                shown += chunk
                placeholder.markdown(shown)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            if save_chat():
                st.rerun()
        else:
            note(answer, err=True)