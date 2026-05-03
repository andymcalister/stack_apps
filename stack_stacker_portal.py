"""
Stack Stacker Portal
Shows fractional loan portfolio, idle cash monitor, reinvestment feed, returns.
Embedded inside stack_home.py via exec() when user_type == stacker.
"""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime

supabase = st.session_state.get("_supabase")
user     = st.session_state.get("user", {})

C = dict(teal="#00C2A8", gold="#F5A623", red="#EF4444",
         green="#10B981", purple="#8B5CF6", navy2="#0F2035", muted="#94A3B8")
PLOT = dict(paper_bgcolor="#0F2035", plot_bgcolor="#0F2035",
            font=dict(color=C["muted"], family="DM Sans"),
            margin=dict(l=8,r=8,t=36,b=8))

def fmt_k(v):
    if v is None: return "—"
    if abs(v) >= 1_000_000: return f"${v/1_000_000:.2f}M"
    if abs(v) >= 1_000:     return f"${v/1_000:.1f}k"
    return f"${v:,.2f}"

# ── HEADER ───────────────────────────────────────────────────
st.markdown(f"""
<div style="margin-bottom:1.5rem">
    <div style="font-family:Syne,sans-serif;font-size:1.8rem;font-weight:800;color:#FFFFFF">
        Your Stack, {user.get('first_name','')}.
    </div>
    <div style="color:#64748B;font-size:0.875rem;margin-top:0.25rem">
        Stacker portfolio · {user.get('email','')}
    </div>
</div>
""", unsafe_allow_html=True)

# ── LOAD DATA ────────────────────────────────────────────────
portfolio  = {}
matches    = []
txns       = []

if supabase and user.get("id"):
    try:
        p = supabase.table("stacker_portfolios").select("*")\
            .eq("user_id", user["id"]).limit(1).execute()
        portfolio = p.data[0] if p.data else {}
    except: pass
    try:
        m = supabase.table("loan_matches").select("*")\
            .eq("stacker_id", user["id"]).order("matched_at", desc=True).execute()
        matches = m.data or []
    except: pass
    try:
        t = supabase.table("transactions").select("*")\
            .eq("user_id", user["id"]).order("created_at", desc=True).limit(20).execute()
        txns = t.data or []
    except: pass

if not portfolio:
    # No portfolio yet
    st.markdown("""
    <div style="background:rgba(245,166,35,0.04);border:1px solid rgba(245,166,35,0.2);
        border-radius:16px;padding:3rem;text-align:center;margin:2rem 0">
        <div style="font-size:3rem;margin-bottom:1rem">📈</div>
        <div style="font-family:Syne,sans-serif;font-size:1.5rem;font-weight:800;
            margin-bottom:0.75rem;color:#FFFFFF">Start Building Your Stack</div>
        <div style="color:#94A3B8;font-size:0.9rem;max-width:440px;margin:0 auto 1.5rem;line-height:1.7">
            You haven't invested yet. Use our portfolio modeller to project your returns,
            then start Stacking from $5,000.
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("📈 Model My Returns →", key="stacker_model_cta"):
        st.session_state.page = "stacker"
        st.rerun()
else:
    current_balance  = float(portfolio.get("current_balance", 0) or 0)
    available_cash   = float(portfolio.get("available_cash", 0) or 0)
    deployed_capital = float(portfolio.get("deployed_capital", 0) or current_balance - available_cash)
    total_earned     = float(portfolio.get("total_earned", 0) or 0)
    total_defaults   = float(portfolio.get("total_defaults", 0) or 0)
    num_active_loans = int(portfolio.get("num_active_loans", len(matches)))
    initial          = float(portfolio.get("initial_investment", current_balance))
    idle_pct         = available_cash / current_balance * 100 if current_balance else 0

    # ── IDLE CASH ALERT ──────────────────────────────────────
    if idle_pct > 10:
        st.markdown(f"""
        <div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);
            border-radius:10px;padding:1rem 1.25rem;margin-bottom:1rem;font-size:0.875rem;color:#FCA5A5">
            🚨 <strong>Action Required:</strong> {idle_pct:.1f}% of your portfolio (${available_cash:,.0f})
            is sitting idle and not earning returns. Stack is working to redeploy this capital into
            matched loans. Target idle cash: <strong>below 5%</strong>.
        </div>
        """, unsafe_allow_html=True)
    elif idle_pct > 5:
        st.markdown(f"""
        <div style="background:rgba(245,166,35,0.08);border:1px solid rgba(245,166,35,0.25);
            border-radius:10px;padding:1rem 1.25rem;margin-bottom:1rem;font-size:0.875rem;color:#FDE68A">
            ⚠️ <strong>Idle cash approaching limit:</strong> {idle_pct:.1f}% idle.
            Stack is matching your capital to borrowers now. Target: below 5%.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background:rgba(0,194,168,0.06);border:1px solid rgba(0,194,168,0.2);
            border-radius:10px;padding:0.85rem 1.25rem;margin-bottom:1rem;font-size:0.875rem;color:#99F6E4">
            ✅ <strong>Portfolio performing well.</strong> {idle_pct:.1f}% idle — within target.
            Your capital is actively earning across {num_active_loans} loan positions.
        </div>
        """, unsafe_allow_html=True)

    # ── KPI ROW ──────────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)
    net_return_pct = (total_earned - total_defaults) / initial * 100 if initial else 0

    for col, label, val, color, sub in [
        (k1, "Portfolio Value",   fmt_k(current_balance),  C["teal"],   f"+{fmt_k(current_balance-initial)} total gain"),
        (k2, "Deployed Capital",  fmt_k(deployed_capital), "#FFFFFF",   f"{100-idle_pct:.1f}% of portfolio"),
        (k3, "Idle Cash",         fmt_k(available_cash),   C["red"] if idle_pct>5 else C["teal"], f"{idle_pct:.1f}% — target <5%"),
        (k4, "Total Earned",      fmt_k(total_earned),     C["green"],  "Gross interest received"),
        (k5, "Net Return",        f"{net_return_pct:.1f}%",C["teal"],   "After defaults"),
    ]:
        with col:
            st.markdown(f"""
            <div style="background:rgba(15,32,53,0.8);border:1px solid rgba(255,255,255,0.07);
                border-radius:14px;padding:1.25rem;backdrop-filter:blur(8px)">
                <div style="font-size:0.68rem;color:#475569;text-transform:uppercase;
                    letter-spacing:0.1em;font-weight:700;margin-bottom:0.5rem">{label}</div>
                <div style="font-family:Syne,sans-serif;font-size:1.6rem;font-weight:800;
                    color:{color};line-height:1">{val}</div>
                <div style="font-size:0.72rem;color:#475569;margin-top:0.35rem">{sub}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── MAIN CHARTS ──────────────────────────────────────────
    chart_col, right_col = st.columns([3, 2])

    with chart_col:
        st.markdown('<div style="font-family:Syne,sans-serif;font-size:0.95rem;font-weight:700;margin-bottom:1rem;color:#E2EDF4">Capital Allocation</div>', unsafe_allow_html=True)

        # Capital split donut
        grade_a = float(portfolio.get("grade_a_pct", 60)) / 100 * deployed_capital
        grade_b = float(portfolio.get("grade_b_pct", 30)) / 100 * deployed_capital
        grade_c = (100 - float(portfolio.get("grade_a_pct",60)) - float(portfolio.get("grade_b_pct",30))) / 100 * deployed_capital

        fig = make_subplots(rows=1, cols=2, specs=[[{"type":"domain"},{"type":"xy"}]])

        fig.add_trace(go.Pie(
            labels=["Grade A","Grade B","Grade C","Idle Cash"],
            values=[grade_a, grade_b, grade_c, available_cash],
            hole=0.6,
            marker=dict(colors=[C["teal"], C["gold"], C["purple"], C["red"]]),
            textinfo="label+percent",
            textfont=dict(size=10, color="#FFFFFF"),
            hovertemplate="<b>%{label}</b><br>%{value:$,.0f}<extra></extra>",
        ), row=1, col=1)

        # Grade return bars
        fig.add_trace(go.Bar(
            x=["Grade A","Grade B","Grade C"],
            y=[9.5, 12.2, 15.5],
            marker_color=[C["teal"], C["gold"], C["purple"]],
            text=["9.5%","12.2%","15.5%"],
            textposition="outside",
            textfont=dict(size=11, color="#FFFFFF"),
            name="Target Return %",
        ), row=1, col=2)

        fig.update_layout(
            **PLOT, height=280,
            annotations=[dict(
                text=f"<b>{fmt_k(current_balance)}</b>",
                x=0.19, y=0.5, font=dict(size=12, color=C["teal"]),
                showarrow=False, xref="paper", yref="paper"
            )],
            showlegend=False,
            yaxis2=dict(ticksuffix="%", gridcolor="rgba(255,255,255,0.04)",
                        tickfont=dict(size=10)),
            xaxis2=dict(tickfont=dict(size=11, color="#94A3B8"),
                        gridcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig, use_container_width=True)

    with right_col:
        st.markdown('<div style="font-family:Syne,sans-serif;font-size:0.95rem;font-weight:700;margin-bottom:1rem;color:#E2EDF4">Idle Cash Monitor</div>', unsafe_allow_html=True)

        # Idle cash gauge
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=idle_pct,
            number=dict(suffix="%", font=dict(color=C["teal"], size=28, family="Syne")),
            gauge=dict(
                axis=dict(range=[0,20], tickfont=dict(size=9, color=C["muted"])),
                bar=dict(color=C["red"] if idle_pct>5 else C["teal"], thickness=0.3),
                bgcolor="rgba(255,255,255,0.03)",
                bordercolor="rgba(255,255,255,0.06)",
                steps=[
                    dict(range=[0,5],   color="rgba(0,194,168,0.12)"),
                    dict(range=[5,10],  color="rgba(245,166,35,0.08)"),
                    dict(range=[10,20], color="rgba(239,68,68,0.08)"),
                ],
                threshold=dict(
                    line=dict(color=C["gold"], width=3),
                    thickness=0.8, value=5
                ),
            ),
            title=dict(text="Idle Cash %", font=dict(color=C["muted"], size=12)),
        ))
        fig_gauge.update_layout(**PLOT, height=220)
        st.plotly_chart(fig_gauge, use_container_width=True)

        target_status = "✅ Within target" if idle_pct <= 5 else "⚠️ Above target" if idle_pct <= 10 else "🚨 Action needed"
        target_color  = C["teal"] if idle_pct <= 5 else C["gold"] if idle_pct <= 10 else C["red"]
        st.markdown(f'<div style="text-align:center;font-size:0.82rem;color:{target_color};font-weight:600">{target_status} · Target: below 5%</div>', unsafe_allow_html=True)

    # ── ACTIVE LOAN POSITIONS ────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div style="font-family:Syne,sans-serif;font-size:0.95rem;font-weight:700;margin-bottom:1rem;color:#E2EDF4">Your Loan Positions</div>', unsafe_allow_html=True)

    if matches:
        for m in matches[:10]:
            fraction_pct = float(m.get("fraction_pct",0)) * 100
            fraction_amt = float(m.get("fraction_amount",0))
            interest     = float(m.get("interest_earned",0))
            status       = m.get("status","active")
            s_color      = C["teal"] if status=="active" else C["muted"] if status=="repaid" else C["red"]

            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:1rem;padding:0.75rem 1.1rem;
                background:rgba(15,32,53,0.7);border-radius:10px;margin-bottom:0.4rem;
                border:1px solid rgba(255,255,255,0.05)">
                <div style="width:8px;height:8px;border-radius:50%;background:{s_color};flex-shrink:0"></div>
                <div style="font-family:DM Mono,monospace;font-size:0.78rem;color:#475569;width:100px;flex-shrink:0">
                    {str(m.get('loan_id',''))[:8]}...
                </div>
                <div style="flex:1;background:rgba(255,255,255,0.04);border-radius:100px;height:5px;overflow:hidden">
                    <div style="width:{min(fraction_pct*3,100):.0f}%;height:100%;
                        background:{s_color};border-radius:100px"></div>
                </div>
                <div style="font-size:0.82rem;font-weight:600;color:#E2EDF4;width:70px;text-align:right">
                    ${fraction_amt:,.0f}
                </div>
                <div style="font-size:0.78rem;color:{C['green']};width:60px;text-align:right;font-weight:600">
                    +${interest:,.2f}
                </div>
                <div style="font-size:0.72rem;color:{s_color};width:60px;text-align:right;
                    text-transform:capitalize;font-weight:600">{status}</div>
            </div>
            """, unsafe_allow_html=True)
        if len(matches) > 10:
            st.caption(f"Showing 10 of {len(matches)} positions")
    else:
        st.markdown('<div style="color:#475569;font-size:0.875rem;padding:1rem 0">No active loan positions yet. Stack will match your capital to borrowers automatically.</div>', unsafe_allow_html=True)

    # ── TRANSACTION FEED ─────────────────────────────────────
    if txns:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div style="font-family:Syne,sans-serif;font-size:0.95rem;font-weight:700;margin-bottom:1rem;color:#E2EDF4">Recent Activity</div>', unsafe_allow_html=True)

        type_icons = {
            "investment": ("💰", C["teal"]),
            "stacker_return": ("💚", C["green"]),
            "reinvestment": ("♻️", C["teal"]),
            "management_fee": ("📋", C["muted"]),
            "subscription_fee": ("📋", C["muted"]),
            "default": ("⚠️", C["red"]),
            "withdrawal": ("↗️", C["gold"]),
        }
        for txn in txns[:8]:
            txn_type = txn.get("type","")
            icon, color = type_icons.get(txn_type, ("•", C["muted"]))
            amount = float(txn.get("amount",0))
            direction = txn.get("direction","out")
            amt_str = f"+${amount:,.2f}" if direction=="in" else f"-${amount:,.2f}"
            amt_color = C["green"] if direction=="in" else C["red"]

            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:0.85rem;padding:0.65rem 1rem;
                background:rgba(15,32,53,0.6);border-radius:8px;margin-bottom:0.3rem;
                border:1px solid rgba(255,255,255,0.04)">
                <span style="font-size:1rem">{icon}</span>
                <div style="flex:1">
                    <div style="font-size:0.82rem;color:#E2EDF4;font-weight:500;text-transform:capitalize">
                        {txn_type.replace('_',' ').title()}
                    </div>
                    <div style="font-size:0.72rem;color:#475569;margin-top:0.1rem">
                        {txn.get('description','') or ''} · {str(txn.get('created_at',''))[:16]}
                    </div>
                </div>
                <div style="font-family:Syne,sans-serif;font-weight:700;
                    font-size:0.9rem;color:{amt_color}">{amt_str}</div>
            </div>
            """, unsafe_allow_html=True)
