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

platform_url = st.secrets.get("PLATFORM_URL", "http://localhost:8502")

# ── Kill Streamlit chrome ─────────────────────────────────────
st.markdown("""
<style>
#MainMenu, header, footer,
[data-testid="stToolbar"],[data-testid="stDecoration"],
[data-testid="stHeader"],[data-testid="stBottom"],
[data-testid="stStatusWidget"],[data-testid="stSidebarNav"],
[data-testid="collapsedControl"] { display: none !important; }
html, body { margin: 0 !important; padding: 0 !important;
    overflow: hidden !important; height: 100% !important; }
.stApp, .main { padding: 0 !important; margin: 0 !important; }
.block-container { padding: 0 !important; margin: 0 !important;
    max-width: 100% !important; width: 100vw !important; }
section[data-testid="stMain"],
[data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"] { padding: 0 !important; }
.stVerticalBlock { gap: 0 !important; padding: 0 !important; }
.element-container { margin: 0 !important; padding: 0 !important; }
iframe {
    position: fixed !important;
    top: 0 !important; left: 0 !important;
    width: 100vw !important; height: 100vh !important;
    border: none !important; z-index: 999999 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Load and patch HTML ───────────────────────────────────────
html_content = open(os.path.join(_DIR, "stack_website.html")).read()

# Patch: set all "Enter Platform" links to go directly to the platform URL
# Use a direct href with target=_top — no query params, no redirect loop
patch = f"""<style>
html, body {{ margin: 0 !important; padding: 0 !important;
    overflow-x: hidden; overflow-y: auto !important; height: auto !important; }}
</style>
<script>
window.addEventListener('DOMContentLoaded', function() {{
    // Replace all enter-platform buttons with direct link to platform
    document.querySelectorAll('a').forEach(function(a) {{
        var h = a.getAttribute('href') || '';
        if (h.indexOf('nav=platform') > -1 || a.classList.contains('enter-platform-btn')) {{
            a.href = '{platform_url}';
            a.target = '_top';
            a.removeAttribute('onclick');
        }}
    }});

    // Also handle the nav CTA button
    var navCta = document.querySelector('.nav-cta');
    if (navCta) {{
        navCta.href = '{platform_url}';
        navCta.target = '_top';
    }}
}});
</script>"""

patched = html_content.replace('</head>', patch + '</head>')

components.html(patched, height=900, scrolling=True)
