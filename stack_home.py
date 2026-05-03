import streamlit as st
import hashlib
import re
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date
from supabase import create_client, Client

# ── PAGE CONFIG ──────────────────────────────────────────────
st.set_page_config(
    page_title="Stack — Redefining Lending & Investing",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── SUPABASE CLIENT ──────────────────────────────────────────
@st.cache_resource
def get_supabase() -> Client:
    url  = st.secrets["SUPABASE_URL"]
    key  = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = get_supabase()

# ── HELPERS ──────────────────────────────────────────────────
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def send_support_email(sender_name, sender_email, subject, message):
    try:
        smtp_user = st.secrets.get("SMTP_USER", "")
        smtp_pass = st.secrets.get("SMTP_PASS", "")
        if not smtp_user or not smtp_pass:
            return False, "Email not configured"
        msg = MIMEMultipart()
        msg["From"]    = smtp_user
        msg["To"]      = "andymcalister0@gmail.com"
        msg["Subject"] = f"[Stack Support] {subject}"
        body = f"""Support request from Stack platform:

Name:    {sender_name}
Email:   {sender_email}
Subject: {subject}

Message:
{message}

---
Sent from stacklend.com support form
"""
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, "andymcalister0@gmail.com", msg.as_string())
        return True, "Message sent"
    except Exception as e:
        return False, str(e)

def is_valid_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))

def is_strong_password(pw: str) -> bool:
    return len(pw) >= 8 and any(c.isdigit() for c in pw) and any(c.isupper() for c in pw)

def register_user(email, password, first_name, last_name, user_type, dob, state):
    try:
        existing = supabase.table("users").select("id").eq("email", email).execute()
        if existing.data:
            return False, "An account with this email already exists."
        supabase.table("users").insert({
            "email":         email,
            "password_hash": hash_password(password),
            "first_name":    first_name,
            "last_name":     last_name,
            "user_type":     user_type,
            "dob":           str(dob),
            "state":         state,
            "created_at":    datetime.utcnow().isoformat(),
            "cookie_consent": True,
            "tila_accepted":  True,
            "terms_accepted": True,
        }).execute()
        return True, "Account created successfully."
    except Exception as e:
        return False, f"Registration error: {str(e)}"

def login_user(email, password):
    try:
        result = supabase.table("users").select("*").eq("email", email).eq("password_hash", hash_password(password)).execute()
        if result.data:
            return True, result.data[0]
        return False, "Invalid email or password."
    except Exception as e:
        return False, f"Login error: {str(e)}"

# ── CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,300&display=swap');

/* ── BASE ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #060E1A;
    color: #E2EDF4;
}
.stApp {
    background: linear-gradient(160deg, #060E1A 0%, #0A1628 50%, #081520 100%);
    min-height: 100vh;
}
h1,h2,h3 { font-family: 'Syne', sans-serif !important; }

/* Hide streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem !important; padding-bottom: 0 !important; max-width: 1100px !important; }

/* ── LABELS ── */
label, label p { color: #CBD5E1 !important; font-weight: 500 !important; opacity: 1 !important; font-size: 0.875rem !important; }
div[data-testid="stWidgetLabel"] p { color: #CBD5E1 !important; font-weight: 500 !important; }
div[data-testid="stWidgetLabel"] { color: #CBD5E1 !important; }
div[data-testid="stCheckbox"] label p { color: #94A3B8 !important; font-size: 0.85rem !important; line-height: 1.5 !important; }
div[data-testid="stRadio"] label p { color: #E2EDF4 !important; }
div[data-testid="stRadio"] > div { gap: 1rem; }

/* ── INPUTS ── */
div[data-testid="stTextInput"] input {
    background: rgba(15,32,53,0.8) !important;
    border: 1px solid rgba(0,194,168,0.2) !important;
    border-radius: 8px !important;
    color: #FFFFFF !important;
    padding: 0.65rem 1rem !important;
    font-size: 0.9rem !important;
    transition: border-color 0.2s !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #00C2A8 !important;
    box-shadow: 0 0 0 3px rgba(0,194,168,0.1) !important;
}
div[data-testid="stTextInput"] input::placeholder { color: #475569 !important; }

div[data-testid="stTextArea"] textarea {
    background: rgba(15,32,53,0.8) !important;
    border: 1px solid rgba(0,194,168,0.2) !important;
    border-radius: 8px !important;
    color: #FFFFFF !important;
    font-size: 0.9rem !important;
}
div[data-testid="stTextArea"] textarea:focus { border-color: #00C2A8 !important; }

div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    background: rgba(15,32,53,0.8) !important;
    border: 1px solid rgba(0,194,168,0.2) !important;
    border-radius: 8px !important;
    color: #FFFFFF !important;
}

/* Date input */
div[data-testid="stDateInput"] input {
    background: rgba(15,32,53,0.8) !important;
    border: 1px solid rgba(0,194,168,0.2) !important;
    border-radius: 8px !important;
    color: #FFFFFF !important;
}

/* ── BUTTONS — all teal by default ── */
div[data-testid="stButton"] button {
    background: linear-gradient(135deg, #00C2A8, #009E88) !important;
    color: #060E1A !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-size: 0.875rem !important;
    padding: 0.65rem 1.5rem !important;
    width: 100% !important;
    letter-spacing: 0.02em !important;
    transition: all 0.2s !important;
    box-shadow: 0 4px 15px rgba(0,194,168,0.2) !important;
}
div[data-testid="stButton"] button:hover {
    background: linear-gradient(135deg, #00D9BC, #00C2A8) !important;
    box-shadow: 0 6px 20px rgba(0,194,168,0.35) !important;
    transform: translateY(-1px) !important;
}

/* ── NAV BUTTONS — ghost style ── */
div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button {
    background: transparent !important;
    color: #94A3B8 !important;
    border: none !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    padding: 0.5rem 0.85rem !important;
    width: auto !important;
    box-shadow: none !important;
    letter-spacing: 0 !important;
}
div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button:hover {
    color: #FFFFFF !important;
    background: rgba(255,255,255,0.06) !important;
    border-radius: 6px !important;
    transform: none !important;
    box-shadow: none !important;
}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(15,32,53,0.6);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 10px;
    padding: 0.3rem;
    gap: 0.2rem;
    backdrop-filter: blur(10px);
}
.stTabs [data-baseweb="tab"] {
    color: #64748B;
    border-radius: 7px;
    padding: 0.55rem 1.25rem;
    font-size: 0.875rem;
    font-weight: 500;
    transition: all 0.2s;
}
.stTabs [aria-selected="true"] {
    background: rgba(0,194,168,0.15) !important;
    color: #00C2A8 !important;
    font-weight: 600 !important;
}
.stTabs [data-baseweb="tab"] p { color: inherit !important; }

/* ── EXPANDER ── */
div[data-testid="stExpander"] {
    background: rgba(15,32,53,0.7);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    margin-bottom: 0.5rem;
    backdrop-filter: blur(8px);
    transition: border-color 0.2s;
}
div[data-testid="stExpander"]:hover { border-color: rgba(0,194,168,0.2); }
div[data-testid="stExpander"] summary { color: #E2EDF4 !important; font-weight: 600 !important; padding: 0.85rem 1rem !important; }
div[data-testid="stExpander"] summary p,
div[data-testid="stExpander"] summary span { color: #E2EDF4 !important; }

/* ── ALERTS ── */
div[data-testid="stAlert"] { border-radius: 10px !important; }

/* ── METRICS ── */
div[data-testid="metric-container"] {
    background: rgba(15,32,53,0.7) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 12px !important;
    padding: 1.25rem !important;
    backdrop-filter: blur(8px) !important;
}
div[data-testid="stMetricLabel"] { color: #64748B !important; font-size: 0.75rem !important; text-transform: uppercase !important; letter-spacing: 0.08em !important; }
div[data-testid="stMetricValue"] { color: #FFFFFF !important; font-family: 'Syne', sans-serif !important; font-size: 1.75rem !important; }
div[data-testid="stMetricDelta"] { font-size: 0.75rem !important; }

/* ── SECTION LABEL ── */
.section-label {
    font-size: 0.7rem; color: #00C2A8;
    text-transform: uppercase; letter-spacing: 0.14em;
    font-weight: 700; margin-bottom: 0.6rem;
    display: flex; align-items: center; gap: 0.5rem;
}
.section-label::before {
    content: ''; display: inline-block;
    width: 20px; height: 2px; background: #00C2A8;
    border-radius: 1px;
}

/* ── CARDS ── */
.card {
    background: rgba(15,32,53,0.7);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px; padding: 1.75rem;
    backdrop-filter: blur(8px);
}
.card.teal-border {
    border-color: rgba(0,194,168,0.3);
    border-top: 3px solid #00C2A8;
    background: rgba(0,194,168,0.03);
}
.card.gold-border {
    border-color: rgba(245,166,35,0.3);
    border-top: 3px solid #F5A623;
    background: rgba(245,166,35,0.03);
}

/* ── STATS ── */
.stat-big {
    font-family: 'Syne', sans-serif;
    font-size: 2.4rem; font-weight: 800; color: #00C2A8;
    line-height: 1;
}
.stat-label { font-size: 0.78rem; color: #64748B; margin-top: 0.3rem; letter-spacing: 0.03em; }

/* ── USER PILL ── */
.user-pill {
    background: rgba(0,194,168,0.1);
    border: 1px solid rgba(0,194,168,0.25);
    border-radius: 100px;
    padding: 0.3rem 1rem;
    font-size: 0.78rem; color: #00C2A8; font-weight: 600;
    display: inline-block;
}

/* ── FAQ ── */
.faq-answer { color: #94A3B8; font-size: 0.9rem; line-height: 1.75; padding: 0.25rem 0 0.5rem; }

/* ── DIVIDER ── */
hr { border-color: rgba(255,255,255,0.06) !important; margin: 1.5rem 0 !important; }

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(0,194,168,0.3); border-radius: 2px; }

/* ── TOGGLE ── */
div[data-testid="stToggle"] label p { color: #CBD5E1 !important; }

/* ── CHECKBOX ── */
div[data-testid="stCheckbox"] { margin-bottom: 0.25rem; }

/* ── FLOATING PARTICLES ── */
.particles-container {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    pointer-events: none; z-index: 0; overflow: hidden;
}
.particle {
    position: absolute; border-radius: 50%;
    animation: floatUp linear infinite;
    opacity: 0;
}
@keyframes floatUp {
    0%   { opacity: 0; transform: translateY(0) scale(0); }
    10%  { opacity: 1; }
    90%  { opacity: 0.3; }
    100% { opacity: 0; transform: translateY(-100vh) scale(1.5); }
}

/* ── GLOW ORBS ── */
.orb {
    position: fixed; border-radius: 50%;
    filter: blur(80px); pointer-events: none; z-index: 0;
}
.orb-1 {
    width: 500px; height: 500px;
    background: radial-gradient(circle, rgba(0,194,168,0.08) 0%, transparent 70%);
    top: -100px; right: -100px;
    animation: orbFloat1 12s ease-in-out infinite;
}
.orb-2 {
    width: 400px; height: 400px;
    background: radial-gradient(circle, rgba(245,166,35,0.05) 0%, transparent 70%);
    bottom: 10%; left: -100px;
    animation: orbFloat2 15s ease-in-out infinite;
}
.orb-3 {
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(139,92,246,0.05) 0%, transparent 70%);
    top: 50%; right: 20%;
    animation: orbFloat3 18s ease-in-out infinite;
}
@keyframes orbFloat1 {
    0%, 100% { transform: translate(0,0) scale(1); }
    33%       { transform: translate(-30px, 40px) scale(1.1); }
    66%       { transform: translate(20px, -20px) scale(0.95); }
}
@keyframes orbFloat2 {
    0%, 100% { transform: translate(0,0) scale(1); }
    50%       { transform: translate(40px, -60px) scale(1.15); }
}
@keyframes orbFloat3 {
    0%, 100% { transform: translate(0,0) scale(1); }
    40%       { transform: translate(-40px, 30px) scale(1.2); }
    70%       { transform: translate(20px, -20px) scale(0.9); }
}

/* ── FLOATING ICON BADGES ── */
.float-badge {
    position: fixed; z-index: 1;
    background: rgba(10,22,40,0.92);
    border: 1px solid rgba(0,194,168,0.3);
    border-radius: 18px;
    padding: 1.1rem 1.5rem;
    backdrop-filter: blur(16px);
    pointer-events: none;
    box-shadow: 0 12px 48px rgba(0,0,0,0.5), 0 0 0 1px rgba(0,194,168,0.08);
    animation: badgeFloat ease-in-out infinite;
    min-width: 200px;
}
.float-badge .badge-icon { font-size: 1.8rem; }
.float-badge .badge-text { font-size: 1rem; color: #00C2A8; font-weight: 700; white-space: nowrap; letter-spacing: -0.01em; }
.float-badge .badge-sub  { font-size: 0.78rem; color: #475569; margin-top: 0.2rem; }

.badge-a { top: 20%; right: 2%; animation-duration: 6s; animation-delay: 0s; }
.badge-b { top: 43%; right: 1.5%; animation-duration: 7s; animation-delay: 1.5s; }
.badge-c { top: 66%; right: 2.5%; animation-duration: 5.5s; animation-delay: 0.8s; }
.badge-d { top: 30%; left: 1%; animation-duration: 8s; animation-delay: 2s; }

@keyframes badgeFloat {
    0%, 100% { transform: translateY(0px); }
    50%       { transform: translateY(-14px); }
}

/* ── ANIMATED GRID BACKGROUND ── */
.grid-bg {
    position: fixed; top: 0; left: 0; right: 0; bottom: 0;
    pointer-events: none; z-index: 0;
    background-image:
        linear-gradient(rgba(0,194,168,0.025) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,194,168,0.025) 1px, transparent 1px);
    background-size: 60px 60px;
    animation: gridScroll 30s linear infinite;
    mask-image: radial-gradient(ellipse 80% 80% at 50% 50%, black 20%, transparent 80%);
}
@keyframes gridScroll {
    from { background-position: 0 0; }
    to   { background-position: 60px 60px; }
}

/* ── LIVE TICKER ── */
.ticker-wrap {
    background: rgba(0,194,168,0.06);
    border-top: 1px solid rgba(0,194,168,0.15);
    border-bottom: 1px solid rgba(0,194,168,0.15);
    padding: 0.5rem 0;
    overflow: hidden;
    margin: 1rem 0;
}
.ticker-inner {
    display: flex; gap: 3rem;
    animation: tickerScroll 20s linear infinite;
    white-space: nowrap;
}
@keyframes tickerScroll {
    from { transform: translateX(0); }
    to   { transform: translateX(-50%); }
}
.ticker-item {
    font-size: 0.78rem; color: #00C2A8; font-weight: 600;
    letter-spacing: 0.05em; display: flex; align-items: center; gap: 0.5rem;
}
.ticker-item span { color: #475569; font-weight: 400; }

/* ── PULSE DOT ── */
@keyframes pulseDot {
    0%, 100% { transform: scale(1); opacity: 1; box-shadow: 0 0 0 0 rgba(0,194,168,0.4); }
    50%       { transform: scale(1.2); box-shadow: 0 0 0 8px rgba(0,194,168,0); }
}
.pulse { animation: pulseDot 2s ease-in-out infinite; }

/* ── SHIMMER on cards ── */
@keyframes shimmer {
    0%   { background-position: -200% 0; }
    100% { background-position:  200% 0; }
}
.shimmer-line {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(0,194,168,0.4), transparent);
    background-size: 200% 100%;
    animation: shimmer 3s ease-in-out infinite;
}

/* ── NUMBER COUNTER ANIMATION ── */
.count-up {
    font-family: 'Syne', sans-serif;
    display: inline-block;
}

</style>
""", unsafe_allow_html=True)

# ── DYNAMIC BACKGROUND ELEMENTS ─────────────────────────────
st.markdown("""
<div class="grid-bg"></div>
<div class="orb orb-1"></div>
<div class="orb orb-2"></div>
<div class="orb orb-3"></div>

<!-- Floating stat badges -->
<div class="float-badge badge-a">
    <div style="display:flex;align-items:center;gap:0.5rem">
        <span class="badge-icon">📈</span>
        <div>
            <div class="badge-text">+11.4% Return</div>
            <div class="badge-sub">Average Stacker yield</div>
        </div>
    </div>
</div>
<div class="float-badge badge-b">
    <div style="display:flex;align-items:center;gap:0.5rem">
        <span class="badge-icon">💸</span>
        <div>
            <div class="badge-text">$1,247 saved</div>
            <div class="badge-sub">vs. credit cards</div>
        </div>
    </div>
</div>
<div class="float-badge badge-c">
    <div style="display:flex;align-items:center;gap:0.5rem">
        <span style="font-size:1.1rem">⚡</span>
        <div>
            <div class="badge-text">34 loans matched</div>
            <div class="badge-sub">in last 24 hours</div>
        </div>
    </div>
</div>
<div class="float-badge badge-d">
    <div style="display:flex;align-items:center;gap:0.5rem">
        <span style="font-size:1.1rem">🔒</span>
        <div>
            <div class="badge-text">AES-256 Secure</div>
            <div class="badge-sub">Bank-level encryption</div>
        </div>
    </div>
</div>

<!-- Particle canvas -->
<canvas id="particleCanvas" style="position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:0;opacity:0.4"></canvas>

<script>
(function() {
    const canvas = document.getElementById('particleCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    canvas.width  = window.innerWidth;
    canvas.height = window.innerHeight;

    const particles = [];
    const colors = ['rgba(0,194,168,', 'rgba(0,230,200,', 'rgba(0,160,140,'];

    for (let i = 0; i < 55; i++) {
        particles.push({
            x:     Math.random() * canvas.width,
            y:     Math.random() * canvas.height,
            r:     Math.random() * 1.8 + 0.3,
            dx:    (Math.random() - 0.5) * 0.3,
            dy:    -Math.random() * 0.5 - 0.2,
            alpha: Math.random() * 0.5 + 0.1,
            color: colors[Math.floor(Math.random() * colors.length)],
        });
    }

    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        particles.forEach(p => {
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            ctx.fillStyle = p.color + p.alpha + ')';
            ctx.fill();
            p.x += p.dx;
            p.y += p.dy;
            if (p.y < -5) { p.y = canvas.height + 5; p.x = Math.random() * canvas.width; }
            if (p.x < 0 || p.x > canvas.width) p.dx *= -1;
        });
        requestAnimationFrame(draw);
    }
    draw();

    window.addEventListener('resize', () => {
        canvas.width  = window.innerWidth;
        canvas.height = window.innerHeight;
    });
})();
</script>
""", unsafe_allow_html=True)

# ── SESSION STATE ─────────────────────────────────────────────
if "logged_in"      not in st.session_state: st.session_state.logged_in      = False
if "user"           not in st.session_state: st.session_state.user           = None
if "cookie_consent" not in st.session_state: st.session_state.cookie_consent = False
if "auth_tab"       not in st.session_state: st.session_state.auth_tab       = "login"
if "page"           not in st.session_state: st.session_state.page           = "home"
if "cookie_modal"   not in st.session_state: st.session_state.cookie_modal   = True

# ── COOKIE MODAL (blocking) ──────────────────────────────────
if not st.session_state.cookie_consent:
    st.markdown("""
    <div style="background:#0F2035;border:2px solid rgba(0,194,168,0.5);
        border-radius:16px;padding:2.5rem;max-width:560px;margin:6rem auto 2rem;
        box-shadow:0 32px 80px rgba(0,0,0,0.7)">
        <div style="font-size:3rem;text-align:center;margin-bottom:0.75rem">🍪</div>
        <div style="font-family:Syne,sans-serif;font-size:1.5rem;font-weight:800;
            text-align:center;margin-bottom:0.75rem;color:#FFFFFF">
            We use cookies
        </div>
        <div style="font-size:0.9rem;color:#8AACBB;line-height:1.75;text-align:center;margin-bottom:1.25rem">
            Stack uses cookies to keep you securely logged in, remember your preferences,
            and improve the platform.<br><br>
            We <strong style="color:#FFFFFF">never sell your personal data</strong> to third parties.<br><br>
            <strong style="color:#FFFFFF">Essential cookies</strong> are required for the platform to work.<br>
            <strong style="color:#FFFFFF">Analytics cookies</strong> help us improve Stack for everyone.
        </div>
        <div style="background:rgba(0,194,168,0.06);border:1px solid rgba(0,194,168,0.15);
            border-radius:8px;padding:0.9rem;font-size:0.78rem;color:#64748B;text-align:center;margin-bottom:0.5rem">
            By clicking Accept you agree to our cookie use as described in our Privacy Policy.
            You can update preferences at any time in Account Settings.
        </div>
    </div>
    """, unsafe_allow_html=True)

    _, cc1, cc2, cc3, _ = st.columns([1, 2, 2, 2, 1])
    with cc1:
        if st.button("✅ Accept All", key="cookie_accept", use_container_width=True):
            st.session_state.cookie_consent = True
            st.rerun()
    with cc2:
        if st.button("🔒 Essential Only", key="cookie_necessary", use_container_width=True):
            st.session_state.cookie_consent = True
            st.rerun()
    with cc3:
        if st.button("🔍 Privacy Policy", key="cookie_privacy_btn", use_container_width=True):
            st.session_state.cookie_consent = True
            st.session_state.page = "privacy"
            st.rerun()
    st.stop()

# ── NAV BAR ──────────────────────────────────────────────────
nav_l, nav_r = st.columns([2, 3])
with nav_l:
    st.markdown('<div style="font-family:Syne,sans-serif;font-weight:800;font-size:1.6rem;letter-spacing:0.15em;color:#FFFFFF;padding:0.4rem 0;display:flex;align-items:center;gap:0.1rem">STACK<span style="color:#00C2A8;text-shadow:0 0 20px rgba(0,194,168,0.5)">.</span></div>', unsafe_allow_html=True)
with nav_r:
    if st.session_state.logged_in:
        user = st.session_state.user
        nc1, nc2, nc3, nc4, nc5 = st.columns(5)
        with nc1:
            if st.button("🏠 Home"):       st.session_state.page = "home";     st.rerun()
        with nc2:
            if st.button("💳 Borrow"):     st.session_state.page = "borrower"; st.rerun()
        with nc3:
            if st.button("📈 Stack"):     st.session_state.page = "stacker";  st.rerun()
        with nc4:
            if st.button("❓ FAQ"):        st.session_state.page = "faq";      st.rerun()
        with nc5:
            if st.button("🚪 Log Out"):
                st.session_state.logged_in = False
                st.session_state.user      = None
                st.session_state.page      = "home"
                st.rerun()
        st.markdown(f'<div style="text-align:right;margin-top:-0.5rem"><span class="user-pill">👤 {user["first_name"]} · {user["user_type"].title()}</span></div>', unsafe_allow_html=True)
    else:
        nc1, nc2, nc3, nc4 = st.columns(4)
        with nc1:
            if st.button("🏠 Home"):    st.session_state.page = "home";    st.rerun()
        with nc2:
            if st.button("❓ FAQ"):     st.session_state.page = "faq";     st.rerun()
        with nc3:
            if st.button("🔑 Login"):   st.session_state.page = "auth";    st.session_state.auth_tab = "login";    st.rerun()
        with nc4:
            if st.button("✨ Sign Up"): st.session_state.page = "auth";    st.session_state.auth_tab = "register"; st.rerun()

st.markdown("---")

# ════════════════════════════════════════════════════════════
# PAGE: HOME
# ════════════════════════════════════════════════════════════
if st.session_state.page == "home":

    # Hero
    st.markdown("""
    <div style="padding:3rem 0 1.5rem;position:relative">
        <div style="display:inline-flex;align-items:center;gap:0.6rem;
            background:rgba(0,194,168,0.08);border:1px solid rgba(0,194,168,0.3);
            color:#00C2A8;padding:0.4rem 1.1rem;border-radius:100px;
            font-size:0.72rem;font-weight:700;letter-spacing:0.1em;margin-bottom:1.75rem">
            <span style="width:7px;height:7px;background:#00C2A8;border-radius:50%;
                display:inline-block;box-shadow:0 0 6px #00C2A8"></span>
            NOW RAISING — $1.5M SEED ROUND
        </div>
        <div style="font-family:Syne,sans-serif;font-size:clamp(2.5rem,6vw,4.5rem);
            font-weight:800;line-height:1.05;letter-spacing:-0.03em;color:#FFFFFF;margin-bottom:1.25rem">
            Lending &amp; Investing,<br>
            <span style="background:linear-gradient(135deg,#00C2A8,#00E5CC);
                -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                background-clip:text">Reimagined.</span>
        </div>
        <div style="color:#94A3B8;font-size:1.05rem;max-width:540px;font-weight:300;line-height:1.75">
            Stack connects people who need <strong style="color:#CBD5E1;font-weight:500">affordable loans</strong>
            with investors who want <strong style="color:#CBD5E1;font-weight:500">superior returns</strong>.
            Below 17%. Above 10%. Community funded. Algorithm powered.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # CTA buttons styled via HTML/JS click triggers using query params workaround
    st.markdown("""
    <div style="display:flex;gap:1.25rem;margin:2rem 0 2.5rem;flex-wrap:wrap">
        <div style="flex:1;min-width:220px;max-width:320px">
            <div style="background:linear-gradient(135deg,#00C2A8,#009E88);
                border-radius:14px;padding:1.6rem 2rem;cursor:pointer;
                box-shadow:0 8px 32px rgba(0,194,168,0.35);
                transition:all 0.25s;position:relative;overflow:hidden">
                <div style="position:absolute;top:-20px;right:-20px;width:80px;height:80px;
                    background:rgba(255,255,255,0.06);border-radius:50%"></div>
                <div style="font-size:1.75rem;margin-bottom:0.5rem">💳</div>
                <div style="font-family:Syne,sans-serif;font-size:1.2rem;font-weight:800;
                    color:#060E1A;margin-bottom:0.3rem">I want to Borrow</div>
                <div style="font-size:0.82rem;color:rgba(6,14,26,0.65);font-weight:500">
                    Loans from $5k – $25k · Below 17% APR
                </div>
            </div>
        </div>
        <div style="flex:1;min-width:220px;max-width:320px">
            <div style="background:rgba(15,32,53,0.8);
                border:1px solid rgba(245,166,35,0.4);
                border-radius:14px;padding:1.6rem 2rem;cursor:pointer;
                box-shadow:0 8px 32px rgba(245,166,35,0.12);
                transition:all 0.25s;position:relative;overflow:hidden">
                <div style="position:absolute;top:-20px;right:-20px;width:80px;height:80px;
                    background:rgba(245,166,35,0.05);border-radius:50%"></div>
                <div style="font-size:1.75rem;margin-bottom:0.5rem">📈</div>
                <div style="font-family:Syne,sans-serif;font-size:1.2rem;font-weight:800;
                    color:#FFFFFF;margin-bottom:0.3rem">I want to Stack</div>
                <div style="font-size:0.82rem;color:rgba(245,166,35,0.7);font-weight:500">
                    Target returns above 10% · From $5,000
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Functional buttons below (hidden visually via column trick, full width)
    cta1, cta2, cta3 = st.columns([1, 1, 3])
    with cta1:
        if st.button("💳  Get Started — Borrow", key="cta_borrow", use_container_width=True):
            st.session_state.page = "auth" if not st.session_state.logged_in else "borrower"
            st.session_state.auth_tab = "register"
            st.rerun()
    with cta2:
        if st.button("📈  Get Started — Stack", key="cta_invest", use_container_width=True):
            st.session_state.page = "auth" if not st.session_state.logged_in else "stacker"
            st.session_state.auth_tab = "register"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Live ticker
    ticker_items = [
        ("⚡", "Algorithm matched", "34 loans funded today"),
        ("📈", "Average Stacker return", "11.4% annualised"),
        ("💳", "Average borrower saving", "$1,247 vs credit cards"),
        ("🔒", "Platform uptime", "99.9% this month"),
        ("⚡", "Loan match time", "Under 48 hours"),
        ("📈", "Stacker portfolios", "Auto-diversified across 30+ loans"),
        ("💸", "Total interest saved", "Growing every day"),
        ("🔒", "Data encryption", "AES-256 bank-level security"),
    ]
    ticker_html = " &nbsp;&nbsp;·&nbsp;&nbsp; ".join(
        f'<span class="ticker-item"><span>{t[0]}</span> <strong>{t[1]}</strong> <span>— {t[2]}</span></span>'
        for t in ticker_items * 2
    )
    st.markdown(f"""
    <div class="ticker-wrap">
        <div class="ticker-inner">{ticker_html} &nbsp;&nbsp;·&nbsp;&nbsp; {ticker_html}</div>
    </div>
    """, unsafe_allow_html=True)

    # Stats
    s1, s2, s3, s4 = st.columns(4)
    stats = [
        ("$1.4T",  "US personal debt crisis"),
        ("<17%",   "Borrower interest rate"),
        (">10%",   "Target Stacker returns"),
        ("$1.25T", "Addressable market (TAM)"),
    ]
    for col, (num, label) in zip([s1,s2,s3,s4], stats):
        with col:
            st.markdown(f"""
            <div style="background:rgba(15,32,53,0.7);border:1px solid rgba(255,255,255,0.08);
                border-radius:14px;padding:1.5rem 1.25rem;text-align:center;
                backdrop-filter:blur(8px);border-top:2px solid rgba(0,194,168,0.4)">
                <div style="font-family:Syne,sans-serif;font-size:2.4rem;font-weight:800;
                    color:#00C2A8;line-height:1;margin-bottom:0.4rem">{num}</div>
                <div style="font-size:0.78rem;color:#64748B;letter-spacing:0.03em">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Two product cards
    st.markdown('<div class="section-label">Choose Your Path</div>', unsafe_allow_html=True)
    pc1, pc2 = st.columns(2)

    with pc1:
        st.markdown("""
        <div style="background:rgba(0,194,168,0.04);border:1px solid rgba(0,194,168,0.25);
            border-radius:16px;padding:2rem;border-top:3px solid #00C2A8;
            backdrop-filter:blur(8px)">
            <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:1.25rem">
                <div style="width:48px;height:48px;background:rgba(0,194,168,0.12);border-radius:12px;
                    display:flex;align-items:center;justify-content:center;font-size:1.5rem">💳</div>
                <div style="font-family:Syne,sans-serif;font-size:1.4rem;font-weight:800;color:#FFFFFF">Borrow Smarter</div>
            </div>
            <div style="color:#94A3B8;font-size:0.9rem;line-height:1.75;margin-bottom:1.5rem">
                Get an unsecured personal loan from $5,000 to $25,000 at rates well below
                credit cards. Community-funded, fast approval, borrower-friendly terms.
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.5rem">
                <div style="font-size:0.82rem;color:#00C2A8;display:flex;align-items:center;gap:0.4rem">
                    <span style="color:#00C2A8">✓</span> Rates below 17% APR</div>
                <div style="font-size:0.82rem;color:#00C2A8;display:flex;align-items:center;gap:0.4rem">
                    <span style="color:#00C2A8">✓</span> $5,000 – $25,000</div>
                <div style="font-size:0.82rem;color:#00C2A8;display:flex;align-items:center;gap:0.4rem">
                    <span style="color:#00C2A8">✓</span> 12 to 60 month terms</div>
                <div style="font-size:0.82rem;color:#00C2A8;display:flex;align-items:center;gap:0.4rem">
                    <span style="color:#00C2A8">✓</span> No hidden fees</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Get My Rate →", key="home_borrow"):
            st.session_state.page = "auth" if not st.session_state.logged_in else "borrower"
            st.session_state.auth_tab = "register"
            st.rerun()

    with pc2:
        st.markdown("""
        <div style="background:rgba(245,166,35,0.04);border:1px solid rgba(245,166,35,0.25);
            border-radius:16px;padding:2rem;border-top:3px solid #F5A623;
            backdrop-filter:blur(8px)">
            <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:1.25rem">
                <div style="width:48px;height:48px;background:rgba(245,166,35,0.12);border-radius:12px;
                    display:flex;align-items:center;justify-content:center;font-size:1.5rem">📈</div>
                <div style="font-family:Syne,sans-serif;font-size:1.4rem;font-weight:800;color:#FFFFFF">Invest &amp; Earn</div>
            </div>
            <div style="color:#94A3B8;font-size:0.9rem;line-height:1.75;margin-bottom:1.5rem">
                Become a Stacker. Invest from $5,000 into a diversified portfolio of personal
                loans. Algorithm-matched, auto-reinvested, targeting double-digit returns.
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.5rem">
                <div style="font-size:0.82rem;color:#F5A623">✓ Target returns above 10%</div>
                <div style="font-size:0.82rem;color:#F5A623">✓ Invest from $5,000</div>
                <div style="font-size:0.82rem;color:#F5A623">✓ Auto-diversified portfolio</div>
                <div style="font-size:0.82rem;color:#F5A623">✓ $15/month membership</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Start Stacking →", key="home_invest"):
            st.session_state.page = "auth" if not st.session_state.logged_in else "stacker"
            st.session_state.auth_tab = "register"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # How it works
    st.markdown('<div class="section-label">How Stack Works</div>', unsafe_allow_html=True)
    h1, h2, h3, h4 = st.columns(4)
    steps = [
        ("01", "Apply or Sign Up", "Create your account in minutes. Tell us whether you want to borrow or invest."),
        ("02", "Get Matched",      "Our algorithm matches borrowers with Stackers, spreading risk across multiple investors."),
        ("03", "Funds Move",       "Borrowers receive funds. Stackers start earning. Everything is automated."),
        ("04", "Grow Together",    "Borrowers repay affordably. Stackers earn above-market returns. Repayments auto-reinvest."),
    ]
    for col, (num, title, body) in zip([h1,h2,h3,h4], steps):
        with col:
            st.markdown(f"""
            <div style="background:rgba(15,32,53,0.6);border-radius:14px;padding:1.5rem;
                border:1px solid rgba(255,255,255,0.07);backdrop-filter:blur(8px);
                position:relative;overflow:hidden">
                <div style="font-family:Syne,sans-serif;font-size:3rem;font-weight:800;
                    color:rgba(0,194,168,0.08);position:absolute;top:-0.5rem;right:0.75rem;
                    line-height:1;user-select:none">{num}</div>
                <div style="width:32px;height:32px;background:rgba(0,194,168,0.12);
                    border-radius:8px;display:flex;align-items:center;justify-content:center;
                    font-family:Syne,sans-serif;font-size:0.8rem;font-weight:800;
                    color:#00C2A8;margin-bottom:1rem;border:1px solid rgba(0,194,168,0.2)">{num}</div>
                <div style="font-weight:700;font-size:0.95rem;color:#E2EDF4;margin-bottom:0.5rem">{title}</div>
                <div style="font-size:0.84rem;color:#64748B;line-height:1.7">{body}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # Trust/regulatory strip
    trust_items = [
        ("🔒", "Bank-level Security"),
        ("⚖️", "TILA / Reg Z Compliant"),
        ("🛡", "AES-256 Encrypted"),
        ("📋", "Full TILA Disclosures"),
        ("🌐", "FL Licensed · Expanding"),
        ("⚡", "Algorithm Matched"),
    ]
    cols = st.columns(len(trust_items))
    for col, (icon, label) in zip(cols, trust_items):
        with col:
            st.markdown(f"""
            <div style="text-align:center;padding:1rem 0.5rem;
                background:rgba(15,32,53,0.5);border-radius:12px;
                border:1px solid rgba(255,255,255,0.06)">
                <div style="font-size:1.4rem;margin-bottom:0.4rem">{icon}</div>
                <div style="font-size:0.72rem;color:#64748B;font-weight:500;
                    letter-spacing:0.02em;line-height:1.4">{label}</div>
            </div>
            """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# PAGE: AUTH (LOGIN / REGISTER)
# ════════════════════════════════════════════════════════════
elif st.session_state.page == "auth":

    _, auth_col, _ = st.columns([1, 2, 1])
    with auth_col:
        st.markdown('<div style="font-family:Syne,sans-serif;font-size:1.8rem;font-weight:800;margin-bottom:1.5rem;text-align:center">Welcome to <span style="color:#00C2A8">Stack</span></div>', unsafe_allow_html=True)

        tab_login, tab_register = st.tabs(["🔑 Log In", "✨ Create Account"])

        # ── LOGIN ──
        with tab_login:
            st.markdown("<br>", unsafe_allow_html=True)
            login_email = st.text_input("Email address", key="login_email", placeholder="you@example.com")
            login_pw    = st.text_input("Password", type="password", key="login_pw", placeholder="Your password")

            if st.button("Log In →", key="do_login"):
                if not login_email or not login_pw:
                    st.error("Please enter your email and password.")
                else:
                    ok, result = login_user(login_email.strip().lower(), login_pw)
                    if ok:
                        st.session_state.logged_in = True
                        st.session_state.user      = result
                        st.session_state.page      = "home"
                        st.success(f"Welcome back, {result['first_name']}!")
                        st.rerun()
                    else:
                        st.error(result)

            st.markdown("""
            <div style="text-align:center;margin-top:1rem;font-size:0.8rem;color:#64748B">
                Forgot your password? <a href="mailto:support@stacklend.com" style="color:#00C2A8">Contact support</a>
            </div>
            """, unsafe_allow_html=True)

        # ── REGISTER ──
        with tab_register:
            st.markdown("<br>", unsafe_allow_html=True)

            user_type = st.radio("I want to:", ["Borrow", "Invest (Stacker)"], horizontal=True, key="reg_type")

            rc1, rc2 = st.columns(2)
            with rc1:
                reg_first = st.text_input("First name", key="reg_first", placeholder="Andy")
            with rc2:
                reg_last  = st.text_input("Last name",  key="reg_last",  placeholder="McAlister")

            reg_email = st.text_input("Email address", key="reg_email", placeholder="you@example.com")

            rc3, rc4 = st.columns(2)
            with rc3:
                reg_pw    = st.text_input("Password", type="password", key="reg_pw",
                                          placeholder="Min 8 chars, 1 number, 1 uppercase")
            with rc4:
                reg_pw2   = st.text_input("Confirm password", type="password", key="reg_pw2", placeholder="Repeat password")

            rc5, rc6 = st.columns(2)
            with rc5:
                reg_dob   = st.date_input("Date of birth", key="reg_dob",
                                          min_value=date(1920,1,1), max_value=date(2006,1,1),
                                          value=date(1990,1,1))
            with rc6:
                reg_state = st.selectbox("State of residence", key="reg_state", options=[
                    "Florida","California","Alabama","Alaska","Arizona","Arkansas","Colorado",
                    "Connecticut","Delaware","Georgia","Hawaii","Idaho","Illinois","Indiana",
                    "Iowa","Kansas","Kentucky","Louisiana","Maine","Maryland","Massachusetts",
                    "Michigan","Minnesota","Mississippi","Missouri","Montana","Nebraska","Nevada",
                    "New Hampshire","New Jersey","New Mexico","New York","North Carolina",
                    "North Dakota","Ohio","Oklahoma","Oregon","Pennsylvania","Rhode Island",
                    "South Carolina","South Dakota","Tennessee","Texas","Utah","Vermont",
                    "Virginia","Washington","West Virginia","Wisconsin","Wyoming"
                ])

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="section-label">Required Disclosures & Agreements</div>', unsafe_allow_html=True)

            # TILA disclosure
            with st.expander("📋 Truth in Lending Act (TILA / Reg Z) Disclosure — Read before proceeding"):
                st.markdown("""
                <div style="font-size:0.82rem;color:#8AACBB;line-height:1.8">
                <strong style="color:#FFFFFF">FEDERAL TRUTH IN LENDING DISCLOSURE STATEMENT</strong><br><br>
                This disclosure is provided pursuant to the Truth in Lending Act (15 U.S.C. § 1601 et seq.)
                and Regulation Z (12 C.F.R. Part 1026).<br><br>

                <strong style="color:#FFFFFF">Annual Percentage Rate (APR):</strong> The cost of your credit as a yearly rate.
                Stack personal loan APRs range from 8.9% to 16.9% depending on creditworthiness, loan amount, and term.
                The APR includes the interest rate and the 5% origination fee amortised over the loan term.<br><br>

                <strong style="color:#FFFFFF">Finance Charge:</strong> The dollar amount the credit will cost you.
                This is calculated based on your specific loan terms and will be disclosed in your loan agreement
                prior to funding.<br><br>

                <strong style="color:#FFFFFF">Amount Financed:</strong> The amount of credit provided to you.
                Loan amounts range from $5,000 to $25,000. A 5% origination fee is deducted from the loan
                proceeds at funding.<br><br>

                <strong style="color:#FFFFFF">Total of Payments:</strong> The amount you will have paid after making
                all scheduled payments. This will be disclosed in your loan agreement.<br><br>

                <strong style="color:#FFFFFF">Payment Schedule:</strong> Loans are repaid in equal monthly installments
                over terms of 12, 24, 36, 48 or 60 months. Payments begin approximately 30 days after funding.<br><br>

                <strong style="color:#FFFFFF">Prepayment:</strong> You may prepay your loan in full or in part at any
                time without penalty. Prepayment will reduce your Finance Charge.<br><br>

                <strong style="color:#FFFFFF">Late Payment:</strong> If a payment is 15 or more days late, you may be
                charged a late fee of 5% of the payment amount or $15, whichever is greater.<br><br>

                <strong style="color:#FFFFFF">Security:</strong> Stack personal loans are unsecured. No collateral is required.<br><br>

                <strong style="color:#FFFFFF">Credit Reporting:</strong> Stack reports loan performance to major credit
                bureaus. On-time payments may help build your credit; missed payments may harm it.<br><br>

                Stack Financial Technologies is an equal opportunity lender. We do not discriminate on the basis
                of race, color, religion, national origin, sex, marital status, age, or any other protected class.
                </div>
                """, unsafe_allow_html=True)

            # Terms of Service
            with st.expander("📄 Terms of Service & User Agreement — Read before proceeding"):
                st.markdown("""
                <div style="font-size:0.82rem;color:#8AACBB;line-height:1.8">
                <strong style="color:#FFFFFF">STACK FINANCIAL TECHNOLOGIES — TERMS OF SERVICE</strong><br>
                <em>Last updated: April 2024</em><br><br>

                <strong style="color:#FFFFFF">1. Acceptance of Terms</strong><br>
                By creating an account you agree to be bound by these Terms of Service, our Privacy Policy,
                and all applicable laws and regulations. If you do not agree, do not create an account.<br><br>

                <strong style="color:#FFFFFF">2. Eligibility</strong><br>
                You must be at least 18 years of age, a US resident, and have a valid Social Security Number
                to use Stack services. Stack is currently available to residents of Florida. We are actively expanding to additional states.<br><br>

                <strong style="color:#FFFFFF">3. Borrower Terms</strong><br>
                Loan applications are subject to credit approval. Approval is not guaranteed. Stack may
                obtain credit reports and use automated decision-making. You have the right to request
                a manual review of any automated decision.<br><br>

                <strong style="color:#FFFFFF">4. Stacker (Investor) Terms</strong><br>
                Stack investment portfolios are not securities under federal or state law. Returns are
                not guaranteed. Past performance does not predict future results. You may lose some or
                all of your invested capital due to borrower defaults. Stack is not a registered
                investment adviser.<br><br>

                <strong style="color:#FFFFFF">5. Privacy & Data</strong><br>
                We collect personal and financial data to operate the platform. We use industry-standard
                encryption. We do not sell your personal data to third parties. See our Privacy Policy
                for full details.<br><br>

                <strong style="color:#FFFFFF">6. Electronic Communications</strong><br>
                By creating an account you consent to receive disclosures and communications electronically.
                You may withdraw consent at any time by contacting support@stacklend.com.<br><br>

                <strong style="color:#FFFFFF">7. Dispute Resolution</strong><br>
                Any disputes shall be resolved by binding arbitration under JAMS rules in the State of
                Florida. You waive your right to a jury trial and to participate in class actions.<br><br>

                <strong style="color:#FFFFFF">8. Limitation of Liability</strong><br>
                Stack's liability to you shall not exceed the fees paid by you in the 12 months prior
                to the event giving rise to the claim.<br><br>

                Contact: legal@stacklend.com · Stack Financial Technologies Inc.
                </div>
                """, unsafe_allow_html=True)

            # Investor risk (shown for stackers)
            if "Invest" in user_type:
                with st.expander("⚠️ Investment Risk Disclosure — Required for Stackers"):
                    st.markdown("""
                    <div style="font-size:0.82rem;color:#8AACBB;line-height:1.8">
                    <strong style="color:#FFFFFF">INVESTMENT RISK DISCLOSURE</strong><br><br>

                    <strong style="color:#FFFFFF">Not a Security:</strong> Stack investment portfolios are NOT securities
                    as defined under the Securities Act of 1933 or the Securities Exchange Act of 1934.
                    Stack is not registered with the SEC or any state securities regulator as a broker-dealer
                    or investment adviser.<br><br>

                    <strong style="color:#FFFFFF">Risk of Loss:</strong> Investing in personal loans involves significant
                    risk including the risk of borrower default. You may lose some or all of your invested
                    capital. Target returns of greater than 10% are not guaranteed.<br><br>

                    <strong style="color:#FFFFFF">Liquidity Risk:</strong> Your investment is illiquid during the loan term.
                    You may not be able to access your funds before loans are repaid.<br><br>

                    <strong style="color:#FFFFFF">No FDIC Insurance:</strong> Stack investments are not bank deposits and
                    are not insured by the FDIC or any other government agency.<br><br>

                    <strong style="color:#FFFFFF">Diversification:</strong> Stack's algorithm automatically diversifies your
                    investment across multiple loans. This reduces but does not eliminate the risk of loss.<br><br>

                    By creating a Stacker account you confirm that you understand these risks and that
                    investing may not be suitable for everyone.
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            cb1 = st.checkbox("I have read and agree to the **Terms of Service** and **User Agreement**", key="cb_terms")
            cb2 = st.checkbox("I have read and acknowledge the **Truth in Lending Act Disclosure**", key="cb_tila")
            cb3 = st.checkbox("I consent to **electronic communications** and **cookie use**", key="cb_cookie")
            if "Invest" in user_type:
                cb4 = st.checkbox("I have read and acknowledge the **Investment Risk Disclosure**", key="cb_risk")
            else:
                cb4 = True

            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Create My Account →", key="do_register"):
                errors = []
                if not reg_first.strip():    errors.append("First name is required.")
                if not reg_last.strip():     errors.append("Last name is required.")
                if not is_valid_email(reg_email.strip()): errors.append("Please enter a valid email address.")
                if not is_strong_password(reg_pw):        errors.append("Password must be at least 8 characters with 1 uppercase and 1 number.")
                if reg_pw != reg_pw2:        errors.append("Passwords do not match.")
                age = (date.today() - reg_dob).days // 365
                if age < 18:                 errors.append("You must be at least 18 years old.")
                if not cb1:                  errors.append("You must agree to the Terms of Service.")
                if not cb2:                  errors.append("You must acknowledge the TILA disclosure.")
                if not cb3:                  errors.append("You must consent to electronic communications.")
                if not cb4:                  errors.append("You must acknowledge the Investment Risk Disclosure.")

                if errors:
                    for e in errors: st.error(e)
                else:
                    utype = "stacker" if "Invest" in user_type else "borrower"
                    ok, msg = register_user(
                        email=reg_email.strip().lower(),
                        password=reg_pw,
                        first_name=reg_first.strip(),
                        last_name=reg_last.strip(),
                        user_type=utype,
                        dob=reg_dob,
                        state=reg_state,
                    )
                    if ok:
                        st.success(f"🎉 Welcome to Stack, {reg_first}! Please log in.")
                        st.balloons()
                    else:
                        st.error(msg)


# ════════════════════════════════════════════════════════════
# PAGE: BORROWER APP
# ════════════════════════════════════════════════════════════
elif st.session_state.page == "borrower":
    if not st.session_state.logged_in:
        st.warning("Please log in to access the borrower calculator.")
        if st.button("Log In / Sign Up"): st.session_state.page = "auth"; st.rerun()
    else:
        # Embed the borrower calculator inline
        exec(open("stack_borrower.py").read())


# ════════════════════════════════════════════════════════════
# PAGE: STACKER APP
# ════════════════════════════════════════════════════════════
elif st.session_state.page == "stacker":
    if not st.session_state.logged_in:
        st.warning("Please log in to access the Stacker dashboard.")
        if st.button("Log In / Sign Up"): st.session_state.page = "auth"; st.rerun()
    else:
        exec(open("stack_stacker.py").read())


# ════════════════════════════════════════════════════════════
# PAGE: FAQ
# ════════════════════════════════════════════════════════════
elif st.session_state.page == "faq":

    st.markdown('<div style="font-family:Syne,sans-serif;font-size:2rem;font-weight:800;margin-bottom:0.5rem">Frequently Asked Questions</div>', unsafe_allow_html=True)
    st.markdown('<div style="color:#8AACBB;margin-bottom:2rem">Everything you need to know about Stack.</div>', unsafe_allow_html=True)

    faq_tab1, faq_tab2, faq_tab3, faq_tab4 = st.tabs(["💳 Borrowers", "📈 Stackers", "🔒 Security & Privacy", "⚖️ Legal & Compliance"])

    with faq_tab1:
        faqs_borrower = [
            ("How much can I borrow?",
             "Stack offers unsecured personal loans from $5,000 to $25,000. The amount you're approved for depends on your credit score, income, and debt-to-income ratio."),
            ("What interest rate will I get?",
             "Stack loan APRs range from 8.9% to 16.9% — significantly below the national average credit card rate of 25%. Your exact rate is based on your credit score, loan amount, and term length. Use our borrower calculator to see your personalised rate instantly."),
            ("What terms are available?",
             "You can choose from 12, 24, 36, 48 or 60 month loan terms. Shorter terms mean higher monthly payments but less total interest paid. Longer terms lower your monthly payment but increase total interest."),
            ("Is there an origination fee?",
             "Yes. Stack charges a one-time 5% origination fee which is deducted from your loan proceeds at funding. For example, if you borrow $10,000 you will receive $9,500. This fee is included in your APR calculation."),
            ("What credit score do I need?",
             "Stack accepts borrowers with a credit score of 580 and above. However, the best rates are reserved for scores of 700+. If your score is below 650, you may want to consider improving it before applying."),
            ("How quickly will I receive funds?",
             "Once your loan is approved and matched with Stackers, funds are typically deposited within 3-5 business days. We're working on same-day funding for future releases."),
            ("Are there prepayment penalties?",
             "No. You can repay your loan early — partially or in full — at any time without any prepayment penalty. Early repayment reduces your total interest paid."),
            ("What happens if I miss a payment?",
             "If your payment is 15 or more days late, a late fee of 5% of the payment amount (minimum $15) may be charged. Missed payments are reported to credit bureaus and can negatively impact your credit score. If you're having difficulty, contact us immediately at support@stacklend.com."),
            ("Will applying affect my credit score?",
             "Checking your rate uses a soft credit pull and does not affect your score. If you proceed with a full application, a hard credit pull will be performed which may temporarily lower your score by a few points."),
            ("Is my loan secured?",
             "No. Stack personal loans are unsecured, meaning no collateral such as a car or property is required."),
        ]
        for q, a in faqs_borrower:
            with st.expander(q):
                st.markdown(f'<div class="faq-answer">{a}</div>', unsafe_allow_html=True)

    with faq_tab2:
        faqs_stacker = [
            ("What is a Stacker?",
             "A Stacker is an investor on the Stack platform. Stackers fund borrower loans in exchange for above-market returns. Your capital is automatically diversified across multiple loans by Stack's proprietary algorithm."),
            ("What returns can I expect?",
             "Stack targets returns above 10% annually for Stackers, after Stack's management fee. Actual returns depend on your risk profile, the mix of loan grades in your portfolio, and borrower default rates. Past performance does not guarantee future results."),
            ("How much do I need to start?",
             "The minimum investment is $5,000. There is no maximum. You can add to your portfolio at any time in increments of $500 or more."),
            ("What fees do Stackers pay?",
             "Stackers pay two fees: a $15 per month platform subscription fee, and a 2% annual management fee charged on loan repayments received. These fees are clearly disclosed before you invest."),
            ("How does auto-reinvestment work?",
             "When borrowers make monthly repayments, the principal and interest returned to your account is automatically reinvested into new matched loans. This creates a compounding effect that significantly accelerates portfolio growth over time. You can model this in our Stacker dashboard."),
            ("What is loan grading?",
             "Stack grades loans A, B, and C based on borrower creditworthiness. Grade A loans carry the lowest risk and lowest return (approximately 9-10%). Grade C loans carry higher risk but higher return potential (14-17%). Your algorithm automatically diversifies across grades based on your chosen risk profile."),
            ("Can I withdraw my money?",
             "Stack investments are relatively illiquid during the loan term. As borrowers repay, cash is returned to you (or reinvested). You cannot demand early repayment from borrowers. Liquidity improves as your portfolio matures and repayments flow in regularly."),
            ("What happens if a borrower defaults?",
             "If a borrower defaults, Stack pursues collections on your behalf. You may lose some or all of the capital allocated to that loan. Stack's diversification algorithm ensures no single loan represents more than a small percentage of your portfolio, limiting the impact of any individual default."),
            ("Are my returns guaranteed?",
             "No. Returns are targeted, not guaranteed. Investing in personal loans involves risk including the risk of loss of capital. Use our Monte Carlo simulation in the Stacker dashboard to model a range of outcomes including pessimistic scenarios."),
            ("Is Stack FDIC insured?",
             "No. Stack is not a bank and Stack investments are not FDIC insured. Your invested capital is at risk."),
        ]
        for q, a in faqs_stacker:
            with st.expander(q):
                st.markdown(f'<div class="faq-answer">{a}</div>', unsafe_allow_html=True)

    with faq_tab3:
        faqs_security = [
            ("How is my data protected?",
             "Stack uses AES-256 encryption for data at rest and TLS 1.3 for data in transit. We follow OWASP security best practices. Our platform is built on enterprise-grade cloud infrastructure with regular penetration testing."),
            ("Does Stack sell my data?",
             "No. Stack does not sell, rent, or share your personal data with third parties for marketing purposes. We share data only as required to operate the platform (e.g., credit bureaus, payment processors) and as required by law."),
            ("What cookies does Stack use?",
             "We use essential cookies (required for login and security), functional cookies (to remember your preferences), and analytics cookies (to improve the platform). We do not use advertising or tracking cookies. You can manage your cookie preferences at any time."),
            ("How are passwords stored?",
             "Passwords are never stored in plain text. Stack uses SHA-256 hashing with salting to store password credentials securely. We recommend using a unique, strong password for your Stack account."),
            ("What is your data retention policy?",
             "We retain your account data for the duration of your relationship with Stack and for up to 7 years thereafter as required by applicable financial regulations. You may request deletion of your data by contacting privacy@stacklend.com, subject to regulatory retention requirements."),
            ("How do I report a security issue?",
             "If you discover a security vulnerability please report it responsibly to security@stacklend.com. We take all reports seriously and aim to respond within 48 hours."),
        ]
        for q, a in faqs_security:
            with st.expander(q):
                st.markdown(f'<div class="faq-answer">{a}</div>', unsafe_allow_html=True)

    with faq_tab4:
        faqs_legal = [
            ("Is Stack a licensed lender?",
             "Stack Financial Technologies is licensed to operate in Florida. We are in the process of obtaining licences in additional states. We operate within applicable state and federal regulations. Our legal team includes specialist FinTech attorneys at Stradling Yocca Carlson & Rauth and Joshua Law Firm."),
            ("Are Stack investments securities?",
             "No. Stack investment portfolios are structured such that they are not securities under the Securities Act of 1933 or applicable state securities laws. This means Stack is not required to register with the SEC as a broker-dealer. However, this does not reduce the investment risk — you can still lose money."),
            ("What is the Truth in Lending Act?",
             "The Truth in Lending Act (TILA), implemented by Regulation Z, requires lenders to disclose the cost of credit in a standardised way so consumers can compare loan products. Stack provides full TILA disclosures including APR, Finance Charge, Amount Financed, and Total of Payments before you accept any loan."),
            ("How does Stack comply with the ECOA?",
             "The Equal Credit Opportunity Act (ECOA) prohibits discrimination in lending. Stack does not discriminate on the basis of race, colour, religion, national origin, sex, marital status, age, or any other protected class. All credit decisions are based solely on creditworthiness factors."),
            ("What is your arbitration policy?",
             "By agreeing to our Terms of Service you agree to resolve disputes through binding arbitration rather than court proceedings or class actions. Full arbitration terms are set out in our Terms of Service."),
            ("How do I file a complaint?",
             "If you have a complaint, please contact us first at support@stacklend.com. If unresolved, you may file a complaint with the Consumer Financial Protection Bureau (CFPB) at consumerfinance.gov/complaint or your state's financial regulator."),
            ("What states does Stack operate in?",
             "Stack is currently launching in Florida. We plan to expand to additional states as we obtain the necessary licences. Stack is not available to residents of states where our service is not yet licenced."),
        ]
        for q, a in faqs_legal:
            with st.expander(q):
                st.markdown(f'<div class="faq-answer">{a}</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background:#0F2035;border-radius:10px;padding:1.5rem;text-align:center;border:1px solid rgba(255,255,255,0.06)">
        <div style="font-weight:600;margin-bottom:0.5rem">Still have questions?</div>
        <div style="color:#8AACBB;font-size:0.9rem">Our team is here to help.</div>
        <div style="margin-top:0.75rem">
            <a href="mailto:support@stacklend.com" style="color:#00C2A8;font-weight:600">support@stacklend.com</a>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── FOOTER ───────────────────────────────────────────────────
st.markdown("<br><br>", unsafe_allow_html=True)
# ════════════════════════════════════════════════════════════
# PAGE: PRIVACY POLICY
# ════════════════════════════════════════════════════════════
if st.session_state.page == "privacy":
    if st.button("← Back", key="back_privacy"): st.session_state.page="home"; st.rerun()
    st.markdown('''<div style="font-family:Syne,sans-serif;font-size:2rem;font-weight:800;margin-bottom:0.25rem">Privacy Policy</div>''', unsafe_allow_html=True)
    st.markdown('<div style="color:#64748B;font-size:0.85rem;margin-bottom:2rem">Last updated: April 2024 · Stack Financial Technologies Inc.</div>', unsafe_allow_html=True)

    sections = [
        ("1. Who We Are", """Stack Financial Technologies Inc. ("Stack", "we", "us") operates the Stack platform at stacklend.com. We are a financial technology company providing peer-to-peer personal lending services. Currently licensed in Florida. Our registered address is 90 Vantis Drive Unit #3087, Aliso Viejo, CA 92656. Contact: privacy@stacklend.com"""),
        ("2. Information We Collect", """We collect the following categories of personal information:
\n• **Identity data**: first name, last name, date of birth, government ID
\n• **Contact data**: email address, phone number, mailing address
\n• **Financial data**: credit score, income, bank account details, transaction history
\n• **Technical data**: IP address, browser type, device identifiers, cookies
\n• **Usage data**: pages visited, features used, time on platform
\n• **Communications**: support messages, emails, phone calls (which may be recorded)
\n\nWe collect this data when you register, apply for a loan, make an investment, contact support, or use our platform."""),
        ("3. How We Use Your Information", """We use your personal information to:
\n• Verify your identity and prevent fraud (legal obligation)
\n• Process loan applications and investment accounts (contract performance)
\n• Conduct credit assessments and risk analysis (legitimate interest / contract)
\n• Comply with anti-money laundering (AML) and Know Your Customer (KYC) requirements (legal obligation)
\n• Send account notifications, payment reminders, and statements (contract)
\n• Report to credit bureaus as required by law (legal obligation)
\n• Improve our platform and services (legitimate interest)
\n• Send marketing communications where you have consented (consent)"""),
        ("4. Legal Basis for Processing", """Under applicable privacy law, we process your data on the following legal bases:
\n• **Performance of a contract**: to provide you with loan or investment services
\n• **Legal obligation**: to comply with financial regulations, AML/KYC, FCRA, ECOA
\n• **Legitimate interests**: fraud prevention, platform security, service improvement
\n• **Consent**: marketing communications, analytics cookies (withdrawable at any time)"""),
        ("5. Information Sharing", """We share your information only as follows:
\n• **Credit bureaus**: Equifax, Experian, TransUnion — for credit checks and reporting
\n• **Identity verification providers**: to verify your identity at registration
\n• **Payment processors**: to process loan disbursements and repayments
\n• **Cloud infrastructure providers**: AWS / Supabase — under data processing agreements
\n• **Legal and regulatory authorities**: when required by law or court order
\n• **Successors**: in the event of a merger, acquisition, or sale of the business
\n\nWe do **not** sell your personal data to third parties for marketing purposes."""),
        ("6. Data Retention", """We retain your personal data for:
\n• **Active accounts**: for the duration of your relationship with Stack
\n• **Closed accounts**: up to 7 years after closure, as required by financial regulations
\n• **Credit report data**: as required under the Fair Credit Reporting Act (FCRA)
\n• **Marketing data**: until you withdraw consent
\n\nAfter retention periods expire, data is securely deleted or anonymised."""),
        ("7. Your Rights", """Depending on your state of residence, you may have the following rights:
\n• **Access**: request a copy of the personal data we hold about you
\n• **Correction**: request correction of inaccurate data
\n• **Deletion**: request deletion of your data (subject to legal retention obligations)
\n• **Opt-out of marketing**: unsubscribe at any time via email link or by contacting us
\n• **California residents (CCPA)**: rights will apply when Stack is licensed in California
\n• **Credit report disputes**: contact the relevant credit bureau directly
\n\nTo exercise any right, contact privacy@stacklend.com. We will respond within 30 days."""),
        ("8. Cookies", """We use the following types of cookies:
\n• **Essential cookies**: required for login, security, and platform function — cannot be disabled
\n• **Functional cookies**: remember your preferences and settings
\n• **Analytics cookies**: help us understand how the platform is used (Google Analytics)
\n\nYou can manage cookie preferences at registration or by contacting support. Disabling analytics cookies will not affect platform functionality."""),
        ("9. Security", """We implement the following security measures:
\n• AES-256 encryption for data at rest
\n• TLS 1.3 encryption for data in transit
\n• SHA-256 password hashing with salting
\n• Role-level access controls on all database tables
\n• Regular security audits and penetration testing
\n\nNo system is 100% secure. If you discover a vulnerability, please report it to security@stacklend.com."""),
        ("10. Children's Privacy", """Stack services are not directed at children under 18. We do not knowingly collect data from anyone under 18. If you believe a minor has registered, contact us immediately at privacy@stacklend.com."""),
        ("11. Changes to This Policy", """We may update this Privacy Policy from time to time. We will notify you of material changes by email and by posting the updated policy on our platform with a revised date. Continued use of the platform after changes constitutes acceptance."""),
        ("12. Contact Us", """For privacy-related questions, requests, or complaints:\n\n**Stack Financial Technologies Inc.**\n90 Vantis Drive Unit #3087\nAliso Viejo, CA 92656\nEmail: privacy@stacklend.com\n\nFor complaints that we have not resolved satisfactorily, you may contact your state Attorney General or the Consumer Financial Protection Bureau (CFPB) at consumerfinance.gov."""),
    ]
    for title, body in sections:
        with st.expander(title):
            st.markdown(body)

# ════════════════════════════════════════════════════════════
# PAGE: LEGAL
# ════════════════════════════════════════════════════════════
elif st.session_state.page == "legal":
    if st.button("← Back", key="back_legal"): st.session_state.page="home"; st.rerun()
    st.markdown('''<div style="font-family:Syne,sans-serif;font-size:2rem;font-weight:800;margin-bottom:0.25rem">Legal</div>''', unsafe_allow_html=True)
    st.markdown('<div style="color:#64748B;font-size:0.85rem;margin-bottom:2rem">Stack Financial Technologies Inc. · Licensed in Florida</div>', unsafe_allow_html=True)

    lt1, lt2 = st.tabs(["📋 Terms of Service", "📄 Promissory Note & TILA"])

    with lt1:
        st.markdown("""
**STACK FINANCIAL TECHNOLOGIES — TERMS OF SERVICE**
*Last updated: April 2024*

**1. Acceptance**
By creating an account you agree to these Terms, our Privacy Policy, and all applicable laws. Stack services are currently available to Florida residents aged 18+. We are actively pursuing licensing in additional states.

**2. Eligibility**
You must be at least 18, a US resident, have a valid SSN, and reside in Florida. Stack is actively expanding to additional states.

**3. Borrower Terms**
Loan applications are subject to credit approval. Stack may use automated decision-making. You have the right to request manual review. Loans are governed by your signed Promissory Note and TILA Disclosure.

**4. Stacker (Investor) Terms**
Stack investment portfolios are not securities. Returns are not guaranteed. You may lose capital. Stack is not a registered investment adviser. The $15/month subscription and 2% management fee apply.

**5. Prohibited Uses**
You may not use Stack for illegal purposes, to purchase securities or real estate, or for any educational purpose that would make a loan a private education loan under TILA.

**6. Intellectual Property**
All Stack platform content, trademarks, and technology are owned by Stack Financial Technologies Inc. You may not reproduce or distribute any content without written permission.

**7. Limitation of Liability**
Stack's liability shall not exceed fees paid by you in the 12 months prior to the claim. Stack is not liable for indirect, consequential, or punitive damages.

**8. Dispute Resolution & Arbitration**
Disputes shall be resolved by binding arbitration under AAA Consumer Arbitration Rules. Class actions are waived. See the Promissory Note for full arbitration terms.

**9. Governing Law**
These Terms are governed by Florida law. Federal law governs the Arbitration Agreement.

**10. Contact**
Stack Financial Technologies Inc. · 90 Vantis Drive Unit #3087 · Aliso Viejo, CA 92656
legal@stacklend.com
        """)

    with lt2:
        st.markdown("""
**STACK PERSONAL LOAN — PROMISSORY NOTE SUMMARY**

The full Promissory Note is provided to borrowers at the time of loan approval and must be signed electronically before funds are disbursed. Key terms include:

**Promise to Pay**
By accepting loan proceeds, you agree to repay the full principal, origination fee, all interest, and any applicable fees and charges.

**Disbursement**
Loan funds will be disbursed within 5 business days of signing. Funds are transferred electronically to your nominated bank account.

**Permitted Use**
Loan funds may only be used for personal, family, or household purposes. Not for investment, real estate, illegal purposes, or education loans.

**Interest**
Interest accrues daily on the outstanding principal balance at your disclosed APR divided by 365. Early payments reduce total interest; late payments increase it.

**Origination Fee**
A 5% origination fee is deducted from loan proceeds at disbursement. The fee is included in your APR calculation.

**Fees**
- Late payment (15+ days late): $15
- Returned payment: $20
- Service fees: disclosed in advance

**Default**
Default may be declared if payment is 90+ days overdue, bankruptcy is filed, false statements were made, or other agreement breaches occur.

**Prepayment**
You may prepay in full or in part at any time without penalty.

**Arbitration & Class Action Waiver**
All disputes are subject to binding arbitration under AAA rules. Class actions are waived. Military servicemembers are excluded from the arbitration agreement under the Military Lending Act.

**Military Lending Act**
The MAPR for covered borrowers under the MLA shall not exceed 36%. Contact 844-306-3568 for MLA inquiries.

**State Notices**
- *California*: Licensed under California Financing Law. Contact DFPI with complaints.
- *Florida*: Made under the Florida Consumer Finance Act.

**Truth in Lending Disclosure**
A personalised TILA disclosure showing your APR, Finance Charge, Amount Financed, and Total of Payments will be provided before you accept any loan.
        """)

# ════════════════════════════════════════════════════════════
# PAGE: SUPPORT
# ════════════════════════════════════════════════════════════
elif st.session_state.page == "support":
    if st.button("← Back", key="back_support"): st.session_state.page="home"; st.rerun()
    st.markdown('''<div style="font-family:Syne,sans-serif;font-size:2rem;font-weight:800;margin-bottom:0.25rem">Support</div>''', unsafe_allow_html=True)
    st.markdown('<div style="color:#8AACBB;margin-bottom:2rem">We typically respond within one business day.</div>', unsafe_allow_html=True)

    _, sup_col, _ = st.columns([1,2,1])
    with sup_col:
        st.markdown('<div style="background:#0F2035;border:1px solid rgba(0,194,168,0.2);border-radius:12px;padding:2rem">', unsafe_allow_html=True)

        sup_name    = st.text_input("Your name",          key="sup_name",    placeholder="Andy McAlister")
        sup_email   = st.text_input("Your email address", key="sup_email",   placeholder="you@example.com")
        sup_subject = st.selectbox("Subject", key="sup_subject", options=[
            "Question about my loan",
            "Question about my Stacker account",
            "Technical issue",
            "Account access / login",
            "Billing or payments",
            "Dispute or complaint",
            "Privacy or data request",
            "Other",
        ])
        sup_message = st.text_area("Your message", key="sup_message",
                                   placeholder="Describe your question or issue in detail...",
                                   height=160)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Send Message →", key="send_support", use_container_width=True):
            if not sup_name.strip():
                st.error("Please enter your name.")
            elif not is_valid_email(sup_email.strip()):
                st.error("Please enter a valid email address.")
            elif not sup_message.strip():
                st.error("Please enter a message.")
            else:
                ok, msg = send_support_email(sup_name, sup_email, sup_subject, sup_message)
                if ok:
                    st.success("✅ Message sent! We'll get back to you within one business day.")
                    st.balloons()
                else:
                    # Fallback if SMTP not configured — show mailto
                    st.info(f"📧 SMTP not configured yet. Please email us directly at andymcalister0@gmail.com with subject: {sup_subject}")

        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("""
        <div style="margin-top:1.5rem;text-align:center;font-size:0.85rem;color:#64748B">
            For urgent loan or account issues:<br>
            <a href="mailto:support@stacklend.com" style="color:#00C2A8">support@stacklend.com</a>
            &nbsp;·&nbsp;
            <a href="tel:8443063568" style="color:#00C2A8">844-306-3568</a>
        </div>
        """, unsafe_allow_html=True)

else:
    pass

st.markdown("""
<div style="border-top:1px solid rgba(255,255,255,0.06);padding-top:2rem;margin-top:1rem">
    <div style="display:flex;flex-wrap:wrap;justify-content:space-between;align-items:flex-start;gap:1.5rem;margin-bottom:1.5rem">
        <div>
            <div style="font-family:Syne,sans-serif;font-weight:800;font-size:1.3rem;
                letter-spacing:0.14em;color:#FFFFFF;margin-bottom:0.4rem">
                STACK<span style="color:#00C2A8;text-shadow:0 0 20px rgba(0,194,168,0.4)">.</span>
            </div>
            <div style="font-size:0.78rem;color:#334155">
                © 2024 Stack Financial Technologies Inc.
            </div>
            <div style="font-size:0.75rem;color:#1E3A50;margin-top:0.2rem">
                90 Vantis Drive Unit #3087 · Aliso Viejo, CA 92656
            </div>
        </div>
        <div style="font-size:0.75rem;color:#334155;max-width:480px;line-height:1.7;text-align:right">
            Stack is not a bank. Loans subject to credit approval. Investment returns not guaranteed.
            Stack portfolios are not FDIC insured and are not securities.<br>
            Currently available to Florida residents only. Expanding to additional states. Stack Financial Technologies Inc. is not a registered investment adviser.
        </div>
    </div>
</div>
""", unsafe_allow_html=True)
# Footer nav buttons
ff1, ff2, ff3, ff4 = st.columns([5, 1, 1, 1])
with ff2:
    if st.button("⚖️ Legal",    key="footer_legal"):   st.session_state.page = "legal";   st.rerun()
with ff3:
    if st.button("🔒 Privacy",  key="footer_privacy"): st.session_state.page = "privacy"; st.rerun()
with ff4:
    if st.button("💬 Support",  key="footer_support"): st.session_state.page = "support"; st.rerun()
