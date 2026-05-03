import streamlit as st
import os

st.set_page_config(
    page_title="Stack — Redefining Lending & Investing",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Check if user clicked "Enter Platform" ─────────────────
_goto = st.query_params.get("goto", "")
if _goto == "platform":
    st.query_params.clear()
    # Redirect to the platform app
    # On Streamlit Cloud this will be the home app URL
    PLATFORM_URL = st.secrets.get("PLATFORM_URL", "http://localhost:8502")
    st.markdown(f"""
    <meta http-equiv="refresh" content="0; url={PLATFORM_URL}">
    <script>window.location.href = "{PLATFORM_URL}";</script>
    """, unsafe_allow_html=True)
    st.stop()

# ── Hide all Streamlit chrome ───────────────────────────────
st.markdown("""
<style>
    #MainMenu, footer, header, [data-testid="stToolbar"],
    [data-testid="stDecoration"], [data-testid="stStatusWidget"],
    .stDeployButton { display: none !important; visibility: hidden !important; }
    .block-container { padding: 0 !important; max-width: 100% !important; }
    section.main > div { padding: 0 !important; }
    html, body, [class*="css"] { margin: 0; padding: 0; overflow-x: hidden; }
    .stApp { background: #0A1628; }
    /* Remove iframe border */
    iframe { border: none !important; display: block; }
</style>
""", unsafe_allow_html=True)

# ── Load modified HTML ──────────────────────────────────────
_DIR = os.path.dirname(os.path.abspath(__file__))
html_path = os.path.join(_DIR, "stack_website_modified.html")

if not os.path.exists(html_path):
    st.error("Marketing site HTML not found. Make sure stack_website_modified.html is in the same folder.")
    st.stop()

with open(html_path, "r") as f:
    html_content = f.read()

# ── Render fullscreen ───────────────────────────────────────
# Use components.html for true full-page rendering
import streamlit.components.v1 as components

components.html(
    html_content,
    height=5000,   # tall enough for full page — scrolls internally
    scrolling=True,
)

# ── Listen for postMessage from iframe ──────────────────────
# JS bridge: if iframe signals "platform", redirect
st.markdown("""
<script>
window.addEventListener('message', function(e) {
    if (e.data && e.data.type === 'streamlit:setComponentValue' && e.data.value === 'platform') {
        window.location.href = window.location.href.split('?')[0] + '?goto=platform';
    }
});
</script>
""", unsafe_allow_html=True)
