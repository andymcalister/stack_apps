import streamlit as st
import streamlit.components.v1 as components
import os

st.set_page_config(
    page_title="Stack — Redefining Lending & Investing",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed",
)

_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Handle platform redirect ──────────────────────────────────
_nav = st.query_params.get("nav", "")
if _nav == "platform":
    st.query_params.clear()
    platform_url = st.secrets.get("PLATFORM_URL", "http://localhost:8502")
    st.markdown(f"""
    <meta http-equiv="refresh" content="0; url={platform_url}">
    <script>window.location.href = '{platform_url}';</script>
    """, unsafe_allow_html=True)
    st.stop()

# ── Kill Streamlit chrome ─────────────────────────────────────
st.markdown("""
<style>
#MainMenu, header, footer,
[data-testid="stToolbar"],[data-testid="stDecoration"],
[data-testid="stHeader"],[data-testid="stBottom"],
[data-testid="stStatusWidget"],[data-testid="stSidebarNav"],
[data-testid="collapsedControl"] { display: none !important; }

html, body {
    margin: 0 !important;
    padding: 0 !important;
    height: 100% !important;
    overflow: hidden !important;
}
.stApp, .main {
    padding: 0 !important;
    margin: 0 !important;
    height: 100vh !important;
    overflow: hidden !important;
}
.block-container {
    padding: 0 !important;
    margin: 0 !important;
    max-width: 100% !important;
    width: 100vw !important;
    height: 100vh !important;
}
section[data-testid="stMain"],
[data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"] {
    padding: 0 !important;
    height: 100vh !important;
    overflow: hidden !important;
}
.stVerticalBlock { gap: 0 !important; padding: 0 !important; height: 100% !important; }
.element-container { margin: 0 !important; padding: 0 !important; height: 100% !important; }

/* iframe fills 100% with its OWN scroll */
iframe {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    border: none !important;
    z-index: 999999 !important;
    overflow: auto !important;
}
</style>
""", unsafe_allow_html=True)

# ── Load and patch HTML ───────────────────────────────────────
html_content = open(os.path.join(_DIR, "stack_website.html")).read()
platform_url = st.secrets.get("PLATFORM_URL", "http://localhost:8502")

patch = f"""<style>
html, body {{
    margin: 0 !important;
    padding: 0 !important;
    overflow-x: hidden;
    /* scroll happens here inside the iframe */
    overflow-y: auto !important;
    height: auto !important;
}}
</style>
<script>
window.addEventListener('DOMContentLoaded', function() {{
    document.querySelectorAll('a').forEach(function(a) {{
        var h = a.getAttribute('href') || '';
        if (h.indexOf('nav=platform') > -1 || a.classList.contains('enter-platform-btn')) {{
            a.href = '{platform_url}';
            a.target = '_top';
        }}
    }});
}});
</script>"""

patched = html_content.replace('</head>', patch + '</head>')

# scrolling=True lets the iframe scroll internally
# height is just a hint — CSS overrides to 100vh fixed
components.html(patched, height=900, scrolling=True)
