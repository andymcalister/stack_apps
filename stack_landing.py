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

# ── Check if user clicked "Enter Platform" ────────────────────
# The iframe posts a message to the parent when clicked
# We detect it via query param set by JS in the PARENT window
_nav = st.query_params.get("go", "")
if _nav == "platform":
    # Clear param and show a full-page redirect
    st.query_params.clear()
    st.markdown(f"""
    <style>
    body {{ margin:0; background:#0A1628; }}
    #MainMenu,header,footer {{ display:none; }}
    </style>
    <script>
    window.top.location.href = "{platform_url}";
    </script>
    <meta http-equiv="refresh" content="0;url={platform_url}">
    """, unsafe_allow_html=True)
    st.stop()

# ── Kill Streamlit chrome ─────────────────────────────────────
st.markdown("""
<style>
#MainMenu,header,footer,
[data-testid="stToolbar"],[data-testid="stDecoration"],
[data-testid="stHeader"],[data-testid="stBottom"],
[data-testid="stStatusWidget"],[data-testid="stSidebarNav"],
[data-testid="collapsedControl"]{display:none!important;}
html,body{margin:0!important;padding:0!important;overflow:hidden!important;height:100%!important;}
.stApp,.main{padding:0!important;margin:0!important;}
.block-container{padding:0!important;margin:0!important;max-width:100%!important;width:100vw!important;}
section[data-testid="stMain"],
[data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"]{padding:0!important;}
.stVerticalBlock{gap:0!important;padding:0!important;}
.element-container{margin:0!important;padding:0!important;}
iframe{
    position:fixed!important;top:0!important;left:0!important;
    width:100vw!important;height:100vh!important;
    border:none!important;z-index:999999!important;
}
</style>
""", unsafe_allow_html=True)

# ── Load and patch HTML ───────────────────────────────────────
html_content = open(os.path.join(_DIR, "stack_website.html")).read()

# The trick: when user clicks Enter Platform,
# JS inside the iframe sets a query param on the PARENT window URL
# then Streamlit detects it on next render and does the redirect
patch = f"""
<style>
html,body{{margin:0!important;padding:0!important;
    overflow-x:hidden;overflow-y:auto!important;height:auto!important;}}
</style>
<script>
function goToPlatform(e) {{
    if (e) e.preventDefault();
    // Navigate the top-level window directly to platform URL
    window.top.location.href = '{platform_url}';
}}

window.addEventListener('DOMContentLoaded', function() {{
    // Target all enter-platform buttons
    document.querySelectorAll('a').forEach(function(a) {{
        var h = a.getAttribute('href') || '';
        if (h.indexOf('nav=platform') > -1 || a.classList.contains('enter-platform-btn')) {{
            a.addEventListener('click', goToPlatform);
            a.href = '{platform_url}';
        }}
    }});

    // Nav CTA button specifically
    document.querySelectorAll('.nav-cta').forEach(function(el) {{
        el.addEventListener('click', goToPlatform);
        el.href = '{platform_url}';
    }});

    // Hero buttons
    document.querySelectorAll('.btn-primary').forEach(function(el) {{
        var h = el.getAttribute('href') || '';
        if (h === '#how' || h === '' || h.indexOf('nav') > -1) {{
            // Only target the "Take Me to the Platform" one
            if (el.textContent.indexOf('Platform') > -1 || el.textContent.indexOf('platform') > -1) {{
                el.addEventListener('click', goToPlatform);
                el.href = '{platform_url}';
            }}
        }}
    }});
}});
</script>"""

patched = html_content.replace('</head>', patch + '</head>')
components.html(patched, height=900, scrolling=True)
