"""
Streamlit Frontend for Multi-Modal Agent

Premium ChatGPT-like interface with:
- Left/right bubble chat layout (user right, assistant left)
- Thumbnail image previews with expandable view
- Dark-themed, modern glassmorphism design
- Sidebar for settings and capabilities
"""

import streamlit as st
import requests
import os
import logging
import base64
import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from io import BytesIO
from PIL import Image

# ============================================================================
# Configuration
# ============================================================================

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "180"))
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

HISTORY_DIR = PROJECT_ROOT / "history"
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# Page Config & Custom CSS
# ============================================================================

st.set_page_config(
    page_title="Multi-Modal Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------- Premium Dark-Theme CSS with Chat Bubbles ---------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* ── Global ─────────────────────────────────────────────────── */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .main .block-container {
        max-width: 960px;
        padding-top: 1.5rem;
        padding-bottom: 4rem;
    }

    /* ── Header ─────────────────────────────────────────────────── */
    .app-header {
        text-align: center;
        padding: 1.2rem 0 0.6rem;
    }
    .app-header h1 {
        font-size: 1.65rem;
        font-weight: 700;
        background: linear-gradient(135deg, #6C63FF, #48C9B0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    .app-header p {
        color: #9ca3af;
        font-size: 0.88rem;
        margin: 0.2rem 0 0;
    }

    /* ── Status pill ────────────────────────────────────────────── */
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 14px;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 600;
    }
    .status-pill.online  { background: rgba(72,201,176,0.15); color: #48C9B0; }
    .status-pill.offline { background: rgba(239,68,68,0.15);  color: #ef4444; }

    /* ── Chat bubbles ───────────────────────────────────────────── */
    .chat-row { display: flex; margin-bottom: 1rem; animation: fadeUp .3s ease-out; }
    .chat-row.user-row    { justify-content: flex-end; }
    .chat-row.bot-row     { justify-content: flex-start; }

    .chat-bubble {
        max-width: 72%;
        padding: 0.85rem 1.1rem;
        border-radius: 1rem;
        font-size: 0.92rem;
        line-height: 1.55;
        word-wrap: break-word;
        position: relative;
    }

    /* User bubble — right side */
    .bubble-user {
        background: linear-gradient(135deg, #6C63FF 0%, #5A54D4 100%);
        color: #f5f5f5;
        border-bottom-right-radius: 4px;
    }
    .bubble-user .bubble-time { color: rgba(255,255,255,0.55); }

    /* Bot bubble — left side */
    .bubble-bot {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.08);
        color: #e5e7eb;
        border-bottom-left-radius: 4px;
        backdrop-filter: blur(6px);
    }
    .bubble-bot .bubble-time { color: rgba(255,255,255,0.35); }

    .bubble-time {
        font-size: 0.68rem;
        margin-top: 0.4rem;
        display: block;
        text-align: right;
    }

    .bubble-label {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.7rem;
        font-weight: 600;
        margin-bottom: 0.35rem;
    }
    .label-summary   { background: rgba(59,130,246,0.18); color: #60a5fa; }
    .label-stance    { background: rgba(251,146,60,0.18); color: #fb923c; }
    .label-image_gen { background: rgba(168,85,247,0.18); color: #c084fc; }
    .label-image_analysis { background: rgba(52,211,153,0.18); color: #34d399; }
    .label-error     { background: rgba(239,68,68,0.18); color: #f87171; }

    /* Avatar circles */
    .avatar { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.9rem; flex-shrink: 0; margin-top: 2px; }
    .avatar-user { background: linear-gradient(135deg,#6C63FF,#5A54D4); margin-left: 8px; }
    .avatar-bot  { background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.12); margin-right: 8px; }

    /* ── Image thumbnail & modal ────────────────────────────────── */
    .img-thumb {
        width: 220px;
        max-width: 100%;
        border-radius: 10px;
        cursor: pointer;
        transition: transform .2s, box-shadow .2s;
        margin-top: 0.4rem;
    }
    .img-thumb:hover { transform: scale(1.03); box-shadow: 0 4px 20px rgba(108,99,255,.3); }

    /* ── Input bar ──────────────────────────────────────────────── */
    .stTextArea textarea {
        border-radius: 12px !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        background: rgba(255,255,255,0.04) !important;
        color: #e5e7eb !important;
        font-family: 'Inter', sans-serif !important;
        padding: 0.8rem 1rem !important;
    }
    .stTextArea textarea:focus {
        border-color: #6C63FF !important;
        box-shadow: 0 0 0 2px rgba(108,99,255,0.25) !important;
    }

    /* ── Buttons ─────────────────────────────────────────────────── */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        transition: all .2s;
    }
    div[data-testid="stButton"] > button[kind="primary"] {
        background: linear-gradient(135deg, #6C63FF, #5A54D4) !important;
        color: white !important;
        border: none !important;
    }
    div[data-testid="stButton"] > button[kind="primary"]:hover {
        box-shadow: 0 4px 16px rgba(108,99,255,0.35) !important;
        transform: translateY(-1px);
    }

    /* ── Sidebar ─────────────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: rgba(17,24,39,0.95);
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #e5e7eb;
    }

    .sidebar-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.8rem;
    }
    .sidebar-card h4 { margin: 0 0 0.6rem; font-size: 0.92rem; color: #e5e7eb; }
    .sidebar-card p, .sidebar-card li { font-size: 0.82rem; color: #9ca3af; line-height: 1.6; }

    /* ── Welcome card ────────────────────────────────────────────── */
    .welcome-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 16px;
        padding: 2.5rem 2rem;
        text-align: center;
        margin: 2rem 0;
    }
    .welcome-card h2 { font-size: 1.25rem; color: #e5e7eb; margin-bottom: 0.5rem; }
    .welcome-card p { color: #9ca3af; font-size: 0.88rem; max-width: 520px; margin: 0 auto; }
    .cap-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 1.2rem; max-width: 440px; margin-left: auto; margin-right: auto; }
    .cap-item {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 10px;
        padding: 0.75rem 0.9rem;
        font-size: 0.82rem;
        color: #d1d5db;
        text-align: left;
    }
    .cap-item span { margin-right: 6px; }

    /* ── Animations ──────────────────────────────────────────────── */
    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(8px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* ── Hide default Streamlit ──────────────────────────────────── */
    #MainMenu, footer, header { visibility: hidden; }

    /* Fix expander text color */
    .streamlit-expanderHeader { color: #d1d5db !important; }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# Session State
# ============================================================================

def init_state():
    """Initialize session state variables."""
    defaults = {
        "messages": [],
        "api_available": None,
        "last_response": None,
        "expanded_image": None,     # index of image to show fullsize (or None)
        "input_key": 0,             # used to force UI reset of input fields
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    if st.session_state.api_available is None:
        _check_health()


def _check_health():
    """Ping backend health endpoint."""
    try:
        r = requests.get(f"{API_BASE_URL}/health", timeout=5)
        st.session_state.api_available = r.status_code == 200
    except Exception:
        st.session_state.api_available = False


# ============================================================================
# API Helpers
# ============================================================================

def call_api(text: str, image_bytes: Optional[bytes] = None, verbose: bool = False) -> dict:
    """Call the backend /process endpoint."""
    try:
        data = {"text": text, "verbose": verbose}
        files = {}
        if image_bytes:
            files["image"] = ("image.jpg", image_bytes, "image/jpeg")

        resp = requests.post(
            f"{API_BASE_URL}/process",
            data=data,
            files=files if files else None,
            timeout=API_TIMEOUT,
        )

        if resp.status_code == 200:
            try:
                return resp.json()
            except ValueError:
                return {"success": False, "error": "Backend returned invalid JSON."}

        detail = resp.text
        try:
            j = resp.json()
            if isinstance(j, dict) and j.get("detail"):
                detail = j["detail"]
        except ValueError:
            pass
        return {"success": False, "error": f"API {resp.status_code}: {detail}"}

    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timed out — try again."}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Cannot reach API — is the backend running?"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# Rendering Helpers
# ============================================================================

_TASK_LABELS = {
    "summary": ("📝 Summary", "label-summary"),
    "stance": ("💭 Sentiment", "label-stance"),
    "image_gen": ("🎨 Image Gen", "label-image_gen"),
    "image_analysis": ("🔍 Analysis", "label-image_analysis"),
}


def _label_html(task_type: str) -> str:
    """Return an HTML badge for the task type."""
    tt = str(task_type).lower().strip() if task_type else ""
    label, cls = _TASK_LABELS.get(tt, (tt.replace("_", " ").title(), "label-summary"))
    return f'<span class="bubble-label {cls}">{label}</span>'


def _render_user_bubble(msg: dict):
    """Render a user chat bubble (right-aligned)."""
    content = msg.get("content", "")
    ts = msg.get("timestamp", "")
    task_type = msg.get("task_type", "")

    bubble_inner = ""
    if task_type:
        bubble_inner += _label_html(task_type) + "<br>"
    bubble_inner += f"{content}"
    if ts:
        bubble_inner += f'<span class="bubble-time">{ts}</span>'

    st.markdown(
        f'''<div class="chat-row user-row">
                <div class="chat-bubble bubble-user">{bubble_inner}</div>
                <div class="avatar avatar-user">👤</div>
            </div>''',
        unsafe_allow_html=True,
    )

    # Show uploaded image thumbnail
    if msg.get("image"):
        try:
            img = Image.open(BytesIO(base64.b64decode(msg["image"])))
            cols = st.columns([6, 1])
            with cols[0]:
                pass  # spacer — push to the right
            with cols[1]:
                st.image(img, width=120, caption="Uploaded")
        except Exception:
            pass


def _render_bot_bubble(msg: dict, msg_index: int):
    """Render a bot chat bubble (left-aligned) with smart result display."""
    ts = msg.get("timestamp", "")
    task_type = str(msg.get("task_type", "")).lower().strip()
    success = msg.get("success", True)
    result = msg.get("result") or {}
    content = msg.get("content", "")
    result_type = result.get("type", "") if isinstance(result, dict) else ""

    # Start bot bubble
    label = _label_html(task_type) if task_type else ""
    if not success:
        label = '<span class="bubble-label label-error">❌ Error</span>'

    # ── Build inner HTML ──
    inner_parts = [label]

    if not success:
        inner_parts.append(f"<p style='color:#f87171'>{content}</p>")
    elif result_type == "summary" or task_type == "summary":
        summary_text = result.get("content", content or "No summary generated.")
        inner_parts.append(f"<p>{summary_text}</p>")
    elif result_type == "stance" or task_type == "stance":
        stance_data = result.get("content", {})
        if isinstance(stance_data, dict):
            lbl = stance_data.get("label", "N/A")
            conf = stance_data.get("confidence", 0)
            inner_parts.append(
                f'<p><strong>{lbl}</strong> &nbsp;·&nbsp; Confidence: <strong>{conf:.1%}</strong></p>'
            )
        else:
            inner_parts.append(f"<p>{content}</p>")
    elif result_type in ("image_gen", "image") or task_type == "image_gen":
        # Just show success text — image will be rendered below as Streamlit widget
        inner_parts.append("<p>✅ Image generated — see below.</p>")
    elif result_type in ("analysis", "image_analysis") or task_type == "image_analysis":
        preds = result.get("content", [])
        if isinstance(preds, list) and preds:
            rows = "".join(
                f"<li><strong>{p.get('label','?')}</strong> — {p.get('score',0):.1%}</li>"
                for p in preds[:5]
            )
            inner_parts.append(f"<ul style='padding-left:1.2rem;margin:0.4rem 0'>{rows}</ul>")
        else:
            inner_parts.append(f"<p>{content}</p>")
    else:
        if content:
            inner_parts.append(f"<p>{content}</p>")

    if ts:
        inner_parts.append(f'<span class="bubble-time">{ts}</span>')

    st.markdown(
        f'''<div class="chat-row bot-row">
                <div class="avatar avatar-bot">🤖</div>
                <div class="chat-bubble bubble-bot">{"".join(inner_parts)}</div>
            </div>''',
        unsafe_allow_html=True,
    )

    # ── Render image as Streamlit widget (thumbnail initially) ──
    if (result_type in ("image_gen", "image") or task_type == "image_gen") and success:
        img_data = result.get("content")
        if img_data and isinstance(img_data, str) and img_data.startswith("http"):
            _render_image_preview(img_data, msg_index)


def _render_image_preview(img_url: str, idx: int):
    """Show a small thumbnail with an expand/collapse toggle."""
    is_expanded = st.session_state.get("expanded_image") == idx

    if is_expanded:
        # ── Expanded view ──
        st.image(img_url, width=560, caption="Generated Image")
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("↩ Back to chat", key=f"collapse_{idx}"):
                st.session_state.expanded_image = None
                st.rerun()
        with col2:
            st.markdown(f"[⬇ Download full-size]({img_url})")
    else:
        # ── Thumbnail view ──
        st.image(img_url, width=220, caption="Click 'Expand' to view larger")
        if st.button("🔍 Expand image", key=f"expand_{idx}"):
            st.session_state.expanded_image = idx
            st.rerun()


# ============================================================================
# Sidebar
# ============================================================================

def render_sidebar():
    """Draw the sidebar with branding, status, capabilities, and settings."""
    with st.sidebar:
        # ── Branding ──
        st.markdown("""
        <div style="text-align:center; padding: 0.5rem 0 1rem;">
            <span style="font-size:2rem">🤖</span>
            <h2 style="margin:0.2rem 0 0; font-size:1.15rem; font-weight:700;
                       background:linear-gradient(135deg,#6C63FF,#48C9B0);
                       -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
                Multi-Modal Agent
            </h2>
            <p style="color:#9ca3af;font-size:0.75rem;margin:0">AI-powered text & image processing</p>
        </div>
        """, unsafe_allow_html=True)

        # ── API Status ──
        if st.session_state.api_available:
            st.markdown(
                '<div class="status-pill online">● Connected</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="status-pill offline">● Offline</div>',
                unsafe_allow_html=True,
            )
            st.caption("Start the backend: `python backend.py`")

        if st.button("🔄 Refresh status", use_container_width=True):
            _check_health()
            st.rerun()

        st.markdown("---")

        # ── Capabilities ──
        st.markdown("""
        <div class="sidebar-card">
            <h4>✨ Capabilities</h4>
            <ul style="list-style:none;padding:0;margin:0">
                <li>📝 &nbsp;Summarize long text</li>
                <li>💭 &nbsp;Detect sentiment &amp; stance</li>
                <li>🎨 &nbsp;Generate images from prompts</li>
                <li>🔍 &nbsp;Analyze &amp; classify images</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        # ── Quick prompts ──
        st.markdown("""
        <div class="sidebar-card">
            <h4>💡 Quick Prompts</h4>
            <p style="margin:0">
                <em>"Summarize this article about …"</em><br>
                <em>"What's the sentiment of …"</em><br>
                <em>"Generate an image of a sunset"</em><br>
                <em>Upload any image → auto-analyze</em>
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # ── Actions ──
        if st.button("🆕 New Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.last_response = None
            st.session_state.expanded_image = None
            st.session_state.input_key += 1
            st.rerun()

        st.markdown("<h3 style='font-size: 1.05rem; margin-top: 1rem;'>💾 Chat History</h3>", unsafe_allow_html=True)
        if st.session_state.messages:
            if st.button("📥 Save Current Chat", use_container_width=True):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                file_path = HISTORY_DIR / f"chat_{timestamp}.json"
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(st.session_state.messages, f, indent=2)
                st.success("Chat saved!")

        st.markdown("<div style='margin-top: 0.8rem;'></div>", unsafe_allow_html=True)
        saved_files = sorted(list(HISTORY_DIR.glob("*.json")), reverse=True)
        
        if saved_files:
            file_options = {f.name: f for f in saved_files}
            selected_file = st.selectbox("Load old chat", options=list(file_options.keys()), label_visibility="collapsed")
            if st.button("📂 Load Selected Chat", use_container_width=True):
                try:
                    with open(file_options[selected_file], "r", encoding="utf-8") as f:
                        history_data = json.load(f)
                    if isinstance(history_data, list):
                        st.session_state.messages = history_data
                        st.session_state.last_response = None
                        st.session_state.expanded_image = None
                        st.session_state.input_key += 1
                        st.rerun()
                    else:
                        st.error("Invalid history format.")
                except Exception as e:
                    st.error(f"Failed to load: {e}")
        else:
            st.caption("No saved chats found on server.")

        # ── Settings (collapsed) ──
        with st.expander("⚙️ Settings"):
            new_url = st.text_input("API URL", value=API_BASE_URL, key="cfg_url")
            if new_url != API_BASE_URL:
                globals()["API_BASE_URL"] = new_url
                st.success("Updated")
            new_timeout = st.number_input(
                "Timeout (s)", value=API_TIMEOUT, min_value=10, max_value=300, key="cfg_to"
            )
            if new_timeout != API_TIMEOUT:
                globals()["API_TIMEOUT"] = int(new_timeout)
                st.success("Updated")


# ============================================================================
# Main App
# ============================================================================

def main():
    init_state()
    render_sidebar()

    # ── Header ──
    st.markdown("""
    <div class="app-header">
        <h1>🤖 Multi-Modal Agent</h1>
        <p>Your AI assistant for text summarization, sentiment analysis, and image generation</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Chat history ──
    if not st.session_state.messages:
        st.markdown("""
        <div class="welcome-card">
            <h2>👋 Welcome!</h2>
            <p>Type a message below to get started. The AI auto-detects what you need.</p>
            <div class="cap-grid">
                <div class="cap-item"><span>📝</span> Summarize text</div>
                <div class="cap-item"><span>💭</span> Detect sentiment</div>
                <div class="cap-item"><span>🎨</span> Generate images</div>
                <div class="cap-item"><span>🔍</span> Analyze images</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for i, msg in enumerate(st.session_state.messages):
            if msg.get("role") == "user":
                _render_user_bubble(msg)
            else:
                _render_bot_bubble(msg, i)

    st.markdown("---")

    # ── Input area ──
    col_input, col_opts = st.columns([5, 1])

    with col_input:
        user_text = st.text_area(
            "Message",
            placeholder="Ask me anything — summarize, analyze sentiment, generate an image …",
            height=90,
            label_visibility="collapsed",
            key=f"chat_input_{st.session_state.input_key}",
        )

    with col_opts:
        uploaded_file = st.file_uploader(
            "📎", type=["jpg", "jpeg", "png", "gif"], label_visibility="collapsed",
            key=f"upload_{st.session_state.input_key}"
        )
        verbose = st.checkbox("Verbose", value=False, key="verbose_cb")

    # ── Send button ──
    btn_cols = st.columns([1, 4])
    with btn_cols[0]:
        send = st.button("🚀 Send", type="primary", use_container_width=True)

    # ── Process ──
    if send:
        if not st.session_state.api_available:
            st.error("❌ Backend is offline. Start it with `python backend.py`")
            return
        if not user_text or not user_text.strip():
            st.warning("✏️ Please type a message first.")
            return

        # Prepare image
        image_bytes = None
        if uploaded_file:
            raw = uploaded_file.read()
            if len(raw) > MAX_FILE_SIZE:
                st.error(f"Image too large (max {MAX_FILE_SIZE // (1024*1024)}MB)")
                return
            try:
                pil = Image.open(BytesIO(raw))
                buf = BytesIO()
                pil.convert("RGB").save(buf, format="JPEG")
                image_bytes = buf.getvalue()
            except Exception as e:
                st.error(f"Could not process image: {e}")
                return

        with st.spinner("⏳ Processing …"):
            response = call_api(user_text.strip(), image_bytes, verbose)

        # Store user message
        user_msg = {
            "role": "user",
            "content": user_text.strip(),
            "timestamp": datetime.now().strftime("%H:%M"),
            "task_type": response.get("task_type") if response.get("success") else None,
        }
        if image_bytes:
            user_msg["image"] = base64.b64encode(image_bytes).decode()
        st.session_state.messages.append(user_msg)

        # Store bot message
        bot_msg = {
            "role": "assistant",
            "success": response.get("success", False),
            "timestamp": datetime.now().strftime("%H:%M"),
            "task_type": response.get("task_type"),
            "result": response.get("result"),
            "content": (
                response.get("error", "Unknown error")
                if not response.get("success")
                else "Request completed."
            ),
        }
        st.session_state.messages.append(bot_msg)
        st.session_state.last_response = response
        st.session_state.input_key += 1
        st.rerun()


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    main()
