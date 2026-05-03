import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, date, timedelta
from supabase import create_client, Client

st.set_page_config(
    page_title="Stack Admin",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── SUPABASE ─────────────────────────────────────────────────
@st.cache_resource
def get_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase()

# ── ADMIN PASSWORD ────────────────────────────────────────────
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "stack-admin-2024")

# ── COLOURS ──────────────────────────────────────────────────
C = dict(
    teal="#00C2A8", gold="#F5A623", red="#EF4444",
    green="#10B981", purple="#8B5CF6",
    navy="#060E1A", navy2="#0F2035", muted="#94A3B8", slate="#475569",
)
PLOT = dict(paper_bgcolor=C["navy2"], plot_bgcolor=C["navy2"],
            font=dict(color=C["muted"], family="DM Sans"),
            margin=dict(l=8, r=8, t=36, b=8))

def fmt(v, prefix="$", decimals=0):
    if v is None: return "—"
    if abs(v) >= 1_000_000: return f"{prefix}{v/1_000_000:.2f}M"
    if abs(v) >= 1_000:     return f"{prefix}{v/1_000:.1f}k"
    return f"{prefix}{v:,.{decimals}f}"

# ── CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;background:#060E1A;color:#E2EDF4;}
.stApp{background:linear-gradient(160deg,#060E1A,#0A1628);}
h1,h2,h3{font-family:'Syne',sans-serif!important;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding-top:1rem!important;}

label,label p{color:#CBD5E1!important;font-weight:500!important;}
div[data-testid="stWidgetLabel"] p{color:#CBD5E1!important;}

/* Sidebar */
section[data-testid="stSidebar"]{background:#0A1628!important;border-right:1px solid rgba(255,255,255,0.06)!important;}
section[data-testid="stSidebar"] .stButton button{background:transparent!important;color:#94A3B8!important;border:none!important;text-align:left!important;font-size:0.875rem!important;padding:0.5rem 0.75rem!important;box-shadow:none!important;width:100%!important;}
section[data-testid="stSidebar"] .stButton button:hover{background:rgba(255,255,255,0.05)!important;color:#FFFFFF!important;}

/* KPI cards */
.kpi{background:rgba(15,32,53,0.8);border:1px solid rgba(255,255,255,0.07);border-radius:14px;padding:1.25rem 1.5rem;backdrop-filter:blur(8px);}
.kpi.alert{border-color:rgba(239,68,68,0.4);background:rgba(239,68,68,0.05);}
.kpi.warn {border-color:rgba(245,166,35,0.4);background:rgba(245,166,35,0.04);}
.kpi.good {border-color:rgba(0,194,168,0.3);background:rgba(0,194,168,0.04);}
.kpi-label{font-size:0.68rem;color:#475569;text-transform:uppercase;letter-spacing:0.1em;font-weight:700;margin-bottom:0.5rem;}
.kpi-val{font-family:'Syne',sans-serif;font-size:2rem;font-weight:800;line-height:1;}
.kpi-sub{font-size:0.75rem;color:#64748B;margin-top:0.4rem;}
.kpi-delta{font-size:0.78rem;margin-top:0.3rem;font-weight:600;}
.up{color:#10B981;} .down{color:#EF4444;} .neutral{color:#64748B;}

.section-hd{font-family:'Syne',sans-serif;font-size:1rem;font-weight:700;margin-bottom:1rem;color:#E2EDF4;display:flex;align-items:center;gap:0.5rem;}
.section-hd::before{content:'';display:inline-block;width:3px;height:16px;background:#00C2A8;border-radius:2px;}

/* Tables */
div[data-testid="stDataFrame"]{border-radius:10px;overflow:hidden;}

/* Health bar */
.health-bar-wrap{background:rgba(255,255,255,0.05);border-radius:100px;height:8px;overflow:hidden;margin:0.4rem 0;}
.health-bar-fill{height:100%;border-radius:100px;transition:width 0.5s ease;}

/* Alert banner */
.alert-banner{background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);border-radius:10px;padding:0.85rem 1.25rem;font-size:0.85rem;color:#FCA5A5;margin-bottom:1rem;}
.warn-banner{background:rgba(245,166,35,0.08);border:1px solid rgba(245,166,35,0.25);border-radius:10px;padding:0.85rem 1.25rem;font-size:0.85rem;color:#FDE68A;margin-bottom:1rem;}
.good-banner{background:rgba(0,194,168,0.08);border:1px solid rgba(0,194,168,0.2);border-radius:10px;padding:0.85rem 1.25rem;font-size:0.85rem;color:#99F6E4;margin-bottom:0.5rem;}

div[data-testid="stButton"] button{background:linear-gradient(135deg,#00C2A8,#009E88)!important;color:#060E1A!important;border:none!important;border-radius:8px!important;font-weight:700!important;padding:0.6rem 1.25rem!important;box-shadow:0 4px 15px rgba(0,194,168,0.2)!important;}

div[data-testid="stSelectbox"] div[data-baseweb="select"]>div{background:rgba(15,32,53,0.8)!important;border:1px solid rgba(0,194,168,0.2)!important;color:#FFFFFF!important;border-radius:8px!important;}
div[data-testid="stTextInput"] input{background:rgba(15,32,53,0.8)!important;border:1px solid rgba(0,194,168,0.2)!important;color:#FFFFFF!important;border-radius:8px!important;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════════
if "admin_auth" not in st.session_state:
    st.session_state.admin_auth = False

if not st.session_state.admin_auth:
    _, ac, _ = st.columns([1,2,1])
    with ac:
        st.markdown("""
        <div style="text-align:center;padding:3rem 0 2rem">
            <div style="font-family:Syne,sans-serif;font-size:2rem;font-weight:800;
                letter-spacing:0.1em;color:#FFFFFF">STACK<span style="color:#00C2A8">.</span></div>
            <div style="font-size:0.8rem;color:#475569;margin-top:0.25rem;letter-spacing:0.12em;
                text-transform:uppercase">Admin Portal</div>
        </div>
        """, unsafe_allow_html=True)
        pw = st.text_input("Admin password", type="password", placeholder="Enter admin password")
        if st.button("Access Admin →", use_container_width=True):
            if pw == ADMIN_PASSWORD:
                st.session_state.admin_auth = True
                st.rerun()
            else:
                st.error("Incorrect password.")
    st.stop()

# ══════════════════════════════════════════════════════════════
# DATA LOADERS
# ══════════════════════════════════════════════════════════════
@st.cache_data(ttl=30)
def load_metrics():
    r = supabase.table("platform_metrics").select("*").order("snapshot_date", desc=False).limit(30).execute()
    return pd.DataFrame(r.data) if r.data else pd.DataFrame()

@st.cache_data(ttl=30)
def load_users():
    r = supabase.table("users").select("id,email,first_name,last_name,user_type,state,created_at,is_admin").execute()
    return pd.DataFrame(r.data) if r.data else pd.DataFrame()

@st.cache_data(ttl=30)
def load_loans():
    r = supabase.table("loan_applications").select("*").order("created_at", desc=True).execute()
    return pd.DataFrame(r.data) if r.data else pd.DataFrame()

@st.cache_data(ttl=30)
def load_portfolios():
    r = supabase.table("stacker_portfolios").select("*").execute()
    return pd.DataFrame(r.data) if r.data else pd.DataFrame()

@st.cache_data(ttl=30)
def load_matches():
    r = supabase.table("loan_matches").select("*").execute()
    return pd.DataFrame(r.data) if r.data else pd.DataFrame()

@st.cache_data(ttl=30)
def load_transactions():
    r = supabase.table("transactions").select("*").order("created_at", desc=True).limit(100).execute()
    return pd.DataFrame(r.data) if r.data else pd.DataFrame()

# ══════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="font-family:Syne,sans-serif;font-weight:800;font-size:1.3rem;
        letter-spacing:0.12em;padding:0.5rem 0 1.5rem;color:#FFFFFF">
        STACK<span style="color:#00C2A8">.</span>
        <div style="font-size:0.65rem;color:#475569;font-family:DM Sans;
            font-weight:400;letter-spacing:0.08em;margin-top:0.1rem">ADMIN PORTAL</div>
    </div>
    """, unsafe_allow_html=True)

    if "admin_page" not in st.session_state:
        st.session_state.admin_page = "dashboard"

    pages = [
        ("📊", "dashboard",   "Dashboard"),
        ("⚡", "matching",    "Matching Engine"),
        ("💳", "loans",       "Loan Book"),
        ("📈", "stackers",    "Stacker Capital"),
        ("👥", "users",       "Users"),
        ("💸", "transactions","Transactions"),
    ]
    for icon, key, label in pages:
        active = "color:#00C2A8!important;" if st.session_state.admin_page == key else ""
        if st.button(f"{icon}  {label}", key=f"nav_{key}", use_container_width=True):
            st.session_state.admin_page = key
            st.rerun()

    st.markdown("---")
    if st.button("🔄  Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    if st.button("🚪  Log Out", use_container_width=True):
        st.session_state.admin_auth = False
        st.rerun()

    st.markdown(f"""
    <div style="font-size:0.7rem;color:#1E3A50;margin-top:1rem;text-align:center">
        Last refresh: {datetime.now().strftime('%H:%M:%S')}
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# LOAD ALL DATA
# ══════════════════════════════════════════════════════════════
df_metrics      = load_metrics()
df_users        = load_users()
df_loans        = load_loans()
df_portfolios   = load_portfolios()
df_matches      = load_matches()
df_transactions = load_transactions()

# Get latest metrics row
latest = df_metrics.iloc[-1].to_dict() if not df_metrics.empty else {}
prev   = df_metrics.iloc[-2].to_dict() if len(df_metrics) > 1 else {}

def delta(key):
    if not latest or not prev: return 0
    return float(latest.get(key,0)) - float(prev.get(key,0))

# ══════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ══════════════════════════════════════════════════════════════
if st.session_state.admin_page == "dashboard":

    st.markdown('<div style="font-family:Syne,sans-serif;font-size:1.6rem;font-weight:800;margin-bottom:0.25rem">Platform Dashboard</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="color:#475569;font-size:0.82rem;margin-bottom:1.5rem">{datetime.now().strftime("%A %d %B %Y, %H:%M")} · Live data</div>', unsafe_allow_html=True)

    # ── HEALTH ALERTS ────────────────────────────────────────
    if latest:
        ds_ratio    = float(latest.get("demand_supply_ratio", 0))
        idle_pct    = float(latest.get("idle_capital_pct", 0))
        avg_match   = float(latest.get("avg_match_hours", 0))

        if idle_pct > 10:
            st.markdown(f'<div class="alert-banner">🚨 <strong>Critical:</strong> Platform idle capital is {idle_pct:.1f}% — target is below 5%. Stacker capital is sitting dormant. Need more borrower demand.</div>', unsafe_allow_html=True)
        elif idle_pct > 5:
            st.markdown(f'<div class="warn-banner">⚠️ <strong>Warning:</strong> Idle capital at {idle_pct:.1f}% — approaching the 5% threshold. Monitor closely.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="good-banner">✅ Platform health nominal — idle capital {idle_pct:.1f}%, D/S ratio {ds_ratio:.2f}, avg match time {avg_match:.0f}hrs</div>', unsafe_allow_html=True)

        if ds_ratio < 1.0:
            st.markdown('<div class="alert-banner">🚨 <strong>Supply exceeds demand</strong> — Stacker capital cannot be fully deployed. Accelerate borrower acquisition immediately.</div>', unsafe_allow_html=True)
        elif ds_ratio > 1.5:
            st.markdown('<div class="warn-banner">⚠️ <strong>High demand ratio</strong> — Borrowers may wait too long for funding. Consider onboarding more Stackers.</div>', unsafe_allow_html=True)

    # ── KPI GRID ─────────────────────────────────────────────
    k1,k2,k3,k4,k5,k6 = st.columns(6)
    kpis = [
        (k1, "D/S Ratio",        f'{float(latest.get("demand_supply_ratio",0)):.2f}x',
         "good" if 1.0 < float(latest.get("demand_supply_ratio",0)) < 1.4 else "alert",
         f'Target: 1.0–1.4x', delta("demand_supply_ratio"), True),
        (k2, "Idle Capital",     f'{float(latest.get("idle_capital_pct",0)):.1f}%',
         "good" if float(latest.get("idle_capital_pct",0)) < 5 else "alert",
         f'Target: <5%', -delta("idle_capital_pct"), False),
        (k3, "Avg Match Time",   f'{float(latest.get("avg_match_hours",0)):.0f}hrs',
         "good" if float(latest.get("avg_match_hours",0)) < 48 else "warn",
         "Target: <48hrs", -delta("avg_match_hours"), False),
        (k4, "Active Loans",     str(int(latest.get("active_loans",0))),
         "good", f'{int(latest.get("pending_loans",0))} pending', delta("active_loans"), True),
        (k5, "Total Capital",    fmt(float(latest.get("total_stacker_capital",0))),
         "good", "Deployed + available", delta("total_stacker_capital"), True),
        (k6, "Loan Demand",      fmt(float(latest.get("total_loan_demand",0))),
         "good", "Pending applications", delta("total_loan_demand"), True),
    ]
    for col, label, val, cls, sub, dlt, up_good in kpis:
        dlt_color = "up" if (dlt > 0 and up_good) or (dlt < 0 and not up_good) else "down" if dlt != 0 else "neutral"
        dlt_sym   = "↑" if dlt > 0 else "↓" if dlt < 0 else "→"
        with col:
            st.markdown(f"""
            <div class="kpi {cls}">
                <div class="kpi-label">{label}</div>
                <div class="kpi-val">{val}</div>
                <div class="kpi-sub">{sub}</div>
                <div class="kpi-delta {dlt_color}">{dlt_sym} {abs(dlt):.2f} vs yesterday</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── MAIN CHARTS ──────────────────────────────────────────
    c1, c2 = st.columns([3, 2])

    with c1:
        st.markdown('<div class="section-hd">Demand vs Supply — 7 Day Trend</div>', unsafe_allow_html=True)
        if not df_metrics.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_metrics["snapshot_date"], y=df_metrics["total_loan_demand"],
                name="Loan Demand ($)", fill="tozeroy",
                fillcolor="rgba(0,194,168,0.08)", line=dict(color=C["teal"], width=2.5),
            ))
            fig.add_trace(go.Scatter(
                x=df_metrics["snapshot_date"], y=df_metrics["total_stacker_capital"],
                name="Stacker Capital ($)", fill="tozeroy",
                fillcolor="rgba(245,166,35,0.06)", line=dict(color=C["gold"], width=2.5, dash="dot"),
            ))
            fig.add_trace(go.Bar(
                x=df_metrics["snapshot_date"], y=df_metrics["available_capital"],
                name="Idle Capital ($)", marker_color="rgba(239,68,68,0.5)",
                yaxis="y2",
            ))
            fig.update_layout(
                **PLOT, height=300,
                xaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickfont=dict(size=10)),
                yaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickformat="$,.0f",
                           tickfont=dict(size=10, color=C["teal"])),
                yaxis2=dict(overlaying="y", side="right", tickformat="$,.0f",
                            tickfont=dict(size=10, color=C["red"]),
                            gridcolor="rgba(0,0,0,0)"),
                legend=dict(orientation="h", y=1.02, x=1, xanchor="right",
                            bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
            )
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown('<div class="section-hd">Capital Utilisation</div>', unsafe_allow_html=True)
        if not df_metrics.empty:
            deployed  = float(latest.get("deployed_capital", 0))
            available = float(latest.get("available_capital", 0))
            total     = deployed + available or 1

            fig2 = go.Figure(go.Pie(
                labels=["Deployed (earning)", "Idle (dormant)"],
                values=[deployed, available],
                hole=0.65,
                marker=dict(colors=[C["teal"], C["red"]]),
                textinfo="label+percent",
                textfont=dict(size=11, color="#FFFFFF"),
                hovertemplate="<b>%{label}</b><br>%{value:$,.0f}<extra></extra>",
            ))
            fig2.update_layout(
                **PLOT, height=220,
                annotations=[dict(
                    text=f"<b>{deployed/total*100:.1f}%</b><br>deployed",
                    x=0.5, y=0.5, font=dict(size=13, color=C["teal"]), showarrow=False
                )],
                legend=dict(orientation="h", y=-0.05, x=0.5, xanchor="center",
                            font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
                showlegend=True,
            )
            st.plotly_chart(fig2, use_container_width=True)

            # Health bars
            util_pct  = deployed / total * 100
            idle_pct2 = available / total * 100
            for label, pct, color, target, good in [
                ("Capital Deployed", util_pct,  C["teal"], 95, True),
                ("Idle Cash",        idle_pct2, C["red"],   5, False),
            ]:
                bar_color = C["teal"] if (pct >= target and good) or (pct <= target and not good) else C["red"]
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;font-size:0.75rem;
                    color:#64748B;margin-bottom:0.2rem">
                    <span>{label}</span>
                    <span style="color:{'#00C2A8' if bar_color==C['teal'] else '#EF4444'};font-weight:600">{pct:.1f}%</span>
                </div>
                <div class="health-bar-wrap">
                    <div class="health-bar-fill" style="width:{min(pct,100):.1f}%;background:{bar_color}"></div>
                </div>
                """, unsafe_allow_html=True)

    # ── D/S RATIO TREND ──────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-hd">Demand / Supply Ratio — Target Zone 1.0–1.4x</div>', unsafe_allow_html=True)
    if not df_metrics.empty:
        fig3 = go.Figure()
        # Target zone band
        fig3.add_hrect(y0=1.0, y1=1.4, fillcolor="rgba(0,194,168,0.06)",
                       line=dict(color="rgba(0,194,168,0.2)", width=1), layer="below")
        fig3.add_hline(y=1.0, line_dash="dash", line_color="rgba(239,68,68,0.4)", line_width=1,
                       annotation_text="Min (1.0x)", annotation_font=dict(color=C["red"], size=10))
        fig3.add_hline(y=1.4, line_dash="dash", line_color="rgba(245,166,35,0.4)", line_width=1,
                       annotation_text="Max (1.4x)", annotation_font=dict(color=C["gold"], size=10))
        fig3.add_trace(go.Scatter(
            x=df_metrics["snapshot_date"], y=df_metrics["demand_supply_ratio"],
            name="D/S Ratio", line=dict(color=C["teal"], width=3),
            mode="lines+markers", marker=dict(size=7, color=C["teal"]),
        ))
        fig3.update_layout(
            **PLOT, height=200,
            xaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickfont=dict(size=10)),
            yaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickfont=dict(size=10),
                       range=[0.5, 2.0]),
            showlegend=False,
        )
        st.plotly_chart(fig3, use_container_width=True)

    # ── BOTTOM ROW ───────────────────────────────────────────
    b1, b2, b3 = st.columns(3)
    with b1:
        st.markdown('<div class="section-hd">Users</div>', unsafe_allow_html=True)
        n_borrow  = len(df_users[df_users.user_type=="borrower"])  if not df_users.empty else 0
        n_stack   = len(df_users[df_users.user_type=="stacker"])   if not df_users.empty else 0
        for label, val, color in [
            ("Borrowers", n_borrow, C["teal"]),
            ("Stackers",  n_stack,  C["gold"]),
            ("Total",     n_borrow+n_stack, "#FFFFFF"),
        ]:
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;padding:0.6rem 1rem;
                background:rgba(15,32,53,0.6);border-radius:8px;margin-bottom:0.4rem;
                border:1px solid rgba(255,255,255,0.05)">
                <span style="font-size:0.85rem;color:#94A3B8">{label}</span>
                <span style="font-family:Syne,sans-serif;font-weight:700;color:{color}">{val}</span>
            </div>
            """, unsafe_allow_html=True)

    with b2:
        st.markdown('<div class="section-hd">Loan Book</div>', unsafe_allow_html=True)
        if not df_loans.empty:
            for status, color in [("pending","#F5A623"),("approved","#8B5CF6"),("funded","#00C2A8"),("rejected","#EF4444")]:
                n = len(df_loans[df_loans.status==status]) if "status" in df_loans.columns else 0
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;padding:0.6rem 1rem;
                    background:rgba(15,32,53,0.6);border-radius:8px;margin-bottom:0.4rem;
                    border:1px solid rgba(255,255,255,0.05)">
                    <span style="font-size:0.85rem;color:#94A3B8;text-transform:capitalize">{status}</span>
                    <span style="font-family:Syne,sans-serif;font-weight:700;color:{color}">{n}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#475569;font-size:0.85rem">No loan data yet</div>', unsafe_allow_html=True)

    with b3:
        st.markdown('<div class="section-hd">Platform Revenue (Est.)</div>', unsafe_allow_html=True)
        total_int = float(latest.get("total_interest_paid", 0)) if latest else 0
        orig_fees = total_int * 0.15  # rough estimate
        sub_fees  = (n_stack if not df_users.empty else 0) * 15
        mgmt_fees = total_int * 0.02
        for label, val in [
            ("Origination fees", orig_fees),
            ("Subscription fees", sub_fees),
            ("Management fees", mgmt_fees),
            ("Total", orig_fees+sub_fees+mgmt_fees),
        ]:
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;padding:0.6rem 1rem;
                background:rgba(15,32,53,0.6);border-radius:8px;margin-bottom:0.4rem;
                border:1px solid rgba(255,255,255,0.05)">
                <span style="font-size:0.85rem;color:#94A3B8">{label}</span>
                <span style="font-family:Syne,sans-serif;font-weight:700;color:#00C2A8">{fmt(val)}</span>
            </div>
            """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# PAGE: MATCHING ENGINE
# ══════════════════════════════════════════════════════════════
elif st.session_state.admin_page == "matching":
    st.markdown('<div style="font-family:Syne,sans-serif;font-size:1.6rem;font-weight:800;margin-bottom:1.5rem">Matching Engine</div>', unsafe_allow_html=True)

    st.markdown("""
    <div style="background:rgba(0,194,168,0.06);border:1px solid rgba(0,194,168,0.2);
        border-radius:12px;padding:1.25rem 1.5rem;margin-bottom:1.5rem;font-size:0.875rem;
        color:#94A3B8;line-height:1.75">
        <strong style="color:#FFFFFF">How the matching model works:</strong><br>
        Each borrower loan is split into fractions and matched across multiple Stackers — spreading risk.
        Target: each loan funded by <strong style="color:#00C2A8">8+ Stackers</strong>.
        Stacker idle cash target: <strong style="color:#00C2A8">&lt;5%</strong> of their portfolio.
        Demand/supply sweet spot: <strong style="color:#00C2A8">1.0x–1.4x</strong>.
        Repayments auto-redeploy into new loans within <strong style="color:#00C2A8">24 hours</strong>.
    </div>
    """, unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    if latest:
        pending_demand = float(latest.get("total_loan_demand",0))
        avail_capital  = float(latest.get("available_capital",0))
        gap            = pending_demand - avail_capital
        pending_loans  = int(latest.get("pending_loans",0))

        for col, label, val, note, cls in [
            (m1, "Pending Loan Demand",   fmt(pending_demand), f"{pending_loans} applications", "good"),
            (m2, "Available Capital",     fmt(avail_capital),  "Ready to deploy",               "good" if avail_capital > 0 else "alert"),
            (m3, "Capital Gap",           fmt(abs(gap)),        "Demand exceeds supply" if gap>0 else "Supply exceeds demand", "good" if gap>0 else "alert"),
            (m4, "Avg Match Time",        f'{float(latest.get("avg_match_hours",0)):.0f}hrs', "Time to fund a loan", "good" if float(latest.get("avg_match_hours",0))<48 else "warn"),
        ]:
            with col:
                st.markdown(f'<div class="kpi {cls}"><div class="kpi-label">{label}</div><div class="kpi-val">{val}</div><div class="kpi-sub">{note}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Fractionalisation model explainer
    st.markdown('<div class="section-hd">Fractionalisation Model</div>', unsafe_allow_html=True)

    # Simulate what a $15,000 loan looks like spread across Stackers
    loan_amount = 15000
    fractions = [
        ("STK-001", "Conservative", 1800, 12.0, "A"),
        ("STK-002", "Balanced",     2100, 14.0, "A"),
        ("STK-003", "Balanced",     1950, 13.0, "B"),
        ("STK-004", "Growth",       2400, 16.0, "B"),
        ("STK-005", "Conservative", 1500, 10.0, "A"),
        ("STK-006", "Growth",       1800, 12.0, "C"),
        ("STK-007", "Balanced",     2250, 15.0, "B"),
        ("STK-008", "Aggressive",   1200,  8.0, "C"),
    ]
    total_frac = sum(f[2] for f in fractions)

    fig_frac = go.Figure(go.Bar(
        x=[f[0] for f in fractions],
        y=[f[2] for f in fractions],
        marker_color=[C["teal"] if f[4]=="A" else C["gold"] if f[4]=="B" else C["red"] for f in fractions],
        text=[f'${f[2]:,.0f}<br>{f[2]/loan_amount*100:.1f}%' for f in fractions],
        textposition="outside",
        textfont=dict(size=10, color="#FFFFFF"),
    ))
    fig_frac.update_layout(
        **PLOT, height=260,
        title=dict(text=f"Example: ${loan_amount:,} loan fractionalised across {len(fractions)} Stackers",
                   font=dict(color=C["muted"], size=12)),
        xaxis=dict(tickfont=dict(size=11, color="#94A3B8"), gridcolor="rgba(0,0,0,0)"),
        yaxis=dict(tickformat="$,.0f", gridcolor="rgba(255,255,255,0.04)",
                   tickfont=dict(size=10, color=C["slate"])),
        showlegend=False,
    )
    st.plotly_chart(fig_frac, use_container_width=True)

    # Table
    frac_df = pd.DataFrame(fractions, columns=["Stacker ID","Profile","Amount ($)","Fraction %","Grade"])
    frac_df["Amount ($)"] = frac_df["Amount ($)"].apply(lambda x: f"${x:,}")
    frac_df["Fraction %"] = frac_df["Fraction %"].apply(lambda x: f"{x:.1f}%")
    st.dataframe(frac_df, use_container_width=True, hide_index=True)

    # Idle capital per Stacker
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-hd">Stacker Idle Cash Monitor</div>', unsafe_allow_html=True)

    if not df_portfolios.empty and "available_cash" in df_portfolios.columns and "current_balance" in df_portfolios.columns:
        df_portfolios["idle_pct"] = df_portfolios.apply(
            lambda r: r["available_cash"] / r["current_balance"] * 100 if r["current_balance"] else 0, axis=1
        )
        for _, row in df_portfolios.iterrows():
            idle = float(row.get("idle_pct", 0))
            color = C["red"] if idle > 5 else C["gold"] if idle > 3 else C["teal"]
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:1rem;padding:0.6rem 1rem;
                background:rgba(15,32,53,0.6);border-radius:8px;margin-bottom:0.4rem;
                border:1px solid rgba(255,255,255,0.05)">
                <span style="font-family:DM Mono,monospace;font-size:0.8rem;color:#64748B;width:120px">{str(row.get('id',''))[:8]}...</span>
                <div style="flex:1;background:rgba(255,255,255,0.05);border-radius:100px;height:6px;overflow:hidden">
                    <div style="width:{min(idle,100):.1f}%;height:100%;background:{color};border-radius:100px"></div>
                </div>
                <span style="font-weight:700;color:{color};width:50px;text-align:right">{idle:.1f}%</span>
                <span style="font-size:0.75rem;color:#475569">{'🚨 REDEPLOY' if idle>5 else '⚠️ Watch' if idle>3 else '✅ OK'}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown('<div style="color:#475569;font-size:0.875rem">No Stacker portfolio data yet. Stackers will appear here once they invest.</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# PAGE: LOAN BOOK
# ══════════════════════════════════════════════════════════════
elif st.session_state.admin_page == "loans":
    st.markdown('<div style="font-family:Syne,sans-serif;font-size:1.6rem;font-weight:800;margin-bottom:1.5rem">Loan Book</div>', unsafe_allow_html=True)

    if df_loans.empty:
        st.info("No loan applications yet. They'll appear here once borrowers apply.")
    else:
        # Filters
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            status_filter = st.selectbox("Status", ["All"] + list(df_loans["status"].unique()) if "status" in df_loans.columns else ["All"])
        with fc2:
            grade_filter = st.selectbox("Grade", ["All","A","B","C"])
        with fc3:
            sort_by = st.selectbox("Sort by", ["Created (newest)", "Amount (high)", "Amount (low)"])

        filtered = df_loans.copy()
        if status_filter != "All" and "status" in filtered.columns:
            filtered = filtered[filtered["status"] == status_filter]
        if grade_filter != "All" and "grade" in filtered.columns:
            filtered = filtered[filtered["grade"] == grade_filter]
        if sort_by == "Amount (high)" and "amount" in filtered.columns:
            filtered = filtered.sort_values("amount", ascending=False)
        elif sort_by == "Amount (low)" and "amount" in filtered.columns:
            filtered = filtered.sort_values("amount", ascending=True)

        # Display cols
        show_cols = [c for c in ["id","amount","term_months","annual_rate","status","grade",
                                  "total_funded","num_stackers","created_at"] if c in filtered.columns]
        st.dataframe(filtered[show_cols], use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════
# PAGE: STACKER CAPITAL
# ══════════════════════════════════════════════════════════════
elif st.session_state.admin_page == "stackers":
    st.markdown('<div style="font-family:Syne,sans-serif;font-size:1.6rem;font-weight:800;margin-bottom:1.5rem">Stacker Capital</div>', unsafe_allow_html=True)

    if not df_metrics.empty:
        deployed = float(latest.get("deployed_capital", 0))
        avail    = float(latest.get("available_capital", 0))
        total    = deployed + avail or 1

        s1, s2, s3, s4 = st.columns(4)
        for col, label, val, cls in [
            (s1, "Total Capital",    fmt(total),    "good"),
            (s2, "Deployed",         fmt(deployed), "good"),
            (s3, "Idle / Available", fmt(avail),    "good" if avail/total*100 < 5 else "alert"),
            (s4, "Active Stackers",  str(int(latest.get("active_stackers",0))), "good"),
        ]:
            with col:
                st.markdown(f'<div class="kpi {cls}"><div class="kpi-label">{label}</div><div class="kpi-val">{val}</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Idle capital trend
        st.markdown('<div class="section-hd">Idle Capital % — 7 Day Trend (Target <5%)</div>', unsafe_allow_html=True)
        fig_idle = go.Figure()
        fig_idle.add_hrect(y0=0, y1=5, fillcolor="rgba(0,194,168,0.05)",
                           line=dict(color="rgba(0,194,168,0.2)", width=1))
        fig_idle.add_hline(y=5, line_dash="dash", line_color=C["gold"], line_width=1.5,
                           annotation_text="5% threshold", annotation_font=dict(color=C["gold"], size=10))
        fig_idle.add_trace(go.Scatter(
            x=df_metrics["snapshot_date"], y=df_metrics["idle_capital_pct"],
            name="Idle %", line=dict(color=C["teal"], width=3),
            fill="tozeroy", fillcolor="rgba(0,194,168,0.08)",
            mode="lines+markers", marker=dict(size=7),
        ))
        fig_idle.update_layout(**PLOT, height=220,
            xaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickfont=dict(size=10)),
            yaxis=dict(gridcolor="rgba(255,255,255,0.04)", ticksuffix="%",
                       tickfont=dict(size=10), range=[0, max(10, float(df_metrics["idle_capital_pct"].max())+2)]),
            showlegend=False)
        st.plotly_chart(fig_idle, use_container_width=True)

    if not df_portfolios.empty:
        st.markdown('<div class="section-hd">Stacker Portfolios</div>', unsafe_allow_html=True)
        st.dataframe(df_portfolios, use_container_width=True, hide_index=True)
    else:
        st.info("No Stacker portfolios yet.")

# ══════════════════════════════════════════════════════════════
# PAGE: USERS
# ══════════════════════════════════════════════════════════════
elif st.session_state.admin_page == "users":
    st.markdown('<div style="font-family:Syne,sans-serif;font-size:1.6rem;font-weight:800;margin-bottom:1.5rem">Users</div>', unsafe_allow_html=True)

    if df_users.empty:
        st.info("No users yet.")
    else:
        type_filter = st.selectbox("Filter by type", ["All","borrower","stacker"])
        filtered_u  = df_users if type_filter=="All" else df_users[df_users.user_type==type_filter]

        u1, u2, u3 = st.columns(3)
        for col, label, val in [
            (u1, "Total Users",  len(df_users)),
            (u2, "Borrowers",    len(df_users[df_users.user_type=="borrower"])),
            (u3, "Stackers",     len(df_users[df_users.user_type=="stacker"])),
        ]:
            with col:
                st.markdown(f'<div class="kpi good"><div class="kpi-label">{label}</div><div class="kpi-val">{val}</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        show_u = [c for c in ["email","first_name","last_name","user_type","state","created_at"] if c in filtered_u.columns]
        st.dataframe(filtered_u[show_u], use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════
# PAGE: TRANSACTIONS
# ══════════════════════════════════════════════════════════════
elif st.session_state.admin_page == "transactions":
    st.markdown('<div style="font-family:Syne,sans-serif;font-size:1.6rem;font-weight:800;margin-bottom:1.5rem">Transactions</div>', unsafe_allow_html=True)

    if df_transactions.empty:
        st.info("No transactions yet.")
    else:
        type_filter_t = st.selectbox("Filter by type", ["All"] + list(df_transactions["type"].unique()) if "type" in df_transactions.columns else ["All"])
        filtered_t = df_transactions if type_filter_t=="All" else df_transactions[df_transactions["type"]==type_filter_t]
        st.dataframe(filtered_t, use_container_width=True, hide_index=True)
